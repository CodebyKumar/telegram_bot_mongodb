"""FastAPI webhook setup."""
import logging
from fastapi import FastAPI, Request
from telegram import Update

logger = logging.getLogger(__name__)


def create_app(telegram_app) -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(title="Brewathon Telegram Bot")
    
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
            update = Update.de_json(json_data, telegram_app.bot)
            
            # Process update asynchronously
            await telegram_app.update_queue.put(update)
            
            return {"status": "ok"}
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return {"status": "error", "message": str(e)}
    
    return app
