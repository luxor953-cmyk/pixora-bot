import os
import time
import json
import threading
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_ID = 1004439571098
BINANCE_ID = "957483337"
RENDER_URL = os.environ.get("RENDER_URL", "").strip()
SUPPORT_WHATSAPP = "https://wa.me/213555668244"

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
app = Flask(__name__)

# قائمة المنتجات الأصلية تماماً كما في الصورة (بدون تطبيقات المشاهدة مثل Crunchyroll)
RAW_PRODUCTS = [
    # المنتجات التي تتوفر في المخزن (تظهر في الأعلى تلقائياً)
    ("gemini_pro_18m", "1 🔥 Gemini Pro 18 Months Link", 3.00),
    ("duolingo_super_12m", "🦉 Duolingo Super 12 Months", 0.75),
    ("adobe_express_12m", "🎨 Adobe Express 12M", 0.35),
    ("hma_vpn", "🐺 HMA VPN Android/PC 30-25 Days", 0.55),
    ("spotify_prem_3m", "🟢 Spotify Premium 3M", 1.45),
    
    # باقي المنتجات الأصلية من الصورة
    ("capcut", "✂️ CapCut", 1.30),
    ("chatgpt", "🤖 ChatGPT", 18.00),
    ("gemini_ai", "1️⃣ Gemini Ai", 3.00),
    ("microsoft_365", "🟩 Microsoft 365", 0.30),
    ("office_pro_plus_p", "💼 Office Pro Plus (P...)", 2.50),
    ("windows_phone", "🪟 Windows (Phone...)", 2.50),
    ("office_pp_online", "💼 Office PP (Online...)", 3.00),
    ("windows_online", "🪟 Windows (Online...)", 3.50),
    ("autodesk", "🔺 AUTODESK", 3.00),
    ("muse_ai", "Ⓜ️ Muse AI", 5.00),
    ("chatgpt_plus_best", "🤖 🔥(💚BEST SELLER) ChatGPT Plus (G Pay...", 18.00)
]

PRODUCTS_INFO = {k: {"name": n, "price": p} for k, n, p in RAW_PRODUCTS}

# قاعدة بيانات المخزون مطابقة للكميات المكتوبة في الصورة
STOCK_DATABASE = {k: [] for k in PRODUCTS_INFO}
STOCK_DATABASE["gemini_pro_18m"] = [
    "Gemini_Link_1", "Gemini_Link_2", "Gemini_Link_3", "Gemini_Link_4"
]
STOCK_DATABASE["duolingo_super_12m"] = [
    "Duo_Key_1", "Duo_Key_2", "Duo_Key_3", "Duo_Key_4", "Duo_Key_5"
]
STOCK_DATABASE["adobe_express_12m"] = [f"Adobe_Acc_{i}" for i in range(1, 11)]
STOCK_DATABASE["hma_vpn"] = ["HMA_VPN_Account_1"]
STOCK_DATABASE["spotify_prem_3m"] = ["Spotify_Key_1", "Spotify_Key_2"]

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

WELCOME_TEXT = "Choose Your Product:"

def get_main_menu_markup():
    markup = InlineKeyboardMarkup()
    
    # 1. المنتجات المتوفرة أولاً (صف واحد لكل منتج مع السعر والكمية مثل الصورة الأصلية)
    for k, info in PRODUCTS_INFO.items():
        stock_count = len(STOCK_DATABASE.get(k, []))
        if stock_count > 0:
            btn_text = f"{info['name']} · ${info['price']} ({stock_count})"
            markup.add(InlineKeyboardButton(btn_text, callback_data=f"buy_{k}"))
            
    # 2. المنتجات ذات الرصيد 0 في شبكة ثنائية (صفوف بـ 2 أزرار كما في الجزء العلوي من صورتك)
    out_stock_btns = []
    for k, info in PRODUCTS_INFO.items():
        if len(STOCK_DATABASE.get(k, [])) == 0:
            out_stock_btns.append(InlineKeyboardButton(f"{info['name']}", callback_data=f"sold_out_{k}"))
            
    for i in range(0, len(out_stock_btns), 2):
        if i + 1 < len(out_stock_btns):
            markup.row(out_stock_btns[i], out_stock_btns[i+1])
        else:
            markup.row(out_stock_btns[i])

    # 3. زر العودة الرئيسي كما في الصورة
    markup.add(InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu"))
    return markup

@app.route('/')
def home():
    return "Pixora Store is Running!", 200

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
    bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=get_main_menu_markup())

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
                msg = f"🎉 <b>تم تأكيد الدفع بنجاح!</b>\n\n📦 بيانات {p_name}:\n<code>{item}</code>\n\nشكراً لتعاملك مع <b>Pixora Store</b> 💚"
                bot.send_message(u_id, msg, parse_mode="HTML")
                bot.edit_message_text(f"✅ تم تسليم {p_name} للعميل بنجاح.", chat_id, msg_id)
            else:
                bot.send_message(u_id, "⚠️ نفد المخزون، يرجى التواصل مع الدعم الفني.")
                bot.edit_message_text("⚠️ المخزون فارغ لهذا الصنف!", chat_id, msg_id)
        return

    elif data.startswith("admin_reject_"):
        token = data.replace("admin_reject_", "")
        if token in PENDING_ORDERS:
            o = PENDING_ORDERS.pop(token)
            bot.send_message(o["chat_id"], "❌ تعذر تأكيد عملية التحويل. يرجى التواصل مع الدعم الفني.")
            bot.edit_message_text("❌ تم رفض الطلب.", chat_id, msg_id)
        return

    if data.startswith("sold_out_"):
        bot.answer_callback_query(call.id, "❌ Sold Out - هذا المنتج غير متوفر حالياً!", show_alert=True)

    elif data.startswith("buy_"):
        p_key = data.replace("buy_", "")
        if p_key in PRODUCTS_INFO:
            stock = len(STOCK_DATABASE.get(p_key, []))
            if stock == 0:
                bot.answer_callback_query(call.id, "❌ نفدت الكمية للتو!", show_alert=True)
                return
            bot.answer_callback_query(call.id)
            USER_SELECTED_PRODUCT[chat_id] = p_key
            info = PRODUCTS_INFO[p_key]
            markup = InlineKeyboardMarkup(row_width=1)
            markup.add(InlineKeyboardButton("🪙 إتمام الشراء / الدفع الفوري", callback_data=f"pay_steps_{p_key}"))
            markup.add(InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu"))
            
            text = f"🏷️ <b>{info['name']}</b>\n💰 <b>Price:</b> <code>${info['price']}</code>\n📦 <b>Stock:</b> <code>{stock}</code>\n\n🛍️ <b>Buy Quantity:</b> 1"
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

    elif data.startswith("pay_steps_"):
        p_key = data.replace("pay_steps_", "")
        info = PRODUCTS_INFO[p_key]
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("🔙 رجوع", callback_data=f"buy_{p_key}"), InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu"))
        
        text = f"🪙 <b>خطوات الدفع عبر Binance Pay:</b>\n\n1️⃣ حول مبلغ (<code>{info['price']} USDT</code>) إلى Binance ID: <code>{BINANCE_ID}</code>\n\n2️⃣ أرسل <b>رقم العملية (Order ID)</b> أو صورة الإشعار هنا في الشات لتأكيد طلبك واستلام حسابك فوراً!"
        safe_delete_message(chat_id, msg_id)
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

    elif data == "main_menu":
        bot.answer_callback_query(call.id)
        USER_SELECTED_PRODUCT.pop(chat_id, None)
        safe_delete_message(chat_id, msg_id)
        bot.send_message(chat_id, WELCOME_TEXT, reply_markup=get_main_menu_markup())

@bot.message_handler(content_types=['text', 'photo'])
def handle_incoming(message):
    chat_id = message.chat.id
    if message.content_type == 'text' and message.text.startswith('/'):
        return

    if chat_id not in USER_SELECTED_PRODUCT:
        bot.send_message(chat_id, "⚠️ يرجى اختيار المنتج أولاً من القائمة (/start) قبل إرسال بيانات الدفع.")
        return

    p_key = USER_SELECTED_PRODUCT[chat_id]
    info = PRODUCTS_INFO[p_key]
    order_id = message.text.strip() if message.content_type == 'text' else "صورة إيصال"
    token = f"{chat_id}_{int(time.time())}"

    PENDING_ORDERS[token] = {
        "chat_id": chat_id,
        "prod_key": p_key,
        "order_id": order_id
    }
    USER_SELECTED_PRODUCT.pop(chat_id, None)
    bot.send_message(chat_id, "⏳ <b>تم استلام بيانات التحويل بنجاح!</b>\nجاري مراجعة الطلب وإرسال بيانات الحساب إليك هنا خلال لحظات...", parse_mode="HTML")

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✅ تأكيد وتسليم الطلب", callback_data=f"admin_approve_{token}"),
        InlineKeyboardButton("❌ رفض", callback_data=f"admin_reject_{token}")
    )
    user_name = message.from_user.first_name or "عميل"
    user_username = f"@{message.from_user.username}" if message.from_user.username else f"ID: {chat_id}"
    admin_msg = f"🔔 <b>طلب شراء جديد في Pixora Store!</b>\n\n👤 <b>العميل:</b> {user_name} ({user_username})\n🛍️ <b>المنتج:</b> {info['name']}\n💰 <b>المطلوب:</b> {info['price']} USDT\n🆔 <b>البيان/التحويل:</b> <code>{order_id}</code>\n\n👇 <i>تأكد من وصول المبلغ في تطبيق Binance ثم اضغط تأكيد:</i>"

    try:
        if message.content_type == 'photo':
            photo_id = message.photo[-1].file_id
            bot.send_photo(ADMIN_ID, photo_id, caption=admin_msg, reply_markup=markup, parse_mode="HTML")
        else:
            bot.send_message(ADMIN_ID, admin_msg, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        print("Admin notify error:", e)

def init_app():
    time.sleep(2)
    if BOT_TOKEN and RENDER_URL:
        try:
            bot.set_webhook(url=f"{RENDER_URL}/{BOT_TOKEN}")
        except Exception as e:
            print("Webhook error:", e)

threading.Thread(target=init_app, daemon=True).start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
