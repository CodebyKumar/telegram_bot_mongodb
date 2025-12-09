"""Application setup and initialization."""
import logging
from functools import partial
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from src.bot.handlers import (
    start, send_stats, send_csv, find_command,
    send_transactions, handle_text
)

logger = logging.getLogger(__name__)


def setup_application(bot_token: str, connection_string: str, 
                     database_name: str, collection_name: str):
    """Set up the Telegram application with handlers."""
    application = ApplicationBuilder().token(bot_token).build()

    # Create partial functions with database credentials
    stats_handler = partial(send_stats, 
                           connection_string=connection_string,
                           database_name=database_name,
                           collection_name=collection_name)
    
    csv_handler = partial(send_csv,
                         connection_string=connection_string,
                         database_name=database_name,
                         collection_name=collection_name)
    
    find_handler = partial(find_command,
                          connection_string=connection_string,
                          database_name=database_name,
                          collection_name=collection_name)
    
    transactions_handler = partial(send_transactions,
                                  connection_string=connection_string,
                                  database_name=database_name,
                                  collection_name=collection_name)
    
    text_handler = partial(handle_text,
                          connection_string=connection_string,
                          database_name=database_name,
                          collection_name=collection_name)

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats_handler))
    application.add_handler(CommandHandler("find", find_handler))
    application.add_handler(CommandHandler("registrations", csv_handler))
    application.add_handler(CommandHandler("transactions", transactions_handler))

    # Add message handler for menu buttons
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    return application


async def setup_webhook(bot, webhook_url: str):
    """Set up webhook for the bot."""
    webhook_endpoint = f"{webhook_url}/webhook"
    await bot.set_webhook(url=webhook_endpoint)
    logger.info(f"Webhook set to: {webhook_endpoint}")
