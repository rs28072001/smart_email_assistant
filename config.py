import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # LLM Configuration
    LLM_MODEL = "gpt-4o"
    LLM_TEMPERATURE = 0.1
    
    # Memory Configuration
    MAX_HISTORY_LENGTH = 5
    
    # Escalation Configuration
    COMPLAINT_ESCALATION_THRESHOLD = 0.8
    
    # Tone Configuration
    DEFAULT_TONE = "neutral"  # formal, friendly, neutral

def get_llm():
    return ChatOpenAI(
        model=Config.LLM_MODEL,
        temperature=Config.LLM_TEMPERATURE,
        api_key=Config.OPENAI_API_KEY
    )