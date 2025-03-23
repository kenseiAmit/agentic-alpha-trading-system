# Configuration file for API keys and settings
# Replace the placeholder values with your actual API keys or set them as environment variables
import os

class Config:
    # OpenAI API Configuration
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    # Alternative AI Service (Anthropic) - Optional
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "your_anthropic_api_key_here")  # Optional, only if using Anthropic
    
    # Financial Data APIs - Optional
    # I am leaving these here to know there are other apis that you can use in the future.
    ALPHA_VANTAGE_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "your_alpha_vantage_key_here")  # Optional, for additional market data
    QUANDL_API_KEY = os.environ.get("QUANDL_API_KEY", "your_quandl_key_here")  # Optional, for financial data
    
    # News and Sentiment APIs - Optional  
    # I am leaving this here to show that taviliy is a great way to use news api to get better sentiment analysis.
    TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "your_tavily_key_here")  # Optional, for news sentiment analysis
    
    # Database Configuration
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///data_storage/trading.db")  # Supports SQLite out of the box and PostgreSQL
    
    # Application Settings
    DEFAULT_SYMBOL = "AAPL"
    CACHE_TIMEOUT_HOURS = 12
    
    # AI Model Settings
    DEFAULT_AI_MODEL = "gpt-4o"  # or "claude-sonnet-4-20250514" if using Anthropic
    USE_OPENAI = True  # Set to False to use Anthropic instead

# Instructions for setup:
# 1. Set the OPENAI_API_KEY environment variable (export OPENAI_API_KEY="...") or paste your key above
# 2. For local database, install PostgreSQL or use SQLite by changing DATABASE_URL
