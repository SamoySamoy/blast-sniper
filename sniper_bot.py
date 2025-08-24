import asyncio
import os
import logging
import requests
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Load environment variables
load_dotenv()
API_URL = os.getenv("API_URL", "https://example.com/api/tokens")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Your author validation function
from profile_crawl import scrape_x_profile_json


async def check_new_tokens(app):
    seen = set()
    while True:
        try:
            logging.info("Fetching new tokens...")
            resp = requests.get(API_URL, timeout=5)

            try:
                tokens = resp.json().get("tokens", [])
            except Exception:
                logging.error("Invalid JSON from API")
                tokens = []

            for token in tokens:
                token_id = token.get("id")
                if not token_id or token_id in seen:
                    continue
                seen.add(token_id)

                # Validate author
                author_url = token.get("author_x", "")
                try:
                    author_data = scrape_x_profile_json(author_url)
                except Exception as e:
                    logging.error(f"Error scraping author {author_url}: {e}")
                    author_data = {}

                followers = author_data.get("legacy", {}).get("followers_count", 0)
                author_name = author_data.get("core", {}).get("name", "Unknown")
                author_screen = author_data.get("core", {}).get("screen_name", "unknown")

                author_score = "✅ Good" if followers > 1000 else "⚠️ Low"

                # Build message
                text = (
                    f"🚀 New Token Listed!\n"
                    f"Name: {token.get('name', 'N/A')}\n"
                    f"Symbol: {token.get('symbol', 'N/A')}\n"
                    f"Author: {author_name} (@{author_screen})\n"
                    f"Followers: {followers}\n"
                    f"Validation: {author_score}"
                )
                keyboard = [[InlineKeyboardButton("💰 Buy Now", callback_data=f"buy:{token_id}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await app.bot.send_message(chat_id=CHAT_ID, text=text, reply_markup=reply_markup)
                logging.info(f"Sent alert for token {token.get('symbol')}")

        except Exception as e:
            logging.error(f"Error in check_new_tokens: {e}")

        await asyncio.sleep(3)  # Poll every 3 seconds


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sniper bot is running! ✅")


async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test command to send a message to the chat."""
    await context.bot.send_message(chat_id=CHAT_ID, text="🚀 Sniper Bot Test Message! ✅")


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("buy:"):
        token_id = query.data.split(":")[1]
        await query.edit_message_text(f"🛒 Buying token {token_id}... (feature coming soon)")


async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))  # ✅ New command
    app.add_handler(CallbackQueryHandler(button_click))

    # Background task for scanning tokens
    asyncio.create_task(check_new_tokens(app))

    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
