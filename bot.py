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

WELCOME_TEXT = "🔥 أهلاً بك في متجر Pixora Store الرقمي الأول!\n\nاختر منتجك أدناه:"

def get_main_menu_markup():
    markup = InlineKeyboardMarkup()
    products_info = fetch_supplier_products()
    
    if not products_info:
        markup.add(InlineKeyboardButton("⚠️ جارِ تحديث المنتجات...", callback_data="main_menu"))
        return markup

    for k, info in products_info.items():
        if info['stock'] > 0:
            markup.add(InlineKeyboardButton(f"✅ {info['name']} · ${info['price']}", callback_data="buy_" + k))
        else:
            markup.add(InlineKeyboardButton(f"❌ {info['name']} (نفد)", callback_data="sold_out_" + k))

    markup.row(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"), InlineKeyboardButton("📜 مشترياتي", callback_data="my_orders"))
    markup.add(InlineKeyboardButton("🛠️ الدعم الفني", url=SUPPORT_WHATSAPP))
    return markup

if bot:
    @bot.message_handler(commands=['start', 'menu'])
    def send_welcome(message):
        bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=get_main_menu_markup())

    @bot.callback_query_handler(func=lambda call: True)
    def handle_query(call):
        chat_id = call.message.chat.id
        msg_id = call.message.message_id
        data = call.data
        products_info = fetch_supplier_products()

        if data.startswith("buy_"):
            prod_key = data.replace("buy_", "")
            if prod_key in products_info:
                info = products_info[prod_key]
                bot.answer_callback_query(call.id)
                USER_SELECTED_PRODUCT[chat_id] = prod_key
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("🪙 إتمام الدفع الفوري", callback_data="pay_" + prod_key))
                markup.row(InlineKeyboardButton("🔙 رجوع", callback_data="main_menu"))
                
                msg_text = f"🏷️ {info['name']}\n💰 السعر: ${info['price']}\n📦 المخزون: {info['stock']}\n\n{info['description']}"
                safe_delete_message(chat_id, msg_id)
                bot.send_message(chat_id, msg_text, reply_markup=markup)
                
        elif data.startswith("pay_"):
            prod_key = data.replace("pay_", "")
            info = products_info.get(prod_key, {"price": 1.0})
            bot.answer_callback_query(call.id)
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("🔙 رجوع", callback_data="main_menu"))
            pay_msg = f"🪙 تحويل مبلغ (${info['price']} USDT) إلى Binance ID: {BINANCE_ID}\n\nثم أرسل رقم العملية (Order ID) هنا للشات."
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, pay_msg, reply_markup=markup)
            
        elif data == "my_orders":
            bot.answer_callback_query(call.id)
            ords = load_orders().get(str(chat_id), [])
            text = "📜 سجل مشترياتي:\n\n" + ("لا توجد طلبات سابقة." if not ords else "\n".join([o['product'] for o in ords]))
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, text, reply_markup=markup)
            
        elif data == "main_menu":
            bot.answer_callback_query(call.id)
            USER_SELECTED_PRODUCT.pop(chat_id, None)
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, WELCOME_TEXT, reply_markup=get_main_menu_markup())

    @bot.message_handler(content_types=['text', 'photo'])
    def handle_incoming(message):
        chat_id = message.chat.id
        if message.text and message.text.startswith('/'):
            return
        if chat_id not in USER_SELECTED_PRODUCT:
            bot.send_message(chat_id, "⚠️ يرجى اختيار المنتج أولاً من /start")
            return

        prod_key = USER_SELECTED_PRODUCT.pop(chat_id)
        order_id = message.text.strip() if message.text else "إيصال مصور"
        
        bot.send_message(chat_id, "⏳ تم استلام بيانات الدفع، جاري مراجعة الطلب وتسليمك الحساب فوراً.")
        
        admin_text = f"🔔 طلب جديد!\nالمنتج: {prod_key}\nرقم العملية: {order_id}\nمن المستخدم: {chat_id}"
        try:
            bot.send_message(ADMIN_ID, admin_text)
        except Exception:
            pass

app = Flask(__name__)

@app.route('/')
def health_check():
    return "Pixora Store Active!", 200

def keep_alive():
    while True:
        time.sleep(300)
        try:
            url = os.environ.get("RENDER_EXTERNAL_URL")
            if url:
                requests.get(url)
        except Exception:
            pass

if __name__ == '__main__':
    if bot:
        try:
            bot.remove_webhook()
        except Exception:
            pass
    threading.Thread(target=keep_alive, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port, use_reloader=False), daemon=True).start()
    
    if bot:
        while True:
            try:
                bot.infinity_polling(skip_pending=True, timeout=60)
            except Exception as e:
                time.sleep(5)
