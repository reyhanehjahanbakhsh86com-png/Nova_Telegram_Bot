import os import logging import asyncio import requests
from telegram import Update from telegram.ext import ( Application, CommandHandler, MessageHandler, ContextTypes, filters )
logging.basicConfig( format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO )
BOT_TOKEN = os.getenv("BOT_TOKEN") GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-2.5-flash"
conversations = {}
SYSTEM_PROMPT = """ تو Nova هستی؛ یک دستیار هوشمند، حرفه‌ای و دوستانه. زبان اصلی تو فارسی است. از تمام زبان‌های دیگر نیز پشتیبانی کن. طبیعی، دقیق، صمیمی و شبیه یک دستیار حرفه‌ای صحبت کن. اگر کاربر فارسی صحبت کرد، فارسی جواب بده. در محاسبات دقت کن و اگر اطلاعات کافی نداری سؤال بپرس. """
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text( "سلام رفیق! ❤️🤖\n\n" "من Nova هستم؛ دستیار هوشمند تو.\n" "می‌تونی فارسی یا به هر زبان دیگه‌ای باهام صحبت کنی.\n\n" "هر سؤالی داری بپرس!" )
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.effective_user.id conversations.pop(user_id, None)
await update.message.reply_text(
    "حافظه مکالمه پاک شد! 🧹"
)
def ask_gemini(history): url = ( f"https://generativelanguage.googleapis.com/" f"v1beta/models/{MODEL}:generateContent" )
headers = {
    "Content-Type": "application/json",
    "x-goog-api-key": GEMINI_API_KEY
}

data = {
    "systemInstruction": {
        "parts": [{"text": SYSTEM_PROMPT}]
    },
    "contents": history[-20:],
    "generationConfig": {
        "temperature": 0.7,
        "maxOutputTokens": 2048
    }
}

response = requests.post(
    url,
    headers=headers,
    json=data,
    timeout=60
)

response.raise_for_status()

result = response.json()

candidates = result.get("candidates", [])

if not candidates:
    raise ValueError("Gemini returned no response")

parts = candidates[0].get("content", {}).get("parts", [])

answer = "".join(
    part.get("text", "")
    for part in parts
).strip()

if not answer:
    raise ValueError("Empty Gemini response")

return answer
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = update.effective_user.id
message = update.message.text

history = conversations.setdefault(user_id, [])

history.append({
    "role": "user",
    "parts": [{"text": message}]
})

status = await update.message.reply_text(
    "⏳ دارم فکر می‌کنم..."
)

try:
    answer = await asyncio.to_thread(
        ask_gemini,
        history
    )

    history.append({
        "role": "model",
        "parts": [{"text": answer}]
    })

    if len(history) > 20:
        del history[:-20]

    for i in range(0, len(answer), 4000):
        await update.message.reply_text(
            answer[i:i + 4000]
        )

    await status.delete()

except Exception:
    logging.exception("Gemini request failed")

    if history and history[-1]["role"] == "user":
        history.pop()

    await status.edit_text(
        "متأسفم رفیق! 😔\n"
        "در اتصال به هوش مصنوعی مشکلی پیش اومده.\n"
        "لطفاً چند لحظه دیگه امتحان کن."
    )
def main():
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing!")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing!")

app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("reset", reset))

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        chat
    )
)

logging.info("Nova is running!")

app.run_polling()
if name == "main": main()
