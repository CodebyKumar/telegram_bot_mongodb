"""Bot command handlers."""
import os
import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

from src.db.queries import (
    export_mongo_collection_to_csv,
    get_stats,
    find_team_by_name,
    get_teams_with_transaction_numbers
)
from src.bot.helpers import (
    get_main_keyboard,
    format_team_details,
    format_stats_message,
    send_large_text_or_file,
    format_transactions_list
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    username = user.username or user.first_name or "Unknown"
    logger.info(f"User @{username} (ID: {user.id}) executed /start")
    
    await update.message.reply_text(
        "Welcome to the Brewathon Bot! 🦥\nUse the menu below to interact.",
        reply_markup=get_main_keyboard()
    )


async def send_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                     connection_string: str, database_name: str, collection_name: str):
    """Handle /stats command and View Stats button."""
    chat_id = update.effective_chat.id
    user = update.effective_user
    username = user.username or user.first_name or "Unknown"
    logger.info(f"User @{username} (ID: {user.id}) requested stats")

    loop = asyncio.get_running_loop()
    stats = await loop.run_in_executor(
        None, get_stats,
        connection_string, database_name, collection_name
    )

    msg = format_stats_message(stats)
    await context.bot.send_message(chat_id=chat_id, text=msg)


async def send_csv(update: Update, context: ContextTypes.DEFAULT_TYPE,
                   connection_string: str, database_name: str, collection_name: str):
    """Handle /registrations command and Download Registrations button."""
    chat_id = update.effective_chat.id
    user = update.effective_user
    username = user.username or user.first_name or "Unknown"
    logger.info(f"User @{username} (ID: {user.id}) requested CSV download")

    status_msg = await context.bot.send_message(chat_id=chat_id, text="Generating CSV...")

    output_file = "registrations.csv"

    loop = asyncio.get_running_loop()
    file_path = await loop.run_in_executor(
        None, export_mongo_collection_to_csv,
        connection_string, database_name, collection_name, output_file
    )

    try:
        if file_path and os.path.exists(file_path):
            await context.bot.send_document(
                chat_id=chat_id,
                document=open(file_path, "rb"),
                filename="registrations.csv",
                caption="Registrations file ready."
            )
            await context.bot.delete_message(chat_id, status_msg.message_id)
        else:
            await context.bot.send_message(chat_id=chat_id, text="Error creating CSV.")

    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)


async def find_command(update: Update, context: ContextTypes.DEFAULT_TYPE,
                       connection_string: str, database_name: str, collection_name: str):
    """Handle /find command to search for a team."""
    user = update.effective_user
    username = user.username or user.first_name or "Unknown"
    
    if not context.args:
        logger.info(f"User @{username} (ID: {user.id}) used /find without team name")
        await update.message.reply_text("Usage: /find team_name")
        return

    team_name = " ".join(context.args)
    logger.info(f"User @{username} (ID: {user.id}) searched for team: '{team_name}'")

    loop = asyncio.get_running_loop()
    team = await loop.run_in_executor(
        None, find_team_by_name,
        connection_string, database_name, collection_name, team_name
    )

    if team:
        msg = format_team_details(team)
    else:
        msg = f"No team found with name: {team_name}"

    await update.message.reply_text(msg)


async def send_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE,
                            connection_string: str, database_name: str, collection_name: str):
    """Handle /transactions command and View Transactions button."""
    chat_id = update.effective_chat.id
    user = update.effective_user
    username = user.username or user.first_name or "Unknown"
    logger.info(f"User @{username} (ID: {user.id}) requested transactions list")
    
    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(
        None, get_teams_with_transaction_numbers,
        connection_string, database_name, collection_name
    )
    
    if not data:
        await update.message.reply_text("No transactions found.")
        return

    formatted_text = format_transactions_list(data)
    await send_large_text_or_file(context, chat_id, formatted_text, "transactions_list.txt")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE,
                      connection_string: str, database_name: str, collection_name: str):
    """Handle text messages (menu button clicks)."""
    text = update.message.text.strip()
    user = update.effective_user
    username = user.username or user.first_name or "Unknown"
    logger.info(f"User @{username} (ID: {user.id}) sent message: '{text}'")

    if text.lower() == "hi":
        await update.message.reply_text(
            "Hello! Please use the menu buttons to interact.",
            reply_markup=get_main_keyboard()
        )

    elif text == "View Stats":
        await send_stats(update, context, connection_string, database_name, collection_name)

    elif text == "Download Registrations":
        await send_csv(update, context, connection_string, database_name, collection_name)

    elif text == "Find a Team":
        await update.message.reply_text("To search for a team, type:\n/find team_name")

    elif text == "View Transactions":
        await send_transactions(update, context, connection_string, database_name, collection_name)

    else:
        await update.message.reply_text(
            "I did not understand that. Please use the menu buttons.",
            reply_markup=get_main_keyboard()
        )
