import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text="🚀 Sniper Bot Test Message! ✅")
    print("Message sent!")

if __name__ == "__main__":
    asyncio.run(main())
