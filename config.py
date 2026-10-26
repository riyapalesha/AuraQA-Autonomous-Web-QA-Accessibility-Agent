import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Browser & Execution Settings
    HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
    DEFAULT_TIMEOUT_MS = int(os.getenv("DEFAULT_TIMEOUT_MS", "30000"))
    VIEWPORT_WIDTH = int(os.getenv("VIEWPORT_WIDTH", "1280"))
    VIEWPORT_HEIGHT = int(os.getenv("VIEWPORT_HEIGHT", "800"))
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 AuraQA/1.0"
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ASSETS_DIR = os.path.join(BASE_DIR, "assets")
    REPORTS_DIR = os.path.join(BASE_DIR, "reports")
    AXE_PATH = os.path.join(ASSETS_DIR, "axe.min.js")

    # Local LLM / Ollama Settings
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()  # ollama, openai, or local_heuristic

    # Cloud LLM fallback keys (optional)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

os.makedirs(Config.REPORTS_DIR, exist_ok=True)
