from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.api.v1.chat import router as chat_router
from src.core.database import engine, Base

# NOVO: Importando a classe explicitamente para o SQLAlchemy enxergar e criar a tabela!
from src.auth.models import Tenant 

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Conecta no banco e cria as tabelas baseadas nos modelos importados acima
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(chat_router, prefix="/v1")

@app.get("/")
async def root():
    return {"status": "Gateway Online"}