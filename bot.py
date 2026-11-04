import os
import time
import json
import threading
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request
from products import PRODUCTS_INFO, STOCK_DATABASE

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_ID = 1004439571098
BINANCE_ID = "957483337"
RENDER_URL = os.environ.get("RENDER_URL", "").strip()
SUPPORT_WHATSAPP = "https://wa.me/213555668244"

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
app = Flask(__name__)

USER_SELECTED_PRODUCT = {}
PENDING_ORDERS = {}
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
        print("Save error:", e)

WELCOME_TEXT = "🔥 <b>أهلاً بك في متجر Pixora Store الرقمي!</b> 🚀\n\n👇 <b>اختر منتجك من القائمة أدناه:</b>"

def get_main_menu_markup():
    markup = InlineKeyboardMarkup(row_width=2)
    btns = []
    for k, info in PRODUCTS_INFO.items():
        if len(STOCK_DATABASE.get(k, [])) == 0:
            btns.append(InlineKeyboardButton(f"❌ {info['name']}", callback_data=f"sold_out_{k}"))
        else:
            btns.append(InlineKeyboardButton(f"🟢 {info['name']} · ${info['price']}", callback_data=f"buy_{k}"))
    markup.add(*btns)
    markup.add(
        InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"),
        InlineKeyboardButton("🛍️ المنتجات", callback_data="main_menu")
    )
    markup.add(
        InlineKeyboardButton("📜 سجل مشترياتي", callback_data="my_orders"),
        InlineKeyboardButton("🪙 Binance Pay", callback_data="show_payments")
    )
    markup.add(InlineKeyboardButton("🛠️ الدعم الفني", url=SUPPORT_WHATSAPP))
    return markup

@app.route('/')
def home():
    return "Bot is Live!", 200

@app.route('/' + BOT_TOKEN, methods=['POST'])
def receive_update():
    if request.headers.get('content-type') == 'application/json':
        try:
            json_str = request.get_data().decode('utf-8')
            bot.process_new_updates([telebot.types.Update.de_json(json_str)])
        except Exception as e:
            print("Update error:", e)
        return "!", 200
    return "Unsupported", 415

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=get_main_menu_markup(), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    data = call.data

    if data.startswith("admin_approve_"):
        token = data.replace("admin_approve_", "")
        if token in PENDING_ORDERS:
            o = PENDING_ORDERS.pop(token)
            u_id, p_key = o["chat_id"], o["prod_key"]
            p_name = PRODUCTS_INFO[p_key]["name"]
            if len(STOCK_DATABASE.get(p_key, [])) > 0:
                item = STOCK_DATABASE[p_key].pop(0)
                ords = load_orders()
                ords.setdefault(str(u_id), []).append({
                    "product": p_name,
                    "item": item,
                    "order_id": o["order_id"],
                    "time": time.strftime("%Y-%m-%d %H:%M:%S")
                })
                save_orders(ords)
                msg = f"🎉 <b>تم تأكيد الدفع بنجاح!</b>\n\n📦 بيانات {p_name}:\n<code>{item}</code>\n\nشكراً لتعاملك مع Pixora Store 💚"
                bot.send_message(u_id, msg, parse_mode="HTML")
                bot.edit_message_text(f"✅ تم تسليم {p_name} للعميل.", chat_id, msg_id)
            else:
                bot.send_message(u_id, "⚠️ نفد المخزون، تواصل مع الدعم الفني.")
                bot.edit_message_text("⚠️ المخزون فارغ!", chat_id, msg_id)
        return

    elif data.startswith("admin_reject_"):
        token = data.replace("admin_reject_", "")
        if token in
