from sqlalchemy import Column, Integer, String, Boolean
from src.core.database import Base

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    
    # A "senha" que o usuário vai digitar no nosso Streamlit
    api_key = Column(String, unique=True, index=True, nullable=False)
    
    # É aqui que definimos quem é Free e quem é Premium!
    tier = Column(String, default="free", nullable=False) 
    
    is_active = Column(Boolean, default=True)