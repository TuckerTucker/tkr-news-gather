import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Anthropic
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
    LLM_TEMP = float(os.getenv("LLM_TEMP", "0.7"))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2000"))
    
    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # News settings
    DEFAULT_NEWS_LIMIT = int(os.getenv("DEFAULT_NEWS_LIMIT", "10"))
    SCRAPE_TIMEOUT = int(os.getenv("SCRAPE_TIMEOUT", "30"))
    MAX_CONCURRENT_SCRAPES = int(os.getenv("MAX_CONCURRENT_SCRAPES", "10"))
    
    # API settings
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    
    # Security settings
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    API_KEYS = os.getenv("API_KEYS")  # Comma-separated list
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    ENABLE_SECURITY_HEADERS = os.getenv("ENABLE_SECURITY_HEADERS", "true").lower() == "true"
    
    # Development settings
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    ENABLE_METRICS = os.getenv("ENABLE_METRICS", "false").lower() == "true"