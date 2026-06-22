import asyncio
from typing import AsyncGenerator
from src.providers.base import BaseProvider

class OllamaProvider(BaseProvider):
    async def generate_stream(self, model: str, messages: list[dict]) -> AsyncGenerator[str, None]:
        mock_response = "Opa! Aqui é o Fallback de emergência. A OpenAI caiu, mas o Gateway me acionou e salvou o dia!"
        words = mock_response.split()
        for word in words:
            yield f"data: {word} \n\n"
            await asyncio.sleep(0.2)
        yield "data: [DONE]\n\n"