import os
import time
import hmac
import hashlib
import urllib.parse
import json
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY", "").strip()
BINANCE_SECRET_KEY = os.environ.get("BINANCE_SECRET_KEY", "").strip()
ADMIN_ID = 1004439571098
BINANCE_ID = "957483337"
RENDER_URL = os.environ.get("RENDER_URL", "https://pixora-bot-1.onrender.com").strip()
SUPPORT_WHATSAPP = "https://wa.me/213555668244"

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

RAW_PRODUCTS = [
    ("capcut", "🎞️ CapCut", 1.3, "CapCut Pro 30 Days - Delivery is automatic."),
    ("gemini", "💠 Gemini", 3.0, "Gemini AI Pro 18 Months Plan - 5TB Storage."),
    ("office", "🟩 Microsoft Office 365", 0.30, "Office 365 Plus 5 Devices + 1TB OneDrive."),
    ("autodesk", "🔺 Autodesk", 3.0, "Autodesk Admin Dashboard 1 Year Access."),
    ("canva", "🎨 Canva", 4.0, "Canva Edu Pro invite link.")
]

PRODUCTS_INFO = {k: {"name": n, "price": p, "description": d} for k, n, p, d in RAW_PRODUCTS}

STOCK_DATABASE = {k: [] for k in PRODUCTS_INFO}
STOCK_DATABASE["capcut"] = ["CapCut_Key_1: user1@pixoras.com / pass123"]
STOCK_DATABASE["gemini"] = ["https://g.co/gemini/share/sample_link_1"]
STOCK_DATABASE["office"] = ["Office365_Key_1: kc5921@o365pp.com / &$^2^jGq"]
STOCK_DATABASE["autodesk"] = ["Autodesk_Key_ABC123"]
STOCK_DATABASE["canva"] = ["https://www.canva.com/brand/join?inv=sample_1"]

USED_TRANSACTIONS = set()
USER_SELECTED_PRODUCT = {}
ORDERS_FILE = "orders.json"

def safe_delete_message(chat_id, msg_id):
    try:
        bot.delete_message(chat_id, msg_id)
    except Exception:
        pass

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

WELCOME_TEXT = """🔥 <b>أهلاً بك في متجر Pixora Store الرقمي الأول!</b> 🚀

⚡ <i>نوفر لك أقوى الحسابات والاشتراكات الرقمية المدفوعة بأفضل الأسعار وأعلى ضمان رسمي.</i>
💎 <b>التسليم فوري وآلي بالكامل</b> خلال ثوانٍ معدودة بعد إتمام الدفع عبر Binance Pay!

👇 <b>اختر منتجك أدناه، وابدأ تطوير أعمالك أو أدواتك الآن:</b>"""

def get_main_menu_markup():
    markup = InlineKeyboardMarkup(row_width=2)
    btns = []
    for k, info in PRODUCTS_INFO.items():
        if len(STOCK_DATABASE.get(k, [])) == 0:
            btns.append(InlineKeyboardButton(f"❌ {info['name']}", callback_data="sold_out_" + k))
        else:
            btns.append(InlineKeyboardButton(f"🟢 {info['name']} · ${info['price']}", callback_data="buy_" + k))
    markup.add(*btns)
    markup.add(
        InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"),
        InlineKeyboardButton("🛍️ المنتجات", callback_data="main_menu")
    )
    markup.add(
        InlineKeyboardButton("📜 سجل مشترياتي", callback_data="my_orders"),
        InlineKeyboardButton("🪙 Binance Pay", callback_data="show_payments")
    )
    markup.add(
        InlineKeyboardButton("🛠️ الدعم الفني (WhatsApp)", url=SUPPORT_WHATSAPP)
    )
    return markup

app = Flask(__name__)

@app.route('/')
def home():
    return "Pixora Store Auto-Delivery Bot is Live!", 200

@app.route('/' + BOT_TOKEN, methods=['POST'])
def receive_update():
    if request.headers.get('content-type') == 'application/json':
        try:
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
        except Exception as e:
            print("Update error:", e)
        return "!", 200
    return "Unsupported Media Type", 415

def verify_binance_payment(order_id, expected_amount):
    clean_id = str(order_id).strip()
    if clean_id in USED_TRANSACTIONS:
        return False, "رقم العملية هذا تم استخدامه مسبقاً من قبل!"
    
    url = "https://api.binance.com/sapi/v1/pay/transactions"
    qs = urllib.parse.urlencode({"timestamp": int(time.time() * 1000), "limit": 100})
    sig = hmac.new(BINANCE_SECRET_KEY.encode('utf-8'), qs.encode('utf-8'), hashlib.sha256).hexdigest()
    try:
        res = requests.get(f"{url}?{qs}&signature={sig}", headers={"X-MBX-APIKEY": BINANCE_API_KEY}, timeout=10)
        data = res.json()
        print("Binance response:", res.status_code, str(data)[:300])
        if data.get("code") == "000000" and "data" in
