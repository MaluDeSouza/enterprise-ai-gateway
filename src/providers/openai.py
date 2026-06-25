import httpx
from typing import AsyncGenerator
from src.providers.base import BaseProvider
from src.config import settings

class OpenAIProvider(BaseProvider):
    def __init__(self):
        self.api_url = "https://api.openai.com/v1/chat/completions"

    async def generate_stream(self, model: str, messages: list[dict]) -> AsyncGenerator[str, None]:
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key.strip()}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,  # Ex: "gpt-4" ou "gpt-3.5-turbo"
            "messages": messages,
            "stream": True
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", self.api_url, headers=headers, json=payload) as response:
                
                # Se a chave for dummy, vai estourar um erro aqui que o Circuit Breaker vai capturar
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        
                        # Como a OpenAI dita o padrão de mercado, nós apenas repassamos o dado blindado
                        yield f"data: {data_str}\n\n"
                        
        yield "data: [DONE]\n\n"