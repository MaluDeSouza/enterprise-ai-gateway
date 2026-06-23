import numpy as np
from redis.asyncio import Redis
from redis.commands.search.field import VectorField, TextField
from redis.commands.search.query import Query
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

from src.config import settings
from src.cache.embeddings import embedding_service

class SemanticCache:
    def __init__(self):
        # Conecta ao Redis Stack (que suporta a procura vetorial)
        self.redis = Redis.from_url(settings.redis_url)
        self.index_name = "idx:semantic_cache"
        
        # 80% de similaridade mínima para considerarmos um "Hit" e pouparmos dinheiro
        self.threshold = 0.80

    async def setup_index(self):
        """Cria o índice vetorial no Redis no arranque do servidor, se ainda não existir."""
        try:
            await self.redis.ft(self.index_name).info()
        except:
            schema = (
                TextField("prompt"),
                TextField("response"),
                VectorField("embedding", "FLAT", {
                    "TYPE": "FLOAT32",
                    "DIM": 384, # O tamanho exato do nosso modelo MiniLM
                    "DISTANCE_METRIC": "COSINE"
                })
            )
            definition = IndexDefinition(prefix=["cache:"], index_type=IndexType.HASH)
            await self.redis.ft(self.index_name).create_index(fields=schema, definition=definition)

    async def check_cache(self, user_prompt: str) -> str | None:
        """Converte a pergunta em vetor e procura a mais parecida no Redis."""
        try:
            vector = embedding_service.generate_embedding(user_prompt)
            vector_bytes = np.array(vector, dtype=np.float32).tobytes()

            # Prepara a query (KNN = K Nearest Neighbors, traz o 1 mais próximo)
            q = Query("*=>[KNN 1 @embedding $vec AS score]").return_fields("response", "score").dialect(2)
            
            res = await self.redis.ft(self.index_name).search(q, query_params={"vec": vector_bytes})
            
            if res.docs:
                # O Redis retorna a distância (0 = idêntico, 1 = oposto)
                distance = float(res.docs[0].score)
                similarity = 1 - distance
                
                print(f"🧠 [DEBUG CACHE] Similaridade da pergunta: {similarity:.2f} | Mínimo exigido: {self.threshold}")
                
                if similarity >= self.threshold:
                    return res.docs[0].response
        except Exception as e:
            print(f"🔴 Erro no Cache Semântico: {e}")
            
        return None

    async def save_to_cache(self, user_prompt: str, response: str):
        """Guarda a pergunta e a resposta no banco vetorial para o futuro."""
        vector = embedding_service.generate_embedding(user_prompt)
        vector_bytes = np.array(vector, dtype=np.float32).tobytes()
        
        key = f"cache:{hash(user_prompt)}"
        mapping = {
            "prompt": user_prompt,
            "response": response,
            "embedding": vector_bytes
        }
        await self.redis.hset(key, mapping=mapping)

# Instanciamos globalmente para reutilizar a mesma ligação
semantic_cache = SemanticCache()