import asyncio
from src.core.database import AsyncSessionLocal
from src.auth.models import Tenant

async def seed_data():
    async with AsyncSessionLocal() as session:
        # Criando nossos dois usuários de teste
        premium_user = Tenant(name="Departamento de Marketing", api_key="premium-key-123", tier="premium")
        free_user = Tenant(name="Estagiários", api_key="free-key-456", tier="free")
        
        # Adicionando na sessão
        session.add(premium_user)
        session.add(free_user)
        
        try:
            # Salvando no banco de dados (Commit)
            await session.commit()
            print("✅ Usuários inseridos com sucesso no banco de dados!")
        except Exception as e:
            print(f"⚠️ Erro ao inserir (Talvez eles já existam?): {e}")

if __name__ == "__main__":
    # Rodando a nossa função assíncrona
    asyncio.run(seed_data())