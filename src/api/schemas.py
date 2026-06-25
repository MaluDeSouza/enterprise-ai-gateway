from pydantic import BaseModel
from typing import Optional

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: list[Message]
    tenant_tier: str = "free" 
    
    document_b64: Optional[str] = None
    document_name: Optional[str] = None