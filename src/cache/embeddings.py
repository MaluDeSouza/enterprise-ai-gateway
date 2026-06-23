class EmbeddingService:
    def __init__(self):
        self._model = None

    @property
    def model(self):
        # Só importa as bibliotecas gigantescas na hora H
        if self._model is None:
            print("⏳ Carregando as bibliotecas e o motor matemático (SentenceTransformers)...")
            
            # A MÁGICA ESTÁ AQUI: Importação escondida dentro da função!
            from sentence_transformers import SentenceTransformer
            
            self._model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Motor matemático pronto!")
        return self._model

    def generate_embedding(self, text: str) -> list[float]:
        """
        Converte a string de texto em um vetor matemático (lista de floats).
        """
        embedding = self.model.encode(text)
        return embedding.tolist()

embedding_service = EmbeddingService()