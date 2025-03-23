"""
Configuration settings for the Email Tracking System.

This file serves as the single source of truth for all configurable parameters.
Change settings here rather than modifying them in individual files.
"""

# ===== EMAIL SETTINGS =====
# Number of emails to download when processing
EMAILS_TO_DOWNLOAD = 10

# ===== MODEL SETTINGS =====
# Model settings for LLM integration
LLM_PROVIDER = "ollama"  # Options: "ollama", "openai", etc.
LLM_MODEL = "gemma3:latest"  # Model name to use with the provider
LLM_HOST = ""  # Host for local models like Ollama
LLM_TEMPERATURE = 0.0  # Lower for more deterministic outputs

# ===== UI SETTINGS =====
# Maximum number of emails to display per page
EMAILS_PER_PAGE = 10

# ===== DATABASE SETTINGS =====
# Database file path
DB_PATH = "emails.db"

# ===== DEBUG SETTINGS =====
# Default debug mode (can be overridden in UI)
DEFAULT_DEBUG_MODE = False

def get_llm_config():
    """
    Returns the LLM configuration as a dictionary
    """
    return {
        "provider": LLM_PROVIDER,
        "model": LLM_MODEL,
        "host": LLM_HOST,
        "temperature": LLM_TEMPERATURE
    }

def create_llm():
    """
    Creates an LLM instance based on the configuration
    """
    if LLM_PROVIDER == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=LLM_MODEL, temperature=LLM_TEMPERATURE)
    if LLM_PROVIDER == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)
    if LLM_PROVIDER == "deepseek":
        from langchain_deepseek import ChatDeepSeek
        return ChatDeepSeek(model=LLM_MODEL, temperature=LLM_TEMPERATURE)
    else:
        # For future expansion with other providers
        raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}") 