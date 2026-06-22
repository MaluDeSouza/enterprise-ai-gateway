from redis.asyncio import Redis
from src.config import settings

class RateLimiter:
    def __init__(self):
        # Conecta ao Redis usando a URL do .env e já decodifica os bytes para texto
        self.redis = Redis.from_url(settings.redis_url, decode_responses=True)
        
        # A nossa regra de negócio: 5 requisições a cada 60 segundos
        self.capacity = 5
        self.window = 60

    async def check_rate_limit(self, api_key: str) -> bool:
        """
        Consulta o balde do Tenant. Retorna True se tem ficha, False se estourou.
        """
        # Criamos uma chave única no Redis para este usuário específico
        key = f"rate_limit:{api_key}"
        
        # Puxa o saldo atual de requisições
        current = await self.redis.get(key)
        
        # Se o balde estiver cheio/esgotado, cortamos o acesso na hora
        if current is not None and int(current) >= self.capacity:
            return False 
            
        # Se for a primeira requisição do minuto, cria a contagem e aciona o cronômetro (TTL)
        if current is None:
            await self.redis.set(key, 1, ex=self.window)
        else:
            # Se já tem contagem rodando, apenas retira mais uma ficha
            await self.redis.incr(key)
            
        return True