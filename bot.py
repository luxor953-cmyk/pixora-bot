import os, time, hmac, hashlib, urllib.parse, json, requests, telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request

BOT_TOKEN = os.environ["BOT_TOKEN"]
BINANCE_API_KEY = os.environ["BINANCE_API_KEY"]
BINANCE_SECRET_KEY = os.environ["BINANCE_SECRET_KEY"]
ADMIN_ID = 1004439571098
BINANCE_ID = "957483337"
RENDER_URL = "https://pixora-bot-egyp.onrender.com"
SUPPORT_WHATSAPP = "https://wa.me/213555668244"

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
try:
    bot.remove_webhook()
    bot.set_webhook(url=RENDER_URL + "/" + BOT_TOKEN)
except Exception as e:
    print("Webhook error:", e)

RAW_PRODUCTS = [
    ("capcut", "🎞️ CapCut", 2.0, "- Full 30 days private Pro Team account .\n- Maximum 2 devices , with full warranty .\n- Stable Account full 30 days (no 7days renew ).\n- Login to mobile App first next to laptop (desktop App no web) via QR code ."),
    ("gemini", "💠 Gemini", 2.0, "- Full access to Gemini Advanced & Pro features.\n- Direct official invite or shared private account.\n- Fast response and full warranty for the duration."),
    ("office", "🟩 Microsoft 365", 2.0, "- Official Microsoft 365 account (5 PCs/Macs + 5 Tablets + 5 Phones).\n- 1TB OneDrive Cloud storage included.\n- Full warranty and multi-device support."),
    ("autodesk", "🔺 Autodesk", 3.0, "- Official Autodesk Educational/Pro access.\n- Access to AutoCAD, Revit, Maya, and more.\n- Full warranty and stable subscription."),
    ("canva", "🎨 Canva", 2.0, "- Canva Pro Team Invitation.\n- Unlock all premium templates, fonts, and background remover.\n- Private account safety with full warranty."),
    ("adobe", "🔴 Adobe", 2.5, "- Full Adobe Creative Cloud access.\n- Full warranty and stability."),
    ("avira", "🔴 Avira", 2.0, "- Premium Antivirus & Security subscription.\n- Full warranty."),
    ("chatgpt", "🔴 ChatGPT", 3.0, "- ChatGPT Plus account access.\n- Fast GPT-4o and DALL-E generation."),
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
STOCK_DATABASE["gemini"] = ["https://g.co/gemini/share/sample_link_1", "https://g.co/gemini/share/sample_link_2"]
STOCK_DATABASE["office"] = ["Office365_Key_1: kc5921@o365pp.com  / &$^2^jGq"]
STOCK_DATABASE["autodesk"] = ["Autodesk_Key_ABC123"]
STOCK_DATABASE["canva"] = ["https://www.canva.com/brand/join?inv=sample_1"]

USED_TRANSACTIONS = set()
USER_SELECTED_PRODUCT = {}

# نظام حفظ واسترجاع السجلات بشكل دائم في ملف orders.json
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
            btns.append(InlineKeyboardButton(info["name"], callback_data="sold_out_" + k))
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

app = Flask('')

@app.route('/')
def home():
    return "Pixora Store Auto-Delivery Bot is Live!"

@app.route('/' + BOT_TOKEN, methods=['POST'])
def receive_update():
    update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
    bot.process_new_updates([update])
    return "!", 200

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
        return False, "تعذر الاتصال ببوابة باينانس، تأكد من مفاتيح الـ API."
    except Exception as e:
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
                history_text += f"{idx}️⃣ **المنتج:** {order['product']}\n🔑 **البيانات:** `{order['item']}`\n🆔 **رقم العملية:** `{order['order_id']}`\n📅 **الوقت:** {order['time']}\n------------------------\n"
        
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
        
        try:
            bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
        bot.send_message(chat_id, history_text, reply_markup=markup, parse_mode="Markdown")
        
    elif call.data == "main_menu":
        bot.answer_callback_query(call.id)
        USER_SELECTED_PRODUCT.pop(chat_id, None)
        try:
            bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
        bot.send_message(chat_id, WELCOME_TEXT, reply_markup=get_main_menu_markup(), parse_mode="Markdown")

@bot.message_handler(content_types=['text', 'photo', 'document'])
def handle_incoming(message):
    chat_id = message.chat.id
    if message.content_type == 'text':
        if message.text.startswith('/'):
            return
        if chat_id not in USER_SELECTED_PRODUCT:
            bot.send_message(chat_id, "⚠️ يرجى اختيار المنتج أولاً من القائمة الرئيسية (/start) قبل إرسال رقم العملية.")
            return
        prod_key = USER_SELECTED_PRODUCT[chat_id]
        info = PRODUCTS_INFO[prod_key]
        if len(STOCK_DATABASE.get(prod_key, [])) == 0:
            bot.send_message(chat_id, "⚠️ عذراً، نفدت كمية هذا المنتج حالياً!")
            return
        
        wait_msg = bot.send_message(chat_id, "⏳ جاري التحقق من عملية الدفع عبر Binance تلقائياً...")
        order_id_input = message.text.strip()
        is_valid, status_text = verify_binance_payment(order_id_input, info["price"])
        
        if is_valid:
            item = STOCK_DATABASE[prod_key].pop(0)
            USER_SELECTED_PRODUCT.pop(chat_id, None)
            
            # حفظ العملية بشكل دائم في ملف orders.json
            all_orders = load_orders()
            str_chat_id = str(chat_id)
            if str_chat_id not in all_orders:
                all_orders[str_chat_id] = []
            
            new_order = {
                "product": info['name'],
                "item": item,
                "order_id": order_id_input,
                "time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            all_orders[str_chat_id].append(new_order)
            save_orders(all_orders)

            bot.edit_message_text(f"🎉 **تم تأكيد الدفع وتسليم طلبك بنجاح!**\n\n📦 بيانات حسابك لمنتج *{info['name']}*:\n`{item}`\n\n📜 تم حفظ طلبك في (سجل مشترياتي).\n\nشكراً لثقتك بمتجر *Pixora Store* 💚", chat_id, wait_msg.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text(f"❌ لم يكتمل التحقق: {status_text}\n\nتأكد من صحة رقم العملية وأن المبلغ مطابق للسعر.", chat_id, wait_msg.message_id)
        return
    bot.send_message(chat_id, "📌 المتجر يعمل بنظام التسليم الآلي عبر Binance Pay. يرجى إرسال **رقم العملية (Order ID)** النصي بعد إتمام التحويل للحصول على طلبك فوراً.", parse_mode="Markdown")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
