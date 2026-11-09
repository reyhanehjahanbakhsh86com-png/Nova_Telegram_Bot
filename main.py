import os
import logging
import requests

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

MODEL = "gemini-2.5-flash"

conversations = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! 🤖❤️\n"
        "من Nova هستم، دستیار هوشمند تو.\n"
        "هر سؤالی داری بپرس!"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversations.pop(user_id, None)

    await update.message.reply_text(
        "حافظه مکالمه پاک شد! 🧹"
    )

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    message = update.message.text

    if user_id not in conversations:
        conversations[user_id] = []

    conversations[user_id].append({
        "role": "user",
        "parts": [{"text": message}]
    })

    await update.message.reply_text("⏳ دارم فکر می‌کنم...")

    url = (
        f"https://generativelanguage.googleapis.com/"
        f"v1beta/models/{MODEL}:generateContent"
        f"?key={GEMINI_API_KEY}"
    )

    data = {
        "systemInstruction": {
            "parts": [{
                "text": "تو Nova هستی، یک دستیار هوشمند، "
                        "دوستانه و مفید. به زبان کاربر پاسخ بده."
            }]
        },
        "contents": conversations[user_id][-20:],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048
        }
    }

    try:
        response = requests.post(
            url,
            json=data,
            timeout=60
        )

        result = response.json()

        if response.status_code != 200:
            raise Exception(
                result.get("error", {}).get(
                    "message", "API Error"
                )
            )

        answer = result["candidates"][0]["content"]["parts"][0]["text"]

        conversations[user_id].append({
            "role": "model",
            "parts": [{"text": answer}]
        })

        await update.message.reply_text(answer)

    except Exception as error:
        logging.exception(error)

        conversations[user_id].pop()

        await update.message.reply_text(
            "متأسفم! 😔 فعلاً مشکلی در اتصال هوش مصنوعی پیش اومده."
        )

def main():

    if not BOT_TOKEN or not GEMINI_API_KEY:
        raise ValueError("Missing API keys!")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, chat)
    )

    print("Nova is running!")

    app.run_polling()

if __name__ == "__main__":
    main()
