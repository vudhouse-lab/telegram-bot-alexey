#!/usr/bin/env python3
import os
import asyncio
import logging
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("8078996700:AAHrX2y0ikL6zU61os0oO_lVvKhKx1be1mc")
GEMINI_KEY = os.getenv("AIzaSyAgHhzfxP-yFpxhKk46kiu0qJybdRsKjao")
ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_ID", "7554064446"))

user_conversations = {}

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_conversations[user_id] = []
    await update.message.reply_text("🤖 Bot online! Gemini 3.1 Flash Lite + Memory")

async def get_response(user_id: int, text: str) -> str:
    try:
        if user_id not in user_conversations:
            user_conversations[user_id] = []
        
        user_conversations[user_id].append({"role": "user", "parts": [{"text": text}]})
        
        async with httpx.AsyncClient(timeout=30.0) as client:
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
            
            if response.status_code == 200:
                ai_response = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                user_conversations[user_id].append({"role": "model", "parts": [{"text": ai_response}]})
                return ai_response
            else:
                return f"Error {response.status_code}: {response.text[:100]}"
    except Exception as e:
        return f"❌ {str(e)}"

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    await update.message.chat.send_action("typing")
    response = await get_response(update.effective_user.id, update.message.text)
    
    if len(response) > 4096:
        for i in range(0, len(response), 4096):
            await update.message.reply_text(response[i:i+4096])
    else:
        await update.message.reply_text(response)

async def clear_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    user_conversations[update.effective_user.id] = []
    await update.message.reply_text("💾 Memory cleared")

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("clear", clear_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
