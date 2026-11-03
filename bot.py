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
REDOTPAY_ID = "1198898814"
RENDER_URL = "https://pixora-bot-egyp.onrender.com"

# === ضع مفاتيح باينانس التي أنشأتها هنا ===
BINANCE_API_KEY = "d6KILQscYZEbSg4SaOf0YAQ02G8tx6a2IkweYQZZjU8F00hw9YvvivEMuOdppw"
BINANCE_SECRET_KEY = "qSiNFjXEOqAEAo9yG5w62yas7utcmJ3zlnXC5JRL97AfUTHSOqjdFsqQ3DmhjRiw"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

try:
    bot.remove_webhook()
    bot.set_webhook(url=RENDER_URL + "/" + BOT_TOKEN)
except Exception as e:
    print("Webhook error:", e)

PRODUCTS_INFO = {
    "capcut": {"name": "CapCut Pro", "price": 2.0},
    "gemini": {"name": "Gemini Pro", "price": 3.0},
    "office": {"name": "Microsoft 365", "price": 5.0},
    "autodesk": {"name": "AUTODESK", "price": 10.0},
    "canva": {"name": "Canva Pro", "price": 2.0}
}

STOCK_DATABASE = {
    "capcut": ["CapCut_Key_1: user1@pixoras.com / pass123", "CapCut_Key_2: user2@pixoras.com / pass123"],
    "gemini": ["https://g.co/gemini/share/sample_link_1", "https://g.co/gemini/share/sample_link_2"],
    "office": ["Office365_Key_1: acc1@pixora.store / P@ss1", "Office365_Key_2: acc2@pixora.store / P@ss2"],
    "autodesk": ["Autodesk_Key_ABC123", "Autodesk_Key_XYZ789"],
    "canva": ["https://www.canva.com/brand/join?inv=sample_1", "https://www.canva.com/brand/join?inv=sample_2"]
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
    
    markup.add(InlineKeyboardButton("طرق الدفع (Binance / RedotPay)", callback_data="show_payments"))
    welcome_text = "مرحباً بك في متجر *Pixora Store* (التسليم الفوري الآلي).\nاختر منتجك المفضل:"
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: not call.data.startswith(("Approve_", "Reject_")))
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
            markup.add(InlineKeyboardButton("القائمة الرئيسية", callback_data="main_menu"))
            
            msg_text = (
                f"المنتج: *{info['name']}*\n"
                f"السعر المطلوب: *{info['price']} USDT*\n"
                f"الكمية المتوفرة: {stock_len}\n\n"
                f"*خيار 1: الدفع والتسليم الفوري التلقائي (Binance Pay)*\n"
                f"حول *{info['price']} USDT* إلى المعرف: `{BINANCE_ID}`\n"
                f"ثم أرسل *رقم العملية (Order ID)* هنا في الشات وسيصلك الحساب في نفس الثانية!\n\n"
                f"*خيار 2: الدفع عبر RedotPay*\n"
                f"حول المبلغ إلى المعرف: `{REDOTPAY_ID}` ثم أرسل *صورة الإيصال* هنا."
            )
            bot.send_message(chat_id, msg_text, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "show_payments":
        bot.answer_callback_query(call.id)
        pay_text = "طرق الدفع المتاحة:\n\n*Binance Pay ID:*\n`" + BINANCE_ID + "`\n\n*RedotPay ID:*\n`" + REDOTPAY_ID + "`\n\nاختر المنتج أولاً من القائمة الرئيسية لتفعيل التسليم التلقائي."
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
            bot.send_message(chat_id, "يرجى اختيار المنتج أولاً من القائمة (/start) قبل إرسال رقم عملية الدفع.")
            return
            
        prod_key = USER_SELECTED_PRODUCT[chat_id]
        info = PRODUCTS_INFO[prod_key]
        
        if len(STOCK_DATABASE[prod_key]) == 0:
            bot.send_message(chat_id, "عذراً، نفدت كمية هذا المنتج حالياً! تواصل مع الإدارة.")
            return

        wait_msg = bot.send_message(chat_id, "جاري التحقق من عملية الدفع عبر Binance تلقائياً...")
        is_valid, status_text = verify_binance_payment(order_id, info["price"])
        
        if is_valid:
            item = STOCK_DATABASE[prod_key].pop(0)
            del USER_SELECTED_PRODUCT[chat_id]
            bot.edit_message_text(
                f"تم تأكيد الدفع آلياً بنجاح!\n\nبيانات حسابك لمنتج *{info['name']}*:\n`{item}`\n\nشكراً لثقتك بمتجر *Pixora Store*",
                chat_id,
                wait_msg.message_id,
                parse_mode="Markdown"
            )
        else:
            bot.edit_message_text("لم يكتمل التحقق الآلي: " + status_text + "\n\nإذا كنت تدفع عبر RedotPay أرسل صورة الإيصال كصورة.", chat_id, wait_msg.message_id)
        return

    user_name = message.from_user.first_name or "عميل"
    markup = InlineKeyboardMarkup(row_width=2)
    for key, info in PRODUCTS_INFO.items():
        markup.add(InlineKeyboardButton("موافقة " + info["name"], callback_data=f"Approve_{key}_{chat_id}"))
    markup.add(InlineKeyboardButton("رفض الإيصال", callback_data=f"Reject_{chat_id}"))

    try:
        bot.forward_message(ADMIN_ID, chat_id, message.message_id)
        bot.send_message(ADMIN_ID, f"إيصال جديد من: {user_name}\nID: `{chat_id}`", reply_markup=markup, parse_mode="Markdown")
        bot.send_message(chat_id, "تم استلام صورة الإيصال بنجاح! سيتم إرسال طلبك فور المراجعة.")
    except Exception as e:
        bot.send_message(chat_id, "تم استلام الصورة، ولكن حدث خطأ في توجيهها للمدير: " + str(e))

@bot.callback_query_handler(func=lambda call: call.data.startswith(("Approve_", "Reject_")))
def admin_action(call):
    bot.answer_callback_query(call.id)
    parts = call.data.split("_")
    if parts[0] == "Reject":
        bot.send_message(parts[1], "عذراً، لم يتم تأكيد إيصال الدفع. يرجى مراجعة الإدارة.")
        bot.edit_message_text("تم رفض الإيصال.", call.message.chat.id, call.message.message_id)
    elif parts[0] == "Approve":
        prod_key, target_id = parts[1], parts[2]
        if len(STOCK_DATABASE[prod_key]) > 0:
            item = STOCK_DATABASE[prod_key].pop(0)
            bot.send_message(target_id, f"تم تأكيد الدفع بنجاح!\n\nبيانات طلبك:\n`{item}`", parse_mode="Markdown")
            bot.edit_message_text("تمت الموافقة وتسليم المنتج: " + item, call.message.chat.id, call.message.message_id)
        else:
            bot.send_message(call.message.chat.id, "تنبيه: المخزون فارغ لهذا المنتج!")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
