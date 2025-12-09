"""Helper functions for bot operations."""
import os
import asyncio
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.constants import ParseMode


def get_main_keyboard():
    """Main keyboard layout for bot menu."""
    keyboard = [
        [KeyboardButton("View Stats"), KeyboardButton("View Transactions")],
        [KeyboardButton("Download Registrations"), KeyboardButton("Find a Team")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)


def format_transaction_chunk(transactions, start_index, chunk_size=20):
    """Format a chunk of transactions for display."""
    chunk = transactions[start_index : start_index + chunk_size]
    msg = "Team Transactions:\n\n"
    for t in chunk:
        name = t.get("teamName", "N/A")
        tid = t.get("transactionId", "N/A")
        msg += f"• *{name}*: `{tid}`\n"
    return msg


def format_team_details(team):
    """Format team details for display."""
    if not team:
        return "No team data available."
    
    msg = f"Team Found: {team.get('teamName', 'Unknown')}\n\n"
    for key, value in team.items():
        if key != "_id":
            msg += f"{key}: {value}\n"
    return msg


def format_stats_message(stats):
    """Format statistics for display."""
    if stats:
        msg = (
            f"Registration Stats\n\n"
            f"Total Teams: {stats.get('total_teams', 0)}\n"
            f"Total Members: {stats.get('total_members', 0)}"
        )
    else:
        msg = "Unable to fetch statistics."
    return msg


async def send_large_text_or_file(context, chat_id, text, filename="output.txt"):
    """Send text as message or file if too large."""
    # Telegram message limit is 4096 chars
    if len(text) > 4000:
        # Save to file
        with open(filename, "w", encoding="utf-8") as f:
            f.write(text)
            
        await context.bot.send_document(
            chat_id=chat_id,
            document=open(filename, "rb"),
            caption="List is too long, sending as file."
        )
        os.remove(filename)
    else:
        # Send as text message
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"```\n{text}```",
            parse_mode=ParseMode.MARKDOWN
        )


def format_transactions_list(data):
    """Format list of transactions as text."""
    formatted_text = ""
    for item in data:
        t_name = item.get("teamName", "Unknown")
        t_id = item.get("transactionId", "N/A")
        formatted_text += f"{t_name}: {t_id}\n"
    return formatted_text
