import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    # LLM Settings
    PROVIDER = os.getenv("LLM_PROVIDER", "mock").lower()  # options: mock, openai, groq, gemini, ollama
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
    
    # Checkpointing DB
    DB_PATH = os.path.join(os.path.dirname(__file__), "agentflow_state.sqlite")
    
    # Mocking / Simulation Settings
    ENABLE_REAL_NOTIFICATIONS = os.getenv("ENABLE_REAL_NOTIFICATIONS", "false").lower() == "true"

def get_llm():
    """
    Returns an initialized LLM based on available configuration.
    Falls back gracefully to a robust MockLLM if no API keys are provided.
    """
    provider = Config.PROVIDER
    
    if provider == "openai" and Config.OPENAI_API_KEY:
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model="gpt-4o-mini", temperature=0)
        except ImportError:
            pass

    if provider == "groq" and Config.GROQ_API_KEY:
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0)
        except ImportError:
            pass

    if provider == "gemini" and Config.GEMINI_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
        except ImportError:
            pass

    if provider == "ollama":
        try:
            from langchain_community.chat_models import ChatOllama
            return ChatOllama(base_url=Config.OLLAMA_BASE_URL, model=Config.OLLAMA_MODEL)
        except ImportError:
            pass

    # Default fallback: MockLLM designed for testing, interview demos, and offline execution
    from core.mock_llm import MockWorkflowLLM
    return MockWorkflowLLM()
