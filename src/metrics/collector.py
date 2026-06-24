from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter
from fastapi.responses import Response

router = APIRouter()

# 1. Contador: Quantas requisições passaram por aqui? (Separado por hit/miss)
REQUEST_COUNT = Counter(
    "gateway_requests_total",
    "Total de requisições recebidas no Gateway",
    ["tenant_id", "status"] 
)

# 2. Histograma: Qual o tempo de resposta?
LATENCY = Histogram(
    "gateway_request_latency_seconds",
    "Tempo de processamento da requisição",
    ["tenant_id", "route_type"]
)

# 3. A Caixa Registradora: Dinheiro economizado (em USD)
COST_SAVED = Counter(
    "gateway_cost_saved_usd_total",
    "Total de dólares economizados graças ao Cache Semântico",
    ["tenant_id"]
)

# 4. Contador de Falhas
ERROR_COUNT = Counter(
    "gateway_errors_total",
    "Total de erros nos provedores de IA",
    ["provider"]
)

@router.get("/metrics")
async def metrics():
    """Expõe os dados matemáticos para o Prometheus (ou Datadog) ler."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)