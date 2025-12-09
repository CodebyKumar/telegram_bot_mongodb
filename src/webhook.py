"""FastAPI webhook setup."""
import logging
from fastapi import FastAPI, Request
from telegram import Update

logger = logging.getLogger(__name__)


def create_app(get_telegram_app, lifespan=None) -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(title="Brewathon Telegram Bot", lifespan=lifespan)
    
    @app.get('/')
    async def index():
        """Health check endpoint."""
        return {"status": "Bot is running!"}
    
    @app.head('/')
    async def index_head():
        """Health check HEAD endpoint."""
        return {"status": "ok"}
    
    @app.post('/webhook')
    async def webhook(request: Request):
        """Handle webhook updates from Telegram."""
        try:
            json_data = await request.json()
            telegram_app = get_telegram_app()
            
            if telegram_app is None:
                logger.error("Telegram app is not initialized")
                return {"status": "error", "message": "Bot not initialized"}
            
            update = Update.de_json(json_data, telegram_app.bot)
            
            # Process update asynchronously using update_queue
            await telegram_app.update_queue.put(update)
            
            return {"status": "ok"}
        except Exception as e:
            logger.error(f"Webhook error: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}
    
    return app
