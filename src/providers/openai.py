# import asyncio
# from typing import AsyncGenerator
# from src.providers.base import BaseProvider

# class OpenAIProvider(BaseProvider):
#     async def generate_stream(self, model: str, messages: list[dict]) -> AsyncGenerator[str, None]:
#         # Nossa IA falsa (Mock) para economizar dinheiro
#         mock_response = "Olá! Eu sou a IA mockada do seu Gateway Enterprise. O seu roteamento está funcionando perfeitamente!"
        
#         # Vamos dividir a frase em palavras para simular a IA "digitando"
#         words = mock_response.split()
        
#         for word in words:
#             yield f"data: {word} \n\n"
#             await asyncio.sleep(0.2) # Pausa de 200ms
            
#         yield "data: [DONE]\n\n"
        
    ##############################################
    
import asyncio
from typing import AsyncGenerator
from src.providers.base import BaseProvider

class OpenAIProvider(BaseProvider):
    async def generate_stream(self, model: str, messages: list[dict]) -> AsyncGenerator[str, None]:
        # Simulando que a API da OpenAI saiu do ar para testarmos o Fallback!
        raise Exception("Erro 503: OpenAI Service Unavailable")
        
        # Essa linha abaixo serve apenas para manter a assinatura do AsyncGenerator correta, 
        # mas nunca será executada por causa do erro acima.
        yield "data: Isso nunca vai rodar\n\n"