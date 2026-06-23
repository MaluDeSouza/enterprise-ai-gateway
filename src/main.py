from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.api.v1.chat import router as chat_router
from src.core.database import engine, Base
from src.auth.models import Tenant # Importante para o SQLAlchemy criar a tabela
from src.cache.manager import semantic_cache

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Inicia o banco de dados relacional (Postgres)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # 2. Inicia o banco de dados vetorial (Redis)
    print("⏳ Inicializando Índice Vetorial no Redis...")
    await semantic_cache.setup_index()
    print("✅ Índice Vetorial pronto!")
    
    yield # O servidor fica rodando aqui

# Inicializa o app injetando o nosso ciclo de vida unificado
app = FastAPI(lifespan=lifespan)

# Registra as rotas
app.include_router(chat_router, prefix="/v1")

@app.get("/")
async def root():
    return {"status": "Enterprise AI Gateway Online 🚀"}