from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.core.database import get_db
from src.auth.models import Tenant

# Ensina o FastAPI a procurar a senha no cabeçalho "Authorization"
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

async def get_current_tenant(
    api_key: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> Tenant:
    if not api_key:
        raise HTTPException(status_code=401, detail="⚠️ Acesso Negado: API Key não fornecida.")
    
    # Limpa a chave caso o front-end envie a palavra "Bearer " na frente
    clean_key = api_key.replace("Bearer ", "") if "Bearer " in api_key else api_key

    # Busca o usuário no PostgreSQL
    result = await db.execute(select(Tenant).where(Tenant.api_key == clean_key))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=403, detail="🚫 Acesso Negado: API Key inválida.")
    
    if not tenant.is_active:
        raise HTTPException(status_code=403, detail="🚫 Acesso Negado: Conta desativada.")

    return tenant