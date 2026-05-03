import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
application = Application.builder().token(BOT_TOKEN).build()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text(f"Echo: {text}")

application.add_handler(MessageHandler(filters.TEXT, handle_message))

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    import asyncio
    data = request.get_json()
    update = Update.de_json(data, application.bot)
    asyncio.run(application.process_update(update))
    return "ok", 200

@app.route("/")
def index():
    return "Bot is running!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)