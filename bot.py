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

# 1. التحقق من الرصيد ومعلومات الحساب لدى المزود
def api_get_my_wallet():
    if not RESELLER_KEY:
        return None
    try:
        res = requests.get(f"{VENTEBOT_API_URL}/me", headers={"X-Reseller-Key": RESELLER_KEY}, timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None

# 2. الاستعلام عن تفاصيل طلب معين بالمزود
def api_get_order_details(order_id):
    if not RESELLER_KEY:
        return None
    try:
        res = requests.get(f"{VENTEBOT_API_URL}/orders/{order_id}", headers={"X-Reseller-Key": RESELLER_KEY}, timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None

# 3. سجل المعاملات المالية
def api_get_wallet_transactions():
    if not RESELLER_KEY:
        return None
    try:
        res = requests.get(f"{VENTEBOT_API_URL}/wallet/transactions", headers={"X-Reseller-Key": RESELLER_KEY}, timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None

# 4. طرق الإيداع المتاحة
def api_get_deposit_methods():
    if not RESELLER_KEY:
        return None
    try:
        res = requests.get(f"{VENTEBOT_API_URL}/wallet/deposit-methods", headers={"X-Reseller-Key": RESELLER_KEY}, timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None

# شراء الطلب أوتوماتيكياً
def purchase_order_from_supplier(product_id, reference_id):
    if not RESELLER_KEY:
        return {"success": False, "error": "No reseller key"}
    
    headers = {"X-Reseller-Key": RESELLER_KEY, "Content-Type": "application/json"}
    payload = {"product_id": product_id, "reference": reference_id}
    try:
        response = requests.post(f"{VENTEBOT_API_URL}/orders", json=payload, headers=headers, timeout=15)
        if response.status_code in [200, 201]:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}

WELCOME_TEXT = "🔥 أهلاً بك في متجر Pixora Store الرقمي الأول!\n\nاختر منتجك أدناه:"

def get_main_menu_markup(is_admin=False):
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
    if is_admin:
        markup.row(InlineKeyboardButton("🛠️ لوحة تحكم الإدارة", callback_data="admin_panel"))
    markup.add(InlineKeyboardButton("🛠️ الدعم الفني", url=SUPPORT_WHATSAPP))
    return markup

def get_admin_markup():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("💰 فحص الرصيد بالمحفظة", callback_data="adm_balance"), InlineKeyboardButton("💳 طرق الإيداع", callback_data="adm_deposits"))
    markup.row(InlineKeyboardButton("📊 سجل المعاملات المالية", callback_data="adm_transactions"))
    markup.row(InlineKeyboardButton("🔙 عودة للقائمة الرئيسية", callback_data="main_menu"))
    return markup

if bot:
    @bot.message_handler(commands=['start', 'menu'])
    def send_welcome(message):
        is_admin = (message.chat.id == ADMIN_ID)
        bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=get_main_menu_markup(is_admin))

    @bot.callback_query_handler(func=lambda call: True)
    def handle_query(call):
        chat_id = call.message.chat.id
        msg_id = call.message.message_id
        data = call.data
        is_admin = (chat_id == ADMIN_ID)
        products_info = fetch_supplier_products()

        if data == "admin_panel" and is_admin:
            bot.answer_callback_query(call.id)
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, "🛠️ <b>لوحة تحكم الإدارة المتقدمة:</b>\nاختر العملية المطلوبة:", reply_markup=get_admin_markup(), parse_mode="HTML")

        elif data == "adm_balance" and is_admin:
            bot.answer_callback_query(call.id)
            wallet = api_get_my_wallet()
            text = f"💰 <b>بيانات المحفظة لدى المزود:</b>\n<pre>{json.dumps(wallet, indent=2, ensure_ascii=False)}</pre>" if wallet else "❌ تعذر جلب بيانات الرصيد."
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔙 رجوع لوحة التحكم", callback_data="admin_panel"))
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

        elif data == "adm_deposits" and is_admin:
            bot.answer_callback_query(call.id)
            dep = api_get_deposit_methods()
            text = f"💳 <b>طرق وأدنى حدود الإيداع:</b>\n<pre>{json.dumps(dep, indent=2, ensure_ascii=False)}</pre>" if dep else "❌ تعذر جلب طرق الإيداع."
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔙 رجوع لوحة التحكم", callback_data="admin_panel"))
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

        elif data == "adm_transactions" and is_admin:
            bot.answer_callback_query(call.id)
            txs = api_get_wallet_transactions()
            text = f"📊 <b>سجل المعاملات المالية:</b>\n<pre>{json.dumps(txs, indent=2, ensure_ascii=False)[:3500]}</pre>" if txs else "❌ تعذر جلب سجل المعاملات."
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔙 رجوع لوحة التحكم", callback_data="admin_panel"))
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

        elif data.startswith("buy_"):
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
            pay_msg = f"🪙 تحويل مبلغ (${info['price']} USDT) إلى Binance ID: {BINANCE_ID}\n\nثم أرسل رقم العملية (Order ID) أو إيصال الدفع هنا للشات ليتم التسليم الفوري أوتوماتيكياً."
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, pay_msg, reply_markup=markup)
            
        elif data == "my_orders":
            bot.answer_callback_query(call.id)
            ords = load_orders().get(str(chat_id), [])
            if not ords:
                text = "📜 سجل مشترياتي:\n\nلا توجد طلبات سابقة."
            else:
                text = "📜 سجل مشترياتي السابقة:\n\n"
                for o in ords:
                    text += f"📦 {o['product']}\n🔑 البيان: <code>{o['item']}</code>\n------------------\n"
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
            
        elif data == "main_menu":
            bot.answer_callback_query(call.id)
            USER_SELECTED_PRODUCT.pop(chat_id, None)
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, WELCOME_TEXT, reply_markup=get_main_menu_markup(is_admin))

    @bot.message_handler(content_types=['text', 'photo'])
    def handle_incoming(message):
        chat_id = message.chat.id
        if message.text and
