import json
import httpx
from typing import AsyncGenerator
from src.providers.base import BaseProvider
from src.config import settings

class OllamaProvider(BaseProvider):
    def __init__(self):
        # Por padrão, o Ollama expõe a API na porta 11434 do localhost
        self.api_url = getattr(settings, "ollama_url", "http://localhost:11434/api/chat")

    async def generate_stream(self, model: str, messages: list[dict]) -> AsyncGenerator[str, None]:
        payload = {
            "model": model, # Ex: "llama3" ou "mistral"
            "messages": messages,
            "stream": True
        }

        # Timeout maior (120s) porque rodar LLM na CPU local demora para engatar a primeira marcha
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", self.api_url, json=payload) as response:
                
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line: # Ignora linhas vazias
                        try:
                            data_json = json.loads(line)
                            
                            # Extrai o texto do padrão Ollama
                            text_chunk = data_json.get("message", {}).get("content", "")
                            
                            if text_chunk:
                                # NORMALIZAÇÃO: Convertendo para o formato padrão (OpenAI / SSE)
                                openai_format = {"choices": [{"delta": {"content": text_chunk}}]}
                                yield f"data: {json.dumps(openai_format)}\n\n"
                                
                        except Exception as parse_error:
                            print(f"🟡 Erro no parser do Ollama: {parse_error}")
                            continue
                            
        yield "data: [DONE]\n\n"