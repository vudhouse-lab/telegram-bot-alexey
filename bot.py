#!/usr/bin/env python3
import os
import logging
import httpx
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
ADMIN = int(os.getenv("TELEGRAM_ADMIN_ID", "0"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN:
        return
    key_status = "✅ Present" if OPENROUTER_KEY else "❌ Missing"
    await update.message.reply_text(f"🤖 Bot online!\nAPI Key: {key_status}")

async def test_openrouter():
    """Test OpenRouter connection"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.io/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_KEY}",
                    "HTTP-Referer": "https://github.com/alexey-assistant",
                    "X-Title": "Alexey Assistant"
                },
                json={
                    "model": "openchat/openchat-3.5",
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 100
                }
            )
            
            logger.info(f"Status: {response.status_code}")
            logger.info(f"Response: {response.text[:500]}")
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                return f"API Error {response.status_code}"
    except Exception as e:
        logger.error(f"Exception: {e}")
        return f"Error: {e}"

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN:
        return
    
    user_message = update.message.text
    logger.info(f"Message: {user_message}")
    
    await update.message.chat.send_action("typing")
    
    result = await test_openrouter()
    logger.info(f"Result: {result}")
    
    await update.message.reply_text(f"Response: {result}")

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    logger.info("Bot started")
    await app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    asyncio.run(main())
