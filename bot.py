"""Main bot application entry point."""
import asyncio
import logging
import uvicorn

from src.config import Config
from src.app import setup_application, setup_webhook
from src.webhook import create_app

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main():
    """Main application entry point."""
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        exit(1)
    
    # Set up Telegram application
    telegram_app = setup_application(
        bot_token=Config.BOT_TOKEN,
        connection_string=Config.CONNECTION_STRING,
        database_name=Config.DATABASE_NAME,
        collection_name=Config.COLLECTION_NAME
    )
    
    # Create FastAPI app
    fastapi_app = create_app(telegram_app)
    
    # Set up webhook
    asyncio.run(setup_webhook(telegram_app.bot, Config.WEBHOOK_URL))
    
    # Run FastAPI app with Uvicorn
    logger.info(f"Starting FastAPI server on port {Config.PORT}")
    uvicorn.run(fastapi_app, host="0.0.0.0", port=Config.PORT)


if __name__ == "__main__":
    main()
