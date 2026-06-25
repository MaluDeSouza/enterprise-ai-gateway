import time
import asyncio
import json
import base64
import fitz  # PyMuPDF
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from src.api.schemas import ChatRequest
from src.auth.dependencies import get_current_tenant
from src.auth.models import Tenant

from src.core.circuit_breaker import CircuitBreaker
from src.core.policy_engine import PolicyEngine
from src.core.dlp_scanner import DLPScanner
from src.cache.manager import semantic_cache
from src.providers.gemini import GeminiProvider
from src.providers.ollama import OllamaProvider
from src.metrics.logger import get_logger
from src.metrics.collector import REQUEST_COUNT, LATENCY, COST_SAVED, ERROR_COUNT

router = APIRouter()

# Setup das engrenagens principais e governança de dados
circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60.0)
policy_engine = PolicyEngine(circuit_breaker)
dlp_scanner = DLPScanner()
logger = get_logger("chat_gateway")

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
            
        # Registra o erro no log estruturado
        logger.error(
            "provider_failure",
            error=repr(e),
            provider=provider.__class__.__name__
        )
        
        # Contador de erro do Prometheus
        ERROR_COUNT.labels(provider=provider.__class__.__name__).inc()
        
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
    
    # 🛡️ 1. Verifica o texto digitado (Prompt)
    if dlp_scanner.has_pii(request.messages[-1].content):
        logger.warning("dlp_block_prompt", tenant_id=tenant.id)
        raise HTTPException(
            status_code=406, 
            detail="Acesso Bloqueado: Informação Sensível (PII) detectada no texto."
        )

    # 🛡️ 2. Verifica o anexo e INJETA O CONTEXTO (A essência da IA Contextual)
    if request.document_b64:
        try:
            # Extraímos o texto aqui mesmo no roteador
            pdf_bytes = base64.b64decode(request.document_b64)
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            document_text = "".join(page.get_text() for page in doc)

            # Passamos o texto puro no Cão de Guarda
            if dlp_scanner.has_pii(document_text):
                logger.warning("dlp_block_document", tenant_id=tenant.id, filename=request.document_name)
                raise HTTPException(
                    status_code=406, 
                    detail=f"Acesso Bloqueado: O arquivo '{request.document_name}' contém informações sensíveis."
                )

            # 👉 A INJEÇÃO: Se passou na aduana, anexamos o texto ao prompt do usuário!
            context_prompt = f"\n\n--- CONTEÚDO DO DOCUMENTO ({request.document_name}) ---\n{document_text}\n--- FIM DO DOCUMENTO ---"
            request.messages[-1].content += context_prompt

        except HTTPException:
            raise  # Repassa o erro 406 do DLP sem mascarar
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro ao processar o anexo: {e}")

    # Captura a mensagem final (agora turbinada com o PDF) para o Cache Semântico
    user_message = request.messages[-1].content
    
    # O fluxo normal de otimização e cache continua daqui para baixo...
    cached_response = await semantic_cache.check_cache(user_message)
    
    if cached_response:
        process_time = time.time() - start_time
        
        logger.info(
            "cache_hit",
            tenant_id=tenant.id,
            tier=tenant.tier,
            latency_seconds=round(process_time, 4),
            cost_saved=0.01
        )
        REQUEST_COUNT.labels(tenant_id=tenant.id, status="cache_hit").inc()
        LATENCY.labels(tenant_id=tenant.id, route_type="cache").observe(process_time)
        COST_SAVED.labels(tenant_id=tenant.id).inc(0.01)
        
        return StreamingResponse(
            cache_stream_generator(cached_response),
            media_type="text/event-stream"
        )
        
    # O Gateway vira apenas um "cano" delegador
    provider, origem = policy_engine.get_provider_for_tenant(tenant)
        
    process_time = time.time() - start_time
    logger.info(
        "cache_miss",
        tenant_id=tenant.id,
        provider_routed=origem,
        latency_seconds=round(process_time, 4)
    )
    REQUEST_COUNT.labels(tenant_id=tenant.id, status="cache_miss").inc()
    LATENCY.labels(tenant_id=tenant.id, route_type="provider").observe(process_time)
        
    # O Gateway retorna o stream SSE diretamente para a aplicação cliente
    return StreamingResponse(
        stream_generator(provider, request),
        media_type="text/event-stream"
    )