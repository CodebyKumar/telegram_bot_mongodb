"""Main bot application entry point."""
import asyncio
import logging
import uvicorn
from contextlib import asynccontextmanager

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

# Global telegram application
telegram_app = None


async def setup_bot():
    """Initialize and set up the bot."""
    global telegram_app
    
    # Set up Telegram application
    telegram_app = setup_application(
        bot_token=Config.BOT_TOKEN,
        connection_string=Config.CONNECTION_STRING,
        database_name=Config.DATABASE_NAME,
        collection_name=Config.COLLECTION_NAME
    )
    
    # Initialize the application
    await telegram_app.initialize()
    await telegram_app.start()
    
    # Set up webhook
    await setup_webhook(telegram_app.bot, Config.WEBHOOK_URL)
    
    logger.info("Bot initialized and started successfully")
    return telegram_app


@asynccontextmanager
async def lifespan(app):
    """Lifespan context manager for FastAPI."""
    # Startup
    await setup_bot()
    yield
    # Shutdown
    if telegram_app:
        await telegram_app.stop()
        await telegram_app.shutdown()


def main():
    """Main application entry point."""
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        exit(1)
    
    # Create FastAPI app with lifespan
    fastapi_app = create_app(lambda: telegram_app, lifespan)
    
    # Run FastAPI app with Uvicorn
    logger.info(f"Starting FastAPI server on port {Config.PORT}")
    uvicorn.run(fastapi_app, host="0.0.0.0", port=Config.PORT)


if __name__ == "__main__":
    main()
