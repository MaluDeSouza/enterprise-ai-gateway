import json
import httpx
from typing import AsyncGenerator
from src.providers.base import BaseProvider
from src.config import settings

class GeminiProvider(BaseProvider):
    def __init__(self):
        # Usando a tag -latest para garantir que a API encontre o modelo ativo
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:streamGenerateContent?alt=sse&key={settings.gemini_api_key.strip()}"

    async def generate_stream(self, model: str, messages: list[dict]) -> AsyncGenerator[str, None]:
        # Convertemos as mensagens do padrão OpenAI para o padrão que o Gemini entende
        gemini_messages = [{"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]} for m in messages]
        
        payload = {"contents": gemini_messages}

               # Adicionamos o timeout de 60 segundos para IAs que demoram a responder
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", self.api_url, json=payload) as response:
                
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data_json = json.loads(data_str)
                            
                            # 1. Extração segura
                            candidates = data_json.get("candidates", [])
                            if not candidates:
                                continue
                                
                            # CUIDADO AQUI: candidates é uma lista! Pegamos o [0] primeiro.
                            content = candidates[0].get("content", {})
                            parts = content.get("parts", [])
                            
                            # 2. Junta todos os pedaços de texto
                            text_chunk = ""
                            for part in parts:
                                text_chunk += part.get("text", "")
                                
                            # 3. Se for status vazio, ignora
                            if not text_chunk:
                                continue
                                
                            # 4. NORMALIZAÇÃO: Padrão universal (OpenAI)
                            openai_format = {"choices": [{"delta": {"content": text_chunk}}]}
                            
                            yield f"data: {json.dumps(openai_format)}\n\n"
                            
                        except Exception as parse_error:
                            print(f"🟡 Erro no parser do Gemini: {parse_error} | Dado puro: {data_str}")
                            continue
                            
        yield "data: [DONE]\n\n"