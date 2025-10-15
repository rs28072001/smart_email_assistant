from typing import TypedDict, List, Optional, Dict, Any
from typing_extensions import Annotated
from pydantic import BaseModel

class EmailMessage(BaseModel):
    from_email: str
    to: str
    subject: str
    body: str

class ConversationHistory(BaseModel):
    messages: List[Dict[str, Any]]

class EmailState(TypedDict):
    # Input
    email: EmailMessage
    history: Optional[ConversationHistory]
    
    # Processing
    intent: str
    summary: str
    memory_context: str
    tone: str
    
    # Output
    reply_subject: str
    reply_body: str
    escalate: bool
    confidence: float
    
    # Metadata
    timestamp: str