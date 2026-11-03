import os
import time
import hmac
import hashlib
import urllib.parse
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request

# === الإعدادات (المفاتيح تُقرأ من Environment Variables في Render) ===
BOT_TOKEN = os.environ["BOT_TOKEN"]
BINANCE_API_KEY = os.environ["BINANCE_API_KEY"]
BINANCE_SECRET_KEY = os.environ["BINANCE_SECRET_KEY"]

ADMIN_ID = 1004439571098
BINANCE_ID = "957483337"
RENDER_URL = "https://pixora-bot-egyp.onrender.com"
SUPPORT_WHATSAPP = "https://wa.me/213555668244"  # رقم الواتساب المباشر للدعم الفني

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

try:
    bot.remove_webhook()
    bot.set_webhook(url=RENDER_URL + "/" + BOT_TOKEN)
except Exception as e:
    print("Webhook error:", e)

# جميع المنتجات مع أسمائها، أسرارها، وأوصافها التفصيلية
PRODUCTS_INFO = {
    "capcut": {
        "name": "🎞️ CapCut", 
        "price": 2.0,
        "description": "- Full 30 days private Pro Team account .\n- Maximum 2 devices , with full warranty .\n- Stable Account full 30 days (no 7days renew ).\n- Login to mobile App first next to laptop (desktop App no web) via QR code ."
    },
    "gemini": {
        "name": "💠 Gemini", 
        "price": 2.0,
        "description": "- Full access to Gemini Advanced & Pro features.\n- Direct official invite or shared private account.\n- Fast response and full warranty for the duration."
    },
    "office": {
        "name": "🟩 Microsoft 365", 
        "price": 2.0,
        "description": "- Official Microsoft 365 account (5 PCs/Macs + 5 Tablets + 5 Phones).\n- 1TB OneDrive Cloud storage included.\n- Full warranty and multi-device support."
    },
    "autodesk": {
        "name": "🔺 Autodesk", 
        "price": 3.0,
        "description": "- Official Autodesk Educational/Pro access.\n- Access to AutoCAD, Revit, Maya, and more.\n- Full warranty and stable subscription."
    },
    "canva": {
        "name": "🎨 Canva", 
        "price": 2.0,
        "description": "- Canva Pro Team Invitation.\n- Unlock all premium templates, fonts, and background remover.\n- Private account safety with full warranty."
    },

    "adobe": {"name": "🔴 Adobe", "price": 2.5, "description": "- Full Adobe Creative Cloud access.\n- Full warranty and stability."},
    "avira": {"name": "🔴 Avira", "price": 2.0, "description": "- Premium Antivirus & Security subscription.\n- Full warranty."},
    "chatgpt": {"name": "🔴 ChatGPT", "price": 3.0, "description": "- ChatGPT Plus account access.\n- Fast GPT-4o and DALL-E generation."},
    "coursera": {"name": "🔴 Coursera", "price": 2.0, "description": "- Coursera subscription for professional certificates."},
    "duolingo": {"name": "🔴 Duolingo", "price": 0.75, "description": "- Duolingo Super 12 Months subscription."},
    "elevenlabs": {"name": "🔴 ElevenLabs", "price": 3.5, "description": "- AI Voice Generator premium plan."},
    "expressvpn": {"name": "🔴 ExpressVPN", "price": 2.5, "description": "- High-speed secure VPN subscription."},
    "figma": {"name": "🔴 Figma", "price": 2.0, "description": "- Figma Pro team access for designers."},
    "framer": {"name": "🔴 Framer", "price": 2.0, "description": "- Framer Pro web building subscription."},
    "gamma": {"name": "🔴 Gamma", "price": 2.0, "description": "- AI presentations and docs generator."},
    "grok": {"name": "🔴 Grok", "price": 2.5, "description": "- xAI Grok premium access."},
    "hmavpn": {"name": "🔴 HMA VPN", "price": 0.55, "description": "- HideMyAss VPN secure access."},
    "jetbrain": {"name": "🔴 JetBrain", "price": 3.0, "description": "- All Products Pack license access."},
    "kaspersky": {"name": "🔴 Kaspersky", "price": 2.0, "description": "- Kaspersky Total Security license."},
    "linkedin": {"name": "🔴 LinkedIn", "price": 3.0, "description": "- LinkedIn Premium Career/Business access."},
    "lovable": {"name": "🔴 Lovable", "price": 2.5, "description": "- Full stack AI web app builder."},
    "muse": {"name": "🔴 Muse", "price": 2.0, "description": "- Muse AI premium tools access."},
    "notion": {"name": "🔴 Notion", "price": 2.0, "description": "- Notion Pro workspace subscription."},
    "youtube": {"name": "🔴 YouTube", "price": 2.0, "description": "- YouTube Premium ad-free subscription."},
    "ilovepdf": {"name": "🔴 iLovePdf", "price": 1.5, "description": "- iLovePDF Premium tools access."},
    "api": {"name": "🔴 API", "price": 5.0, "description": "- High limit developer API keys."},
    "grammarly": {"name": "🔴 Grammarly", "price": 2.0, "description": "- Grammarly Premium writing assistant."},
    "nordvpn": {"name": "🔴 Nord Vpn", "price": 2.0, "description": "- NordVPN secure high-speed servers."},
    "scribd": {"name": "🔴 Scribd", "price": 2.0, "description": "- Scribd ebooks and audiobooks access."},
    "wispr": {"name": "🔴 Wispr", "price": 2.0, "description": "- Wispr Flow voice dictation tool."},
    "udemy": {"name": "🔴 Udemy", "price": 2.0, "description": "- Premium courses access plan."}
}

# قاعدة بيانات المخزون
STOCK_DATABASE = {
    "capcut": ["CapCut_Key_1: user1@pixoras.com / pass123"],
    "gemini": ["https://g.co/gemini/share/sample_link_1", "https://g.co/gemini/share/sample_link_2"],
    "office": ["Office365_Key_1: kc5921@o365pp.com  / &$^2^jGq"],
    "autodesk": ["Autodesk_Key_ABC123"],
    "canva": ["https://www.canva.com/brand/join?inv=sample_1"],

    "adobe": [], "avira": [], "chatgpt": [], "coursera": [], "duolingo": [],
    "elevenlabs": [], "expressvpn": [], "figma": [], "framer": [], "gamma": [],
    "grok": [], "hmavpn": [], "jetbrain": [], "kaspersky": [], "linkedin": [],
    "lovable": [], "muse": [], "notion": [], "youtube": [], "ilovepdf": [],
    "api": [], "grammarly": [], "nordvpn": [], "scribd": [], "wispr": [], "udemy": []
}

USED_TRANSACTIONS = set()
USER_SELECTED_PRODUCT = {}

# === شعارات المنتجات ===
LOGO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logos")
LOGO_CACHE = {} 

def send_product_card(chat_id, prod_key, caption, markup):
    path = os.path.join(LOGO_DIR, prod_key + ".png")
    try:
        if prod_key in LOGO_CACHE:
            bot.send_photo(chat_id, LOGO_CACHE[prod_key], caption=caption,
                           reply_markup=markup, parse_mode="Markdown")
            return
        if os.path.exists(path):
            with open(path, "rb") as f:
                msg = bot.send_photo(chat_id, f, caption=caption,
                                     reply_markup=markup, parse_mode="Markdown")
            LOGO_CACHE[prod_key] = msg.photo[-1].file_id
            return
    except Exception as e:
        print("Logo error:", e)
    bot.send_message(chat_id, caption, reply_markup=markup, parse_mode="Markdown")

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
    query_string = urllib.parse.urlencode({"timestamp": timestamp, "limit": 100})
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
                prepay_id = str(tx.get("prepayId", ""))
                amount = float(tx.get("amount", 0))
                currency = tx.get("currency", "")
                if (tx_id == str(order_id).strip() or prepay_id == str(order_id).strip()) and amount >= expected_amount and currency == "USDT":
                    USED_TRANSACTIONS.add(order_id)
                    return True, "تم التحقق بنجاح"
            return False, "لم يتم العثور على حوالة بهذا الرقم أو أن المبلغ أقل من المطلوب."
        else:
            return False, "تعذر الاتصال ببوابة باينانس، تأكد من مفاتيح الـ API."
    except Exception as e:
        return False, "خطأ في الاتصال: " + str(e)

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    markup = InlineKeyboardMarkup(row_width=3)
    buttons = []

    for key, info in PRODUCTS_INFO.items():
        count = len(STOCK_DATABASE.get(key, []))

        if count == 0:
            btn_text = f"{info['name']}"
            buttons.append(InlineKeyboardButton(btn_text, callback_data="sold_out_" + key))
        else:
            btn_text = f"🟢 {info['name']} · ${info['price']}"
            buttons.append(InlineKeyboardButton(btn_text, callback_data="buy_" + key))

    markup.add(*buttons)
    
    # صف أزرار التحكم والخدمات الإضافية أسفل القائمة
    markup.add(
        InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"),
        InlineKeyboardButton("🛍️ المنتجات", callback_data="main_menu")
    )
    markup.add(
        InlineKeyboardButton("🪙 Binance Pay", callback_data="show_payments"),
        InlineKeyboardButton("🛠️ الدعم الفني (WhatsApp)", url=SUPPORT_WHATSAPP)
    )

    # رسالة الترحيب القوية التي تحفز الزبون على الاشتراك والشراء الفوري
    welcome_text = (
        "🔥 **أهلاً بك في متجر Pixora Store الرقمي الأول!** 🚀\n\n"
        "⚡ *نوفر لك أقوى الحسابات والاشتراكات الرقمية المدفوعة بأفضل الأسعار وأعلى ضمان رسمي.*\n"
        "💎 **التسليم فوري وآلي بالكامل** خلال ثوانٍ معدودة بعد إتمام الدفع عبر Binance Pay!\n\n"
        "👇 **اختر منتجك أدناه، وابدأ تطوير أعمالك أو أدواتك الآن:**"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id

    if call.data.startswith("sold_out_"):
        bot.answer_callback_query(call.id, "❌ عذراً، هذا المنتج غير متوفر في المخزن حالياً!", show_alert=True)
        return

    if call.data.startswith("buy_"):
        prod_key = call.data.replace("buy_", "")
        if prod_key in PRODUCTS_INFO:
            stock_len = len(STOCK_DATABASE.get(prod_key, []))
            if stock_len == 0:
                bot.answer_callback_query(call.id, "❌ عذراً، نفدت كمية هذا المنتج للتو!", show_alert=True)
                return

            bot.answer_callback_query(call.id)
            USER_SELECTED_PRODUCT[chat_id] = prod_key
            info = PRODUCTS_INFO[prod_key]

            markup = InlineKeyboardMarkup(row_width=1)
            markup.add(InlineKeyboardButton("🪙 إتمام الشراء / الدفع الفوري", callback_data="pay_steps_" + prod_key))
            markup.add(
                InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"),
                InlineKeyboardButton("🛠️ الدعم الفني", url=SUPPORT_WHATSAPP)
            )

            msg_text = (
                f"🏷️ **{info['name']}**\n"
                f"💰 **Price:** `${info['price']}`\n\n"
                f"📦 **Stock:** `{stock_len}`\n"
                f"📰 **Description:**\n\n"
                f"{info['description']}\n\n"
                f"🛍️ **Buy Quantity:** 1"
            )
            send_product_card(chat_id, prod_key, msg_text, markup)

    elif call.data.startswith("pay_steps_"):
        prod_key = call.data.replace("pay_steps_", "")
        info = PRODUCTS_INFO[prod_key]
        bot.answer_callback_query(call.id)
        
        pay_msg = (
            f"🪙 **خطوات الدفع الفوري عبر Binance Pay:**\n\n"
            f"1️⃣ حول مبلغ (`{info['price']} USDT`) إلى Binance ID: `{BINANCE_ID}`\n\n"
            f"2️⃣ انسخ **رقم العملية (Order ID)** من باينانس وأرسله هنا في الشات لتتلقى حسابك في نفس الثانية!"
        )
        bot.send_message(chat_id, pay_msg, parse_mode="Markdown")

    elif call.data == "show_payments":
        bot.answer_callback_query(call.id)
        pay_text = f"🪙 **معلومات الدفع في متجر Pixora Store:**\n\nBinance Pay ID: `{BINANCE_ID}`\n\nاختر منتجك أولاً من القائمة الرئيسية ثم أرسل رقم العملية بعد التحويل لتستلم طلبك فوراً."
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

        if len(STOCK_DATABASE.get(prod_key, [])) == 0:
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
