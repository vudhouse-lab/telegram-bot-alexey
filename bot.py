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

# Более надёжная модель
OPENROUTER_MODEL = "openchat/openchat-3.5"
OPENROUTER_URL = "https://openrouter.io/api/v1/chat/completions"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN:
        return
    await update.message.reply_text("🤖 Bot online! Asking OpenChat 3.5...")

async def get_ai_response(user_message: str) -> str:
    try:
        logger.info(f"Sending to OpenRouter: {user_message}")
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_KEY}",
                    "HTTP-Referer": "https://github.com/alexey-assistant",
                    "X-Title": "Alexey Assistant"
                },
                json={
                    "model": OPENROUTER_MODEL,
                    "messages": [
                        {"role": "user", "content": user_message}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 500
                }
            )
            
            logger.info(f"OpenRouter response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                result = data['choices'][0]['message']['content']
                logger.info(f"Got response: {result[:50]}...")
                return result
            else:
                error_text = response.text
                logger.error(f"OpenRouter error {response.status_code}: {error_text}")
                return f"❌ API Error: {response.status_code}"
    
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        return f"❌ Error: {str(e)}"

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN:
        return
    
    user_message = update.message.text
    logger.info(f"Got message: {user_message}")
    
    await update.message.chat.send_action("typing")
    
    response = await get_ai_response(user_message)
    
    if len(response) > 4096:
        for i in range(0, len(response), 4096):
            await update.message.reply_text(response[i:i+4096])
    else:
        await update.message.reply_text(response)

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    logger.info("Bot started with OpenRouter")
    await app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    asyncio.run(main())
