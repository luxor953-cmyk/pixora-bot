import os
import time
import json
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.environ.get("ADMIN_ID", "1004439571")) 
BINANCE_ID = "957483337"
SUPPORT_WHATSAPP = "https://wa.me/213555668244"

if not BOT_TOKEN or ":" not in BOT_TOKEN:
    raise ValueError("⚠️ خطأ: متغير البيئة BOT_TOKEN غير موجود أو غير مدخل في لوحة تحكم Render!")

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

RAW_PRODUCTS = [
    ("capcut", "🎞️ CapCut Pro 1 Month FW", 1.47, "Full 30 days private Pro Team account."),
    ("gemini", "💠 Gemini Ai · Gemini Pro 18 Months Link", 3.0, "18 Months Plan - 100% Private."),
    ("office", "📱 Microsoft 365 1Tb 5 Devices Lifetime", 1.0, "Microsoft Office apps full access."),
    ("autodesk", "🔺 Autodesk all Apps 1 Year", 0.60, "1 year subscription to Autodesk Student."),
    ("canva", "🎨 Canva Education Panel", 4.0, "Canva Education Panel setup guide.")
]

PRODUCTS_INFO = {k: {"name": n, "price": p, "description": d} for k, n, p, d in RAW_PRODUCTS}
STOCK_DATABASE = {k: [] for k in PRODUCTS_INFO}
STOCK_DATABASE["capcut"] = ["CapCut_Key_1: user1@pixoras.com / pass123"]
STOCK_DATABASE["gemini"] = ["https://g.co/gemini/share/sample_link_1"]

USER_SELECTED_PRODUCT = {}
PENDING_ORDERS = {}
ORDERS_FILE = "orders.json"

def load_orders():
    if os.path.exists(ORDERS_FILE):
        try:
            with open(ORDERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_orders(orders_data):
    try:
        with open(ORDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(orders_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Error saving orders:", e)

WELCOME_TEXT = "🔥 **أهلاً بك في متجر Pixora Store الرقمي!** 🚀\n\nاختر منتجك أدناه:"

def get_main_menu_markup():
    markup = InlineKeyboardMarkup()
    for k, info in PRODUCTS_INFO.items():
        if len(STOCK_DATABASE.get(k, [])) > 0:
            markup.add(InlineKeyboardButton(f"🟢 {info['name']} · ${info['price']}", callback_data="buy_" + k))
        else:
            markup.add(InlineKeyboardButton(f"❌ {info['name']}", callback_data="sold_out_" + k))
    markup.add(InlineKeyboardButton("🛠️ الدعم الفني", url=SUPPORT_WHATSAPP))
    return markup

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=get_main_menu_markup(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    data = call.data
    if data.startswith("buy_"):
        prod_key = data.replace("buy_", "")
        if prod_key in PRODUCTS_INFO:
            bot.answer_callback_query(call.id)
            info = PRODUCTS_INFO[prod_key]
            bot.send_message(chat_id, f"🏷️ **{info['name']}**\n💰 السعر: `${info['price']}`")

if __name__ == '__main__':
    try:
        bot.remove_webhook()
        time.sleep(1)
    except Exception:
        pass
    
    print("🤖 Bot is running...")
    bot.infinity_polling(skip_pending=True)
