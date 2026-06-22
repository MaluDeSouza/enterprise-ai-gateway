class SemanticCache:
    def __init__(self):
        # Este é o nosso "banco de dados" falso (Mock). 
        # No mundo real, isso aqui será o Redis fazendo buscas vetoriais.
        self._mock_db = {
            "qual o cnpj da empresa?": "O CNPJ da nossa empresa é 12.345.678/0001-99."
        }

    def check_cache(self, user_message: str) -> str | None:
        """
        Verifica se já temos a resposta para essa pergunta guardada.
        """
       
        question = user_message.lower().strip()

        if question in self._mock_db:
            return self._mock_db[question]
            

        return None