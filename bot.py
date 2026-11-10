import os
import time
import json
import threading
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.environ.get("ADMIN_ID", "1004439571")) 
BINANCE_ID = "957483337"
SUPPORT_WHATSAPP = "https://wa.me/213555668244"

RESELLER_KEY = os.environ.get("RESELLER_KEY", "").strip()
VENTEBOT_API_URL = "https://web-production-1c7b1.up.railway.app/api/reseller"

if not BOT_TOKEN:
    print("⚠️ تحذير: BOT_TOKEN غير موجود، يرجى تأكيده في متغيرات البيئة بـ Render.")

bot = telebot.TeleBot(BOT_TOKEN, threaded=False) if BOT_TOKEN else None

USER_SELECTED_PRODUCT = {}
PENDING_ORDERS = {}
ORDERS_FILE = "orders.json"

def safe_delete_message(chat_id, msg_id):
    try:
        if bot:
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

def fetch_supplier_products():
    if not RESELLER_KEY:
        return {}
    headers = {"X-Reseller-Key": RESELLER_KEY}
    try:
        response = requests.get(f"{VENTEBOT_API_URL}/products", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            products_map = {}
            items = data.get("products", data) if isinstance(data, dict) else data
            for item in items:
                p_id = str(item.get("id", item.get("code", "unknown")))
                p_name = item.get("name", "منتج رقمي")
                raw_price = float(item.get("price", 1.0))
                p_price = round(raw_price * 1.20, 2)
                p_stock = item.get("stock", item.get("quantity", 10))
                p_desc = item.get("description", "اشتراك رقمي رسمي مع ضمان كامل.")
                
                products_map[p_id] = {
                    "name": p_name,
                    "price": p_price,
                    "stock": p_stock,
                    "description": p_desc
                }
            return products_map
    except Exception as e:
        print("Error fetching supplier products:", e)
    return {}

WELCOME_TEXT = (
    "🔥 **أهلاً بك في متجر Pixora Store الرقمي الأول!** 🚀\n\n"
    "⚡ *نوفر لك أقوى الحسابات والاشتراكات الرقمية المدفوعة بأفضل الأسعار وأعلى ضمان رسمي.*\n"
    "💎 **التسليم فوري** بعد إتمام الدفع عبر Binance Pay!\n\n"
    "👇 **اختر منتجك أدناه، وابدأ تطوير أعمالك أو أدواتك الآن:**"
)

def get_main_menu_markup():
    markup = InlineKeyboardMarkup()
    products_info = fetch_supplier_products()
    
    if not products_info:
        markup.add(InlineKeyboardButton("⚠️ جارِ تحديث المنتجات من المزود...", callback_data="main_menu"))
        return markup

    in_stock_btns = []
    for k, info in products_info.items():
        clean_name = info['name'].replace("🔴", "").replace("🟢", "").replace("🎞️", "").replace("💠", "").strip()
        if info['stock'] > 0:
            in_stock_btns.append(InlineKeyboardButton(f"✅ {clean_name} · ${info['price']}", callback_data="buy_" + k))
        else:
            in_stock_btns.append(InlineKeyboardButton(f"❌ {clean_name} (نفد)", callback_data="sold_out_" + k))
    
    for i in range(0, len(in_stock_btns), 2):
        if i + 1 < len(in_stock_btns):
            markup.row(in_stock_btns[i], in_stock_btns[i+1])
        else:
            markup.row(in_stock_btns[i])

    markup.row(
        InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"),
        InlineKeyboardButton("📜 سجل مشترياتي", callback_data="my_orders")
    )
    markup.row(
        InlineKeyboardButton("🪙 Binance Pay", callback_data="show_payments"),
        InlineKeyboardButton("🛠️ الدعم الفني", url=SUPPORT_WHATSAPP)
    )
    return markup

if bot:
    @bot.message_handler(commands=['start', 'menu'])
    def send_welcome(message):
        bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=get_main_menu_markup(), parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda call: True)
    def handle_query(call):
        chat_id = call.message.chat.id
        msg_id = call.message.message_id
        data = call.data
        
        products_info = fetch_supplier_products()

        if data.startswith("admin_approve_"):
            token = data.replace("admin_approve_", "")
            if token in PENDING_ORDERS:
                o = PENDING_ORDERS.pop(token)
                u_id, p_key = o["chat_id"], o["prod_key"]
                p_info = products_info.get(p_key, {"name": "منتج رقمي", "price": 1.0})
                p_name = p_info["name"]
                
                item_data = "بيانات الحساب المسلمة من الموزع الآلي - تم التحقق بنجاح"
                
                ords = load_orders()
                ords.setdefault(str(u_id), []).append
