#!/usr/bin/env python3
import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import AsyncOpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_ID", "0"))

# OpenRouter client (как в документации)
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_KEY
)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Start command")
    await update.message.reply_text("🤖 Bot online! Using OpenRouter")

async def get_response(text: str) -> str:
    try:
        logger.info(f"Calling OpenRouter: {text[:50]}")
        
        response = await client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://github.com/alexey-assistant",
                "X-OpenRouter-Title": "Alexey Assistant"
            },
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": text}]
        )
        
        result = response.choices[0].message.content
        logger.info(f"Got response: {result[:100]}")
        return result
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"❌ Error: {str(e)}"

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    text = update.message.text
    logger.info(f"Message: {text}")
    
    await update.message.chat.send_action("typing")
    response = await get_response(text)
    await update.message.reply_text(response)

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    logger.info("Bot started")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
