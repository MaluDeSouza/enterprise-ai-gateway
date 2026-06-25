from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    environment: str = "development"
    port: int = 8000
    
    # As nossas chaves de API e Endereços
    openai_api_key: str = ""
    gemini_api_key: str = ""
    ollama_url: str = "http://localhost:11434/api/chat"

    # Bancos de dados
    redis_url: str = ""
    database_url: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"  # Diz pro Pydantic ignorar variáveis extras que não listamos aqui

# Instanciamos globalmente para todo o app usar
settings = Settings()