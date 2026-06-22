from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from src.config import settings

# Pegamos a URL do banco que você configurou no .env
# Caso não encontre, usamos o padrão do nosso Docker de desenvolvimento
DATABASE_URL = settings.database_url or "postgresql+asyncpg://admin:admin123@localhost:5432/gateway_db"

# Criamos a "engine" (o motor assíncrono que conversa com o Postgres)
engine = create_async_engine(DATABASE_URL, echo=True)

# Criamos a fábrica de sessões (para abrir e fechar transações com segurança)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# A classe Base que nossas tabelas vão herdar
Base = declarative_base()

# Função injetável que as rotas do FastAPI vão usar para pegar uma sessão do banco
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session