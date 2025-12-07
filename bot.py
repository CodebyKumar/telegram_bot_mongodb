import os
import asyncio
import logging
from dotenv import load_dotenv

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

from mongo_utils import export_mongo_collection_to_csv, get_stats, find_team_by_name

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

# MongoDB Configuration
CONNECTION_STRING = os.getenv("CONNECTION_STRING")
DATABASE_NAME = os.getenv("DATABASE_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

# Bot token
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def get_main_keyboard():
    """Main keyboard layout."""
    keyboard = [
        [KeyboardButton("Check Status"), KeyboardButton("View Stats")],
        [KeyboardButton("Download Registrations"), KeyboardButton("Find a Team")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to the Brewathon Bot. Use the menu below to interact.",
        reply_markup=get_main_keyboard()
    )


async def send_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    loop = asyncio.get_running_loop()
    stats = await loop.run_in_executor(
        None, get_stats,
        CONNECTION_STRING, DATABASE_NAME, COLLECTION_NAME
    )

    if stats:
        msg = f"Registration Stats\n\nTotal Teams: {stats['total_teams']}"
    else:
        msg = "Unable to fetch statistics."

    await context.bot.send_message(chat_id=chat_id, text=msg)


async def send_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    status_msg = await context.bot.send_message(chat_id=chat_id, text="Generating CSV...")

    output_file = "registrations.csv"

    loop = asyncio.get_running_loop()
    file_path = await loop.run_in_executor(
        None, export_mongo_collection_to_csv,
        CONNECTION_STRING, DATABASE_NAME, COLLECTION_NAME, output_file
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


async def find_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /find team_name")
        return

    team_name = " ".join(context.args)

    loop = asyncio.get_running_loop()
    team = await loop.run_in_executor(
        None, find_team_by_name,
        CONNECTION_STRING, DATABASE_NAME, COLLECTION_NAME, team_name
    )

    if team:
        msg = f"Team Found: {team.get('teamName', 'Unknown')}\n\n"
        for key, value in team.items():
            if key != "_id":
                msg += f"{key}: {value}\n"
    else:
        msg = f"No team found with name: {team_name}"

    await update.message.reply_text(msg)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "Check Status" or text.lower() == "hi":
        await update.message.reply_text("You are connected to the bot and can continue.")

    elif text == "View Stats":
        await send_stats(update, context)

    elif text == "Download Registrations":
        await send_csv(update, context)

    elif text == "Find a Team":
        await update.message.reply_text("To search for a team, type:\n/find team_name")

    else:
        await update.message.reply_text("I did not understand that. Please use the menu buttons.")


if __name__ == "__main__":
    if not BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN missing")
    else:
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("stats", send_stats))
        app.add_handler(CommandHandler("find", find_command))
        app.add_handler(CommandHandler("registrations", send_csv))

        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

        app.run_polling()
