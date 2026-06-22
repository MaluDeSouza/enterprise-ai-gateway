from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    environment: str = "development"
    port: int = 8000
    
    # As nossas chaves de API
    openai_api_key: str = ""
    gemini_api_key: str = ""

    # NOVO: Ensinando o Pydantic a ler as variáveis de banco de dados
    redis_url: str = ""
    database_url: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"  # Diz pro Pydantic ignorar variáveis extras que não listamos aqui

# Instanciamos globalmente para todo o app usar
settings = Settings()