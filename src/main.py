from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.api.v1.chat import router as chat_router
from src.core.database import engine, Base
from src.auth.models import Tenant 
from src.cache.manager import semantic_cache
from src.metrics.logger import setup_logger
from src.metrics.collector import router as metrics_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    # 0. Ativa o motor de logs estruturados em JSON
    setup_logger()
    
    # 1. Inicia o banco de dados relacional (Postgres)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # 2. Inicia o banco de dados vetorial (Redis)
    # (Como o logger já está ativo, estes prints já vão começar a sair formatados se usares o logger aqui também)
    print("⏳ Inicializando Índice Vetorial no Redis...")
    await semantic_cache.setup_index()
    print("✅ Índice Vetorial pronto!")
    
    yield # O servidor fica rodando aqui

# Inicializa o app injetando o nosso ciclo de vida unificado
app = FastAPI(lifespan=lifespan)

# Registra as rotas
app.include_router(chat_router, prefix="/v1")
app.include_router(metrics_router)

@app.get("/")
async def root():
    return {"status": "Enterprise AI Gateway Online 🚀"}