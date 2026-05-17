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
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_ID", "0"))

logger.info(f"Bot initialized with ADMIN_ID: {ADMIN_ID}")
logger.info(f"GEMINI_KEY set: {bool(GEMINI_KEY)}")

user_conversations = {}

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"START from user {user_id}")
    user_conversations[user_id] = []
    await update.message.reply_text("🤖 Bot online! Gemini 3.1 Flash Lite + Memory")

async def get_response(user_id: int, text: str) -> str:
    try:
        logger.info(f"Getting response for user {user_id}: {text[:50]}")
        
        if user_id not in user_conversations:
            user_conversations[user_id] = []
        
        user_conversations[user_id].append({"role": "user", "parts": [{"text": text}]})
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info("Sending request to Gemini API")
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent",
                headers={
                    "x-goog-api-key": GEMINI_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "contents": user_conversations[user_id],
                    "generationConfig": {"maxOutputTokens": 2000}
                }
            )
            
            logger.info(f"Gemini response status: {response.status_code}")
            
            if response.status_code == 200:
                ai_response = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                user_conversations[user_id].append({"role": "model", "parts": [{"text": ai_response}]})
                logger.info(f"Got response: {ai_response[:50]}")
                return ai_response
            else:
                error = f"Error {response.status_code}: {response.text[:100]}"
                logger.error(error)
                return error
    except Exception as e:
        logger.error(f"Exception in get_response: {str(e)}")
        return f"❌ {str(e)}"

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"Message from user {user_id}, ADMIN_ID={ADMIN_ID}")
    
    if user_id != ADMIN_ID:
        logger.warning(f"Access denied for user {user_id}")
        await update.message.reply_text("❌ You are not authorized")
        return
    
    logger.info(f"Processing message from authorized user {user_id}")
    await update.message.chat.send_action("typing")
    response = await get_response(user_id, update.message.text)
    
    if len(response) > 4096:
        for i in range(0, len(response), 4096):
            await update.message.reply_text(response[i:i+4096])
    else:
        await update.message.reply_text(response)

async def clear_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    user_conversations[user_id] = []
    await update.message.reply_text("💾 Memory cleared")

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("clear", clear_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
