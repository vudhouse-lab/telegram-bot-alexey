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

OPENROUTER_MODEL = "mistralai/mistral-7b-instruct"
OPENROUTER_URL = "https://openrouter.io/api/v1/chat/completions"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN:
        return
    await update.message.reply_text("🤖 Bot online! (Using Mistral 7B - very cheap!)")

async def get_ai_response(user_message: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
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
                    "max_tokens": 300
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content']
            else:
                logger.error(f"OpenRouter error: {response.status_code}")
                return "❌ AI service error"
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"❌ Error: {str(e)}"

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN:
        return
    
    user_message = update.message.text
    
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
    logger.info("Bot polling started with OpenRouter (Mistral 7B)")
    await app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    asyncio.run(main())
