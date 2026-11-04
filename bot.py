import os, time, hmac, hashlib, urllib.parse, json, requests, telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY", "").strip()
BINANCE_SECRET_KEY = os.environ.get("BINANCE_SECRET_KEY", "").strip()
ADMIN_ID = 1004439571098
BINANCE_ID = "957483337"
RENDER_URL = os.environ.get("RENDER_URL", "https://pixora-bot-1.onrender.com").strip()
SUPPORT_WHATSAPP = "https://wa.me/213555668244"

if not BOT_TOKEN:
    print("FATAL ERROR: BOT_TOKEN is missing in Environment Variables!")

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

RAW_PRODUCTS = [
    ("capcut", "🎞️ CapCut", 1.3, 
     "📱 CAPCUT PRO Individual – 30 DAYS\n\n"
     "📌 INFORMATIONS\n"
     "✔️ CapCut Pro account, valid for 29-30 days.\n"
     "✔️ Format : Email | Password\n\n"
     "Delivery is automatic after payment confirmation."),
     
    ("gemini", "💠 Gemini", 3.0, 
     "⚡ 18 Months Plan\n"
     "⚡ 5TB cloud storage included\n"
     "⚡ 100% Genuine Gemini AI Pro Subscription Activated on Your Own Gmail."),
     
    ("office", "🟩 Microsoft Office 365", 0.30, 
     "✔️ Microsoft 365 Plus – 100GB/1000GB | 5 Devices\n\n"
     "✔️ Activate on up to 5 devices\n"
     "✔️ Instant & automatic delivery"),
     
    ("autodesk", "🔺 Autodesk", 3.0, 
     "✔️ Autodesk Admin Dashboard Access\n"
     "✔️ 1 Year Subscription\n"
     "Delivery is automatic after payment confirmation."),
     
    ("canva", "🎨 Canva", 4.0, 
     "Canva Edu pro invite 499 user\n\n"
     "After placing your order, please send your Canva registered email address to receive your invitation."),
     
    ("adobe", "🔴 Adobe", 2.5, "- Full Adobe Creative Cloud access.\n- Full warranty and stability."),
    ("avira", "🔴 Avira", 2.0, "- Premium Antivirus & Security subscription."),
    ("chatgpt", "🔴 ChatGPT", 3.0, "- ChatGPT Plus account access."),
    ("coursera", "🔴 Coursera", 2.0, "- Coursera subscription for professional certificates."),
    ("duolingo", "🔴 Duolingo", 0.75, "- Duolingo Super 12 Months subscription."),
    ("elevenlabs", "🔴 ElevenLabs", 3.5, "- AI Voice Generator premium plan."),
    ("expressvpn", "🔴 ExpressVPN", 2.5, "- High-speed secure VPN subscription."),
    ("figma", "🔴 Figma", 2.0, "- Figma Pro team access for designers."),
    ("framer", "🔴 Framer", 2.0, "- Framer Pro web building subscription."),
    ("gamma", "🔴 Gamma", 2.0, "- AI presentations and docs generator."),
    ("grok", "🔴 Grok", 2.5, "- xAI Grok premium access."),
    ("hmavpn", "🔴 HMA VPN", 0.55, "- HideMyAss VPN secure access."),
    ("jetbrain", "🔴 JetBrain", 3.0, "- All Products Pack license access."),
    ("kaspersky", "🔴 Kaspersky", 2.0, "- Kaspersky Total Security license."),
    ("linkedin", "🔴 LinkedIn", 3.0, "- LinkedIn Premium Career/Business access."),
    ("lovable", "🔴 Lovable", 2.5, "- Full stack AI web app builder."),
    ("muse", "🔴 Muse", 2.0, "- Muse AI premium tools access."),
    ("notion", "🔴 Notion", 2.0, "- Notion Pro workspace subscription."),
    ("youtube", "🔴 YouTube", 2.0, "- YouTube Premium ad-free subscription."),
    ("ilovepdf", "🔴 iLovePdf", 1.5, "- iLovePDF Premium tools access."),
    ("api", "🔴 API", 5.0, "- High limit developer API keys."),
    ("grammarly", "🔴 Grammarly", 2.0, "- Grammarly Premium writing assistant."),
    ("nordvpn", "🔴 Nord Vpn", 2.0, "- NordVPN secure high-speed servers."),
    ("scribd", "🔴 Scribd", 2.0, "- Scribd ebooks and audiobooks access."),
    ("wispr", "🔴 Wispr", 2.0, "- Wispr Flow voice dictation tool."),
    ("udemy", "🔴 Udemy", 2.0, "- Premium courses access plan.")
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

WELCOME_TEXT = (
    "🔥 **أهلاً بك في متجر Pixora Store الرقمي الأول!** 🚀\n\n"
    "⚡ *نوفر لك أقوى الحسابات والاشتراكات الرقمية المدفوعة بأفضل الأسعار وأعلى ضمان رسمي.*\n"
    "💎 **التسليم فوري وآلي بالكامل** خلال ثوانٍ معدودة بعد إتمام الدفع عبر Binance Pay!\n\n"
    "👇 **اختر منتجك أدناه، وابدأ تطوير أعمالك أو أدواتك الآن:**"
)

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
            print("Update processing error:", e)
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
        if data.get("code") == "000000" and "data" in data:
            for tx in data["data"]:
                t_id, p_id = str(tx.get("orderId", "")), str(tx.get("prepayId", ""))
                if (t_id == clean_id or p_id == clean_id) and float(tx.get("amount", 0)) >= expected_amount and tx.get("currency") == "USDT":
                    USED_TRANSACTIONS.add(clean_id)
                    return True, "تم التحقق بنجاح"
            return False, "لم يتم العثور على حوالة بهذا الرقم أو أن المبلغ أقل من المطلوب."
        return False, f"رد باينانس: {data.get('msg', 'تحقق من المفاتيح')}"
    except Exception as e:
        print("Binance request error:", e)
        return False, "خطأ في الاتصال: " + str(e)

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=get_main_menu_markup(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id, msg_id = call.message.chat.id, call.message.message_id
    if call.data.startswith("sold_out_"):
        bot.answer_callback_query(call.id, "❌ عذراً، هذا المنتج غير متوفر في المخزن حالياً!", show_alert=True)
    elif call.data.startswith("buy_"):
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
            markup.add(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"), InlineKeyboardButton("🛠️ الدعم الفني", url=SUPPORT_WHATSAPP))
            msg_text = f"🏷️ **{info['name']}**\n💰 **Price:** `${info['price']}`\n\n📦 **Stock:** `{stock_len}`\n📰 **Description:**\n\n{info['description']}\n\n🛍️ **Buy Quantity:** 1"
            
            try:
                bot.delete_message(chat_id, msg_id)
            except Exception:
                pass
            bot.send_message(chat_id, msg_text, reply_markup=markup, parse_mode="Markdown")
            
    elif call.data.startswith("pay_steps_"):
        prod_key = call.data.replace("pay_steps_", "")
        info = PRODUCTS_INFO[prod_key]
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("🔙 رجوع للمنتج", callback_data="buy_" + prod_key), InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
        pay_msg = f"🪙 **خطوات الدفع الفوري عبر Binance Pay:**\n\n1️⃣ حول مبلغ (`{info['price']} USDT`) إلى Binance ID: `{BINANCE_ID}`\n\n2️⃣ انسخ **رقم العملية (Order ID)** من باينانس وأرسله هنا في الشات لتتلقى حسابك في نفس الثانية!"
        
        try:
            bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
        bot.send_message(chat_id, pay_msg, reply_markup=markup, parse_mode="Markdown")
        
    elif call.data == "show_payments":
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
        pay_text = f"🪙 **معلومات الدفع في متجر Pixora Store:**\n\nBinance Pay ID: `{BINANCE_ID}`\n\nاختر منتجك أولاً من القائمة الرئيسية ثم أرسل رقم العملية بعد التحويل لتستلم طلبك فوراً."
        
        try:
            bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
        bot.send_message(chat_id, pay_text, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "my_orders":
        bot.answer_callback_query(call.id)
        all_orders = load_orders()
        user_history = all_orders.get(str(chat_id), [])
        
        if not user_history:
            history_text = "📜 **سجل مشترياتي:**\n\nعذراً، ليس لديك أي عمليات شراء مسجلة حتى الآن."
        else:
            history_text = "📜 **سجل مشترياتي السابقة:**\n\n"
            for idx, order in enumerate(user_history, 1):
                history_text += f"{idx}️⃣ **المنتج:** {order['product']}\n🔑 **البيانات:** <code>{order['item']}</code>\n🆔 **رقم العملية:** <code>{order['order_id']}</code>\n📅 **الوقت:** {order['time']}\n------------------------\n"
        
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
        
        try:
            bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
        bot.send_message(chat_id, history_text, reply_markup=markup, parse_mode="HTML")
        
    elif call.data == "main_menu":
        bot.answer_callback_query(call.id)
        USER_SELECTED_PRODUCT.pop(chat_id, None)
        try:
            bot.delete_message(chat_id, msg_id)
