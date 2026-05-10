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
GEMINI_KEY = os.getenv("GEMINI_KEY")
ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_ID", "0"))

logger.info(f"GEMINI_KEY exists: {bool(GEMINI_KEY)}")

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Start command from {update.effective_user.id}")
    await update.message.reply_text("🤖 Bot online! Using Gemini 1.5 Flash")

async def get_gemini_response(text: str) -> str:
    logger.info(f"Calling Gemini with: {text[:50]}")
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        logger.info(f"URL: {url[:80]}...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json={"contents": [{"parts": [{"text": text}]}]}
            )
            logger.info(f"Gemini status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                result = data['candidates'][0]['content']['parts'][0]['text']
                logger.info(f"Gemini response: {result[:100]}")
                return result
            else:
                logger.error(f"Gemini error: {response.text[:200]}")
                return f"Gemini Error: {response.status_code}"
    except Exception as e:
        logger.error(f"Exception: {e}")
        return f"❌ Error: {str(e)}"

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Message from {update.effective_user.id}: {update.message.text[:50]}")
    
    if update.effective_user.id != ADMIN_ID:
        logger.warning(f"Unauthorized user: {update.effective_user.id}")
        return
    
    text = update.message.text
    logger.info(f"Processing message: {text}")
    
    await update.message.chat.send_action("typing")
    
    response = await get_gemini_response(text)
    logger.info(f"Sending response: {response[:100]}")
    
    await update.message.reply_text(response)

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    logger.info("Bot started successfully")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
