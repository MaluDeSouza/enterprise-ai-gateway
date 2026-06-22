import time
import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, Depends

from src.api.schemas import ChatRequest
# Importamos o nosso novo provedor real de IA!
from src.providers.gemini import GeminiProvider
from src.providers.ollama import OllamaProvider
from src.auth.dependencies import get_current_tenant
from src.auth.models import Tenant

from src.core.circuit_breaker import CircuitBreaker
from src.core.policy_engine import PolicyEngine
from src.cache.manager import SemanticCache 

router = APIRouter()

circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60.0)
policy_engine = PolicyEngine(circuit_breaker)
semantic_cache = SemanticCache() 

async def stream_generator(provider, request: ChatRequest):
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    try:
        # Aqui o httpx.AsyncClient entra em ação de verdade!
        async for chunk in provider.generate_stream(request.model, messages):
            yield chunk
            
        # Avisamos o disjuntor que a API do Google respondeu com sucesso
        if isinstance(provider, GeminiProvider):
            circuit_breaker.record_success()
            
    except Exception as e:
        if isinstance(provider, GeminiProvider):
            circuit_breaker.record_failure()
            
        # Logamos o erro exato e a linha no terminal do backend
        print(f"🔴 ERRO INTERNO DETECTADO: {repr(e)}")
        
        # O repr(e) garante que a mensagem de erro nunca mais venha vazia no cliente
        yield f"data: [FALHA DE CONEXÃO COM A IA: {repr(e)}]\n\n"
        yield "data: [DONE]\n\n"

async def cache_stream_generator(cached_response: str):
    words = cached_response.split()
    for word in words:
        yield f"data: {word} \n\n"
        await asyncio.sleep(0.05)
    yield "data: [DONE]\n\n"

@router.post("/chat/completions")
async def chat_completion(
    request: ChatRequest,
    tenant: Tenant = Depends(get_current_tenant)
):
    start_time = time.time()
    
    user_message = request.messages[-1].content
    cached_response = semantic_cache.check_cache(user_message)
    
    if cached_response:
        process_time = time.time() - start_time
        print(f"🟢 [MÉTRICA - CACHE HIT] Resposta servida em {process_time:.4f} segundos! Custo: $0.00")
        
        return StreamingResponse(
            cache_stream_generator(cached_response),
            media_type="text/event-stream"
        )
        
    # AQUI ESTÁ A MÁGICA: O Gateway vira apenas um "cano" delegador
    provider, origem = policy_engine.get_provider_for_tenant(tenant)
        
    process_time = time.time() - start_time
    print(f"🟡 [MÉTRICA - CACHE MISS] Roteado para {origem} em {process_time:.4f} segundos.")
        
    # O Gateway retorna o stream SSE diretamente para a aplicação cliente usando Inversão de Dependência
    return StreamingResponse(
        stream_generator(provider, request),
        media_type="text/event-stream"
    )