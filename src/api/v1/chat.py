import time
import asyncio
import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from src.api.schemas import ChatRequest
from src.auth.dependencies import get_current_tenant
from src.auth.models import Tenant

from src.core.circuit_breaker import CircuitBreaker
from src.core.policy_engine import PolicyEngine
from src.cache.manager import semantic_cache
from src.providers.gemini import GeminiProvider
from src.providers.ollama import OllamaProvider

router = APIRouter()

# Setup das engrenagens principais
circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60.0)
policy_engine = PolicyEngine(circuit_breaker)

async def stream_generator(provider, request: ChatRequest):
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    
    # Variáveis para capturarmos a conversa e o resultado
    user_prompt = request.messages[-1].content
    full_response = ""
    
    try:
        async for chunk in provider.generate_stream(request.model, messages):
            yield chunk
            
            # Interceptamos o fluxo SSE para extrair apenas o texto puro da IA
            if chunk.startswith("data: ") and "[DONE]" not in chunk:
                try:
                    data_json = json.loads(chunk[6:])
                    text = data_json["choices"][0]["delta"].get("content", "")
                    full_response += text
                except:
                    pass
            
        # Quando a IA terminar de falar, nós salvamos o resultado no Redis
        if full_response:
            await semantic_cache.save_to_cache(user_prompt, full_response)
            
        if isinstance(provider, GeminiProvider):
            circuit_breaker.record_success()
            
    except Exception as e:
        if isinstance(provider, GeminiProvider):
            circuit_breaker.record_failure()
            
        print(f"🔴 ERRO INTERNO DETECTADO: {repr(e)}")
        # Retorna o erro no formato normalizado para o front-end não quebrar
        error_json = {"choices": [{"delta": {"content": f"[FALHA DE CONEXÃO: {repr(e)}] "}}]}
        yield f"data: {json.dumps(error_json)}\n\n"
        yield "data: [DONE]\n\n"

async def cache_stream_generator(cached_response: str):
    words = cached_response.split()
    for word in words:
        # Emitimos o cache no formato universal blindado
        chunk_data = {"choices": [{"delta": {"content": word + " "}}]}
        yield f"data: {json.dumps(chunk_data)}\n\n"
        await asyncio.sleep(0.05)
    yield "data: [DONE]\n\n"

@router.post("/chat/completions")
async def chat_completion(
    request: ChatRequest,
    tenant: Tenant = Depends(get_current_tenant)
):
    start_time = time.time()
    
    user_message = request.messages[-1].content
    cached_response = await semantic_cache.check_cache(user_message)
    
    if cached_response:
        process_time = time.time() - start_time
        print(f"🟢 [MÉTRICA - CACHE HIT] Resposta servida em {process_time:.4f} segundos! Custo: $0.00")
        
        return StreamingResponse(
            cache_stream_generator(cached_response),
            media_type="text/event-stream"
        )
        
    # O Gateway vira apenas um "cano" delegador
    provider, origem = policy_engine.get_provider_for_tenant(tenant)
        
    process_time = time.time() - start_time
    print(f"🟡 [MÉTRICA - CACHE MISS] Roteado para {origem} em {process_time:.4f} segundos.")
        
    # O Gateway retorna o stream SSE diretamente para a aplicação cliente
    return StreamingResponse(
        stream_generator(provider, request),
        media_type="text/event-stream"
    )