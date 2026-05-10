#!/usr/bin/env python3
import os
import logging
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
    key_start = OPENROUTER_KEY[:10] if OPENROUTER_KEY else "NONE"
    await update.message.reply_text(f"🤖 Bot online!\nKey starts with: {key_start}...")

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN:
        return
    
    msg = update.message.text
    await update.message.reply_text(f"You said: {msg}\n\nKey exists: {'✅ Yes' if OPENROUTER_KEY else '❌ No'}")

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    logger.info("Diagnostic bot started")
    await app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    asyncio.run(main())
