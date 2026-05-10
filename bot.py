#!/usr/bin/env python3
import os
import asyncio
import logging
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_ID", "0"))

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot online! Using Gemini 3.1 Flash Lite")

async def get_response(text: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_KEY}",
                    "HTTP-Referer": "https://github.com/alexey",
                    "X-OpenRouter-Title": "Alexey Bot"
                },
                json={
                    "model": "google/gemini-3.1-flash-lite",
                    "messages": [{"role": "user", "content": text}]
                }
            )
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                return f"Error {response.status_code}"
    except Exception as e:
        return f"❌ {str(e)}"

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.chat.send_action("typing")
    response = await get_response(update.message.text)
    await update.message.reply_text(response)

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
