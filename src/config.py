"""Configuration management."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""
    
    # MongoDB Configuration
    CONNECTION_STRING = os.getenv("CONNECTION_STRING")
    DATABASE_NAME = os.getenv("DATABASE_NAME")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME")
    
    # Bot Configuration
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    PORT = int(os.environ.get("PORT", 8080))
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is missing")
        if not cls.WEBHOOK_URL:
            raise ValueError("WEBHOOK_URL is missing")
        if not cls.CONNECTION_STRING:
            raise ValueError("CONNECTION_STRING is missing")
        if not cls.DATABASE_NAME:
            raise ValueError("DATABASE_NAME is missing")
        if not cls.COLLECTION_NAME:
            raise ValueError("COLLECTION_NAME is missing")
