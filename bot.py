import os
import threading
from flask import Flask
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()

# --- Choreo Health Check (Port 8080 is recommended) ---
web_app = Flask(__name__)

@web_app.route('/')
def health_check():
    return "YBS Guide Bot is running!", 200

def run_web_server():
    # Choreo အတွက် Port 8080 ကို default ထားပေးပါသည်
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

# --- AICC API Configuration ---
client = OpenAI(
    api_key=os.environ.get("GEMINI_API_KEY"),
    base_url="https://api.aicc.io/v1"
)

def generate_content(user_prompt: str) -> str:
    try:
        # AI ကို အတိအကျဖြေနိုင်ရန် ဦးနှောက် (System Instruction) ထည့်သွင်းခြင်း
        system_instruction = """
        မင်းက ရန်ကုန်မြို့ရဲ့ အကျွမ်းကျင်ဆုံး YBS Bus Guide တစ်ယောက်ပါ။
        User က သွားချင်တဲ့နေရာ ဒါမှမဟုတ် ကားမှတ်တိုင်ကို မေးရင် အောက်ပါအတိုင်း ဖြေပေးပါ -
        
        1. လက်ရှိ ၂၀၂၆ ခုနှစ်ရဲ့ YBS လမ်းကြောင်းတွေကို အင်တာနက်ကနေ အမြဲ Search လုပ်ပြီး Update ဖြစ်တာကိုပဲ ဖြေပါ။
        2. စီးရမယ့် YBS နံပါတ်၊ တက်ရမယ့်မှတ်တိုင် နဲ့ ဆင်းရမယ့်မှတ်တိုင်ကို အတိအကျ ပြပေးပါ။
        3. အကယ်၍ ကားနှစ်ဆင့်စီးရမယ်ဆိုရင် ဘယ်မှတ်တိုင်မှာ ကားပြောင်းစီးရမလဲဆိုတာကို သေချာရှင်းပြပါ။
        4. မှတ်တိုင်တွေရဲ့ Google Maps Link ပါဝင်အောင် ကြိုးစားပေးပါ။
        5. User မေးတာ မသေချာရင် ခန့်မှန်းမဖြေပါနဲ့၊ "လက်ရှိမှာ လမ်းကြောင်းအပြောင်းအလဲ ရှိနိုင်တာမို့ YBMS App မှာ ထပ်စစ်ပေးပါ" လို့ အကြံပြုပါ။
        
        စာသားတွေကို ယဉ်ကျေးပျူငှာစွာနဲ့ မြန်မာလိုပဲ ဖြေကြားပေးပါ။
        """

        response = client.chat.completions.create(
            model="gemini-2.5-flash", 
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"တောင်းပန်ပါတယ်၊ အချက်အလက်ရှာဖွေရာမှာ အမှားအယွင်းရှိသွားလို့ပါ- {str(e)}"

# --- Telegram Bot Logic ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_text = (
        f"မင်္ဂလာပါ {update.effective_user.first_name}!\n"
        "ကျွန်တော်က ရန်ကုန် YBS လမ်းကြောင်းတွေကို ကူညီပေးမယ့် Guide Bot ပါ။\n\n"
        "ဥပမာ - 'သာကေတကနေ Junction City ကို ဘယ်လိုသွားရမလဲ' လို့ မေးမြန်းနိုင်ပါတယ်။"
    )
    await update.message.reply_text(welcome_text)

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    # Typing... status ပြပေးရန်
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    response_text = generate_content(user_message)
    await update.message.reply_text(response_text)

if __name__ == "__main__":
    # 1. Start Flask in background (Port 8080)
    threading.Thread(target=run_web_server, daemon=True).start()

    # 2. Start Telegram Bot
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        print("Error: TELEGRAM_TOKEN variable is missing!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

        print("YBS Bot is starting...")
        app.run_polling()
