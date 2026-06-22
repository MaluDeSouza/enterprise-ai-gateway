from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.core.database import get_db
from src.auth.models import Tenant
from src.rate_limit.limiter import RateLimiter # Importando o nosso Guardião!

# Ensina o FastAPI a procurar a senha no cabeçalho "Authorization"
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

# Instanciamos o limitador no escopo global para ele gerenciar a conexão com eficiência
limiter = RateLimiter()

async def get_current_tenant(
    api_key: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> Tenant:
    if not api_key:
        raise HTTPException(status_code=401, detail="⚠️ Acesso Negado: API Key não fornecida.")
    
    # Limpa a chave caso o front-end envie a palavra "Bearer " na frente
    clean_key = api_key.replace("Bearer ", "") if "Bearer " in api_key else api_key

    # 1. Validação Absoluta (PostgreSQL)
    result = await db.execute(select(Tenant).where(Tenant.api_key == clean_key))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=403, detail="🚫 Acesso Negado: API Key inválida.")
    
    if not tenant.is_active:
        raise HTTPException(status_code=403, detail="🚫 Acesso Negado: Conta desativada.")

    # 2. A Trava Financeira (Redis Rate Limiter)
    is_allowed = await limiter.check_rate_limit(clean_key)
    
    if not is_allowed:
        raise HTTPException(
            status_code=429, 
            detail="⚠️ Too Many Requests: O seu limite de requisições por minuto esgotou. Aguarde um instante."
        )

    # Se passou pelo banco e tem saldo no Redis, acesso liberado!
    return tenant