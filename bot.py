import os
import time
import hmac
import hashlib
import urllib.parse
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request

# === إعداداتك الخاصة ===
BOT_TOKEN = "9118344859:AAFqrcRY71z4f3fC87fs91c4z_wDQVHzyfo"
ADMIN_ID = 1004439571098
BINANCE_ID = "957483337"
RENDER_URL = "https://pixora-bot-egyp.onrender.com"

# === مفاتيح باينانس الخاصة بك ===
BINANCE_API_KEY = "d6KILQscYZEbSg4SaOf0YAQ02G8tx6a2IkweYQZZjU8F00hw9YvvivEMuOdppw"
BINANCE_SECRET_KEY = "qSiNFjXEOqAEAo9yG5w62yas7utcmJ3zlnXC5JRL97AfUTHSOqjdFsqQ3DmhjRiw"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

try:
    bot.remove_webhook()
    bot.set_webhook(url=RENDER_URL + "/" + BOT_TOKEN)
except Exception as e:
    print("Webhook error:", e)

# الأسعار والمنتجات بالصيغة النصية النظيفة
PRODUCTS_INFO = {
    "capcut": {"name": "CapCut Pro", "price": 1.5},
    "gemini": {"name": "Gemini Pro", "price": 2.0},
    "office": {"name": "Microsoft 365", "price": 2.0},
    "autodesk": {"name": "AUTODESK", "price": 3.0},
    "canva": {"name": "Canva Pro", "price": 2.0}
}

# المخزون بالكميات والأسعار المطلوبة
STOCK_DATABASE = {
    "capcut": [
        "CapCut_Key_1: user1@pixoras.com / pass123"
    ],
    "gemini": [
        "https://g.co/gemini/share/sample_link_1",
        "https://g.co/gemini/share/sample_link_2"
    ],
    "office": [
        "Office365_Key_1: acc1@pixora.store / P@ss1",
        "Office365_Key_2: acc2@pixora.store / P@ss2"
    ],
    "autodesk": [
        "Autodesk_Key_ABC123"
    ],
    "canva": [
        "https://www.canva.com/brand/join?inv=sample_1"
    ]
}

USED_TRANSACTIONS = set()
USER_SELECTED_PRODUCT = {}

app = Flask('')

@app.route('/')
def home():
    return "Pixora Store Auto-Delivery Bot is Live!"

@app.route('/' + BOT_TOKEN, methods=['POST'])
def receive_update():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

def verify_binance_payment(order_id, expected_amount):
    if order_id in USED_TRANSACTIONS:
        return False, "رقم العملية هذا تم استخدامه مسبقاً!"
    
    url = "https://api.binance.com/sapi/v1/pay/transactions"
    timestamp = int(time.time() * 1000)
    query_string = urllib.parse.urlencode({"timestamp": timestamp, "limit": 50})
    signature = hmac.new(
        BINANCE_SECRET_KEY.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    full_url = f"{url}?{query_string}&signature={signature}"
    headers = {"X-MBX-APIKEY": BINANCE_API_KEY}
    
    try:
        response = requests.get(full_url, headers=headers, timeout=10)
        data = response.json()
        if data.get("code") == "000000" and "data" in data:
            for tx in data["data"]:
                tx_id = str(tx.get("orderId", ""))
                amount = float(tx.get("amount", 0))
                currency = tx.get("currency", "")
                if tx_id == str(order_id).strip() and amount >= expected_amount and currency == "USDT":
                    USED_TRANSACTIONS.add(order_id)
                    return True, "تم التحقق بنجاح"
            return False, "لم يتم العثور على حوالة بهذا الرقم أو أن المبلغ أقل من المطلوب."
        else:
            return False, "تعذر الاتصال ببوابة باينانس، تأكد من مفاتيح الـ API."
    except Exception as e:
        return False, "خطأ في الاتصال: " + str(e)

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    markup = InlineKeyboardMarkup(row_width=2)
    for key, info in PRODUCTS_INFO.items():
        count = len(STOCK_DATABASE[key])
        btn_text = f"{info['name']} · ${info['price']} ({count})"
        markup.add(InlineKeyboardButton(btn_text, callback_data="buy_" + key))
    
    markup.add(InlineKeyboardButton("🪙 Binance Pay (معلومات الدفع)", callback_data="show_payments"))
    welcome_text = "مرحباً بك في متجر *Pixora Store* 🚀\n(التسليم الفوري الآلي عبر Binance Pay).\nاختر منتجك المفضل:"
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id

    if call.data.startswith("buy_"):
        prod_key = call.data.replace("buy_", "")
        if prod_key in PRODUCTS_INFO:
            bot.answer_callback_query(call.id)
            USER_SELECTED_PRODUCT[chat_id] = prod_key
            info = PRODUCTS_INFO[prod_key]
            stock_len = len(STOCK_DATABASE[prod_key])
            
            markup = InlineKeyboardMarkup(row_width=1)
            markup.add(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
            
            msg_text = (
                f"📦 المنتج: *{info['name']}*\n"
                f"💰 السعر المطلوب: *{info['price']} USDT*\n"
                f"📊 الكمية المتوفرة: {stock_len}\n\n"
                f"🪙 **خطوات الدفع والتسليم الفوري:**\n"
                f"1️⃣ حول المبلغ (`{info['price']} USDT`) إلى Binance Pay ID:\n`{BINANCE_ID}`\n\n"
                f"2️⃣ انسخ **رقم العملية (Order ID)** من باينانس وأرسله هنا في الشات، وسيصلك الحساب في نفس الثانية تلقائياً!"
            )
            bot.send_message(chat_id, msg_text, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "show_payments":
        bot.answer_callback_query(call.id)
        pay_text = f"🪙 **معلومات الدفع في متجر Pixora Store:**\n\nBinance Pay ID:\n`{BINANCE_ID}`\n\nاختر منتجك أولاً من القائمة الرئيسية ثم أرسل رقم العملية بعد التحويل لتستلم طلبك فوراً."
        bot.send_message(chat_id, pay_text, parse_mode="Markdown")

    elif call.data == "main_menu":
        bot.answer_callback_query(call.id)
        send_welcome(call.message)

@bot.message_handler(content_types=['text', 'photo', 'document'])
def handle_incoming(message):
    chat_id = message.chat.id
    
    if message.content_type == 'text':
        if message.text.startswith('/'):
            return
        order_id = message.text.strip()
        
        if chat_id not in USER_SELECTED_PRODUCT:
            bot.send_message(chat_id, "⚠️ يرجى اختيار المنتج أولاً من القائمة الرئيسية (/start) قبل إرسال رقم العملية.")
            return
            
        prod_key = USER_SELECTED_PRODUCT[chat_id]
        info = PRODUCTS_INFO[prod_key]
        
        if len(STOCK_DATABASE[prod_key]) == 0:
            bot.send_message(chat_id, "⚠️ عذراً، نفدت كمية هذا المنتج حالياً!")
            return

        wait_msg = bot.send_message(chat_id, "⏳ جاري التحقق من عملية الدفع عبر Binance تلقائياً...")
        is_valid, status_text = verify_binance_payment(order_id, info["price"])
        
        if is_valid:
            item = STOCK_DATABASE[prod_key].pop(0)
            del USER_SELECTED_PRODUCT[chat_id]
            bot.edit_message_text(
                f"🎉 **تم تأكيد الدفع وتسليم طلبك بنجاح!**\n\n"
                f"📦 بيانات حسابك لمنتج *{info['name']}*:\n`{item}`\n\n"
                f"شكراً لثقتك بمتجر *Pixora Store* 💚",
                chat_id,
                wait_msg.message_id,
                parse_mode="Markdown"
            )
        else:
            bot.edit_message_text(f"❌ لم يكتمل التحقق: {status_text}\n\nتأكد من صحة رقم العملية وأن المبلغ مطابق للسعر.", chat_id, wait_msg.message_id)
        return

    bot.send_message(chat_id, "📌 المتجر يعمل بنظام التسليم الآلي عبر Binance Pay. يرجى إرسال **رقم العملية (Order ID)** النصي بعد إتمام التحويل للحصول على طلبك فوراً.")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
