import os
import threading
import openai
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()

# --- Choreo Health Check (Port 8000) ---
web_app = Flask(__name__)

@web_app.route('/')
def health_check():
    return "Surprise Bot is Online!", 200

def run_web_server():
   def run_web_server():
    port = int(os.environ.get("PORT", 8080)) # 8000 အစား 8080 ပြောင်းပါ
    web_app.run(host='0.0.0.0', port=port)

# --- AICC API Configuration ---
client = openai.OpenAI(
    api_key=os.environ.get("GEMINI_API_KEY"),
    base_url="https://api.aicc.io/v1"
)

def generate_content(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gemini-1.5-flash",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI Error: {str(e)}"

# --- Telegram Bot Logic ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_name = update.effective_user.first_name
    
    # --- GitHub Pages Link ကို ဒီနေရာမှာ ပြင်ပါ ---
    # ဥပမာ: https://yourname.github.io/your-repo/birthday.html
    url = "https://unhit88.github.io/my-surprise-bot/birthday.html"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❤️ Open Surprise ❤️", web_app=WebAppInfo(url=url))]
    ])
    
    await update.message.reply_text(
        f"Hello {user_name}! surprise လေးတစ်ခု ရှိတယ်။ ❤️\n\nအောက်က ခလုတ်လေးကို နှိပ်ကြည့်။",
        reply_markup=keyboard
    )

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    response_text = generate_content(user_message)
    await update.message.reply_text(response_text)

if __name__ == "__main__":
    # 1. Start Flask in background (Choreo အတွက်)
    threading.Thread(target=run_web_server, daemon=True).start()

    # 2. Start Telegram Bot
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("Surprise Bot is starting...")
    app.run_polling()
