import os
import time
import json
import threading
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
# ضع هنا رقم الـ Chat ID الخاص بك الذي حصلت عليه من @userinfobot
ADMIN_ID = 1004439571098  # استبدله برقمك إذا كان مختلفاً

BINANCE_ID = "957483337"
RENDER_URL = os.environ.get("RENDER_URL", "").strip()
SUPPORT_WHATSAPP = "https://wa.me/213555668244"

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
app = Flask(__name__)

# قائمة المنتجات كاملة
RAW_PRODUCTS = [
    ("capcut", "🎞️ CapCut", 1.3, "CapCut Pro 30 Days - التسليم فوري وآلي."),
    ("gemini", "💠 Gemini", 3.0, "Gemini AI Pro 18 Months Plan - سعة 5TB."),
    ("office", "🟩 Microsoft Office 365", 0.30, "Office 365 Plus 5 Devices + 1TB OneDrive."),
    ("autodesk", "🔺 Autodesk", 3.0, "Autodesk Admin Dashboard 1 Year Access."),
    ("canva", "🎨 Canva Edu", 4.0, "رابط دعوة رسمي لحساب Canva Edu Pro مدى الحياة."),
    ("chatgpt", "🤖 ChatGPT Plus", 5.0, "اشتراك ChatGPT Plus لمدة شهر."),
    ("netflix", "🍿 Netflix UHD", 3.5, "حساب Netflix بريميوم شاشة واحدة لمدة شهر."),
    ("spotify", "🎵 Spotify Premium", 2.0, "اشتراك Spotify فردي مدة شهر."),
    ("nordvpn", "🛡️ NordVPN", 2.5, "حساب NordVPN مدفوع لمدة سنة."),
    ("crunchyroll", "🍥 Crunchyroll", 1.8, "حساب Crunchyroll Mega Fan لمدة شهر.")
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
        print("Error saving orders:", e)

WELCOME_TEXT = """🔥 <b>أهلاً بك في متجر Pixora Store الرقمي الأول!</b> 🚀

⚡ <i>نوفر لك أقوى الحسابات والاشتراكات الرقمية المدفوعة بأفضل الأسعار وأعلى ضمان رسمي.</i>
💎 <b>التسليم فوري</b> بعد إتمام الدفع عبر Binance Pay!

👇 <b>اختر منتجك أدناه، وابدأ طلبك الآن:</b>"""

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

@app.route('/')
def home():
    return "Pixora Store Bot is Running!", 200

@app.route('/' + BOT_TOKEN, methods=['POST'])
def receive_update():
    if request.headers.get('content-type') == 'application/json':
        try:
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
        except Exception as e:
            print("Update error:", e)
        return "!", 200
    return "Unsupported Media Type", 415

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=get_main_menu_markup(), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    data = call.data
    
    # تحكم المدير في قبول أو رفض الطلب
    if data.startswith("admin_approve_"):
        order_key = data.replace("admin_approve_", "")
        if order_key in PENDING_ORDERS:
            order_info = PENDING_ORDERS.pop(order_key)
            u_chat_id = order_info["chat_id"]
            prod_key = order_info["prod_key"]
            p_name = PRODUCTS_INFO[prod_key]["name"]
            
            if len(STOCK_DATABASE.get(prod_key, [])) > 0:
                item = STOCK_DATABASE[prod_key].pop(0)
                
                # حفظ الطلب
                all_orders = load_orders()
                s_id = str(u_chat_id)
                if s_id not in all_orders:
                    all_orders[s_id] = []
                all_orders[s_id].append({
                    "product": p_name,
                    "item": item,
                    "order_id": order_info["order_id"],
                    "time": time.strftime("%Y-%m-%d %H:%M:%S")
                })
                save_orders(all_orders)
                
                # رسالة التسليم للزبون
                success_text = f"""🎉 <b>تم تأكيد عملية الدفع بنجاح!</b>

📦 بيانات حسابك لمنتج <b>{p_name}</b>:
<code>{item}</code>

📜 تم حفظ الطلب في (سجل مشترياتي).
شكراً لتعاملك مع <b>Pixora Store</b> 💚"""
                bot.send_message(u_chat_id, success_text, parse_mode="HTML")
                bot.edit_message_text(f"✅ تم تأكيد وتسليم طلب ({p_name}) للعميل بنجاح.", chat_id, msg_id)
            else:
                bot.send_message(u_chat_id, f"⚠️ تم التحقق من الدفع بنجاح ولكن المنتج ({p_name}) نفد من المخزون، يرجى مراسلة الدعم الفني.")
                bot.edit_message_text(f"⚠️ المخزون فارغ لهذا المنتج!", chat_id, msg_id)
        else:
            bot.answer_callback_query(call.id, "تم اتخاذ إجراء مسبقاً بشأن هذا الطلب.", show_alert=True)
        return

    elif data.startswith("admin_reject_"):
        order_key = data.replace("admin_reject_", "")
        if order_key in PENDING_ORDERS:
            order_info = PENDING_ORDERS.pop(order_key)
            u_chat_id = order_info["chat_id"]
            bot.send_message(u_chat_id, "❌ تعذر تأكيد عملية الدفع. يرجى التأكد من التحويل والتواصل مع الدعم الفني.")
            bot.edit_message_text("❌ تم رفض الطلب.", chat_id, msg_id)
        else:
            bot.answer_callback_query(call.id, "تم اتخاذ إجراء مسبقاً.", show_alert=True)
        return

    # مسار المستخدم العادي
    if data.startswith("sold_out_"):
        bot.answer_callback_query(call.id, "❌ عذراً، هذا المنتج غير متوفر في المخزن حالياً!", show_alert=True)
        
    elif data.startswith("buy_"):
        prod_key = data.replace("buy_", "")
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
            
            msg_text = f"""🏷️ <b>{info['name']}</b>
💰 <b>Price:</b> <code>${info['price']}</code>

📦 <b>Stock:</b> <code>{stock_len}</code>
📰 <b>Description:</b>

{info['description']}

🛍️ <b>Buy Quantity:</b> 1"""
            
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, msg_text, reply_markup=markup, parse_mode="HTML")
            
    elif data.startswith("pay_steps_"):
        prod_key = data.replace("pay_steps_", "")
        info = PRODUCTS_INFO[prod_key]
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("🔙 رجوع للمنتج", callback_data="buy_" + prod_key), InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
        
        pay_msg = f"""🪙 <b>خطوات الدفع عبر Binance Pay:</b>

1️⃣ حول مبلغ (<code>{info['price']} USDT</code>) إلى Binance ID: <code>{BINANCE_ID}</code>

2️⃣ انسخ <b>رقم العملية (Order ID)</b> أو أرسل صورة الإشعار هنا في الشات لتأكيد طلبك واستلام حسابك فوراً!"""
        
        safe_delete_message(chat_id, msg_id)
        bot.send_message(chat_id, pay_msg, reply_markup=markup, parse_mode="HTML")
        
    elif data == "show_payments":
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
        
        pay_text = f"""🪙 <b>معلومات الدفع في متجر Pixora Store:</b>

Binance Pay ID: <code>{BINANCE_ID}</code>

اختر منتجك أولاً من القائمة الرئيسية ثم أرسل رقم العملية بعد التحويل."""
        
        safe_delete_message(chat_id, msg_id)
        bot.send_message(chat_id, pay_text, reply_markup=markup, parse_mode="HTML")

    elif data == "my_orders":
        bot.answer_callback_query(call.id)
        all_orders = load_orders()
        user_history = all_orders.get(str(chat_id), [])
        
        if not user_history:
            history_text = "📜 <b>سجل مشترياتي:</b>\n\nعذراً، ليس لديك أي عمليات شراء مسجلة حتى الآن."
        else:
            history_text = "📜 <b>سجل مشترياتي السابقة:</b>\n\n"
            for idx, order in enumerate(user_history, 1):
                history_text += f"{idx}️⃣ <b>المنتج:</b> {order['product']}\n🔑 <b>البيانات:</b> <code>{order['item']}</code>\n🆔 <b>رقم العملية:</b> <code>{order['order_id']}</code>\n📅 <b>الوقت:</b> {order['time']}\n------------------------\n"
        
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
        
        safe_delete_message(chat_id, msg_id)
        bot.send_message(chat_id, history_text, reply_markup=markup, parse_mode="HTML")
        
    elif data == "main_menu":
        bot.answer_callback_query(call.id)
        USER_SELECTED_PRODUCT.pop(chat_id, None)
        safe_delete_message(chat_id, msg_id)
        bot.send_message(chat_id, WELCOME_TEXT, reply_markup=get_main_menu_markup(), parse_mode="HTML")

@bot.message_handler(content_types=['text', 'photo'])
def handle_incoming(message):
    chat_id = message.chat.id
    if message.content_type == 'text' and message.text.startswith('/'):
        return
        
    if chat_id not in USER_SELECTED_PRODUCT:
        bot.send_message(chat_id, "⚠️ يرجى اختيار المنتج أولاً من القائمة الرئيسية (/start) قبل إرسال بيانات الدفع.")
        return
        
    prod_key = USER_SELECTED_PRODUCT[chat_id]
    info = PRODUCTS_INFO[prod_key]
    
    if len(STOCK_DATABASE.get(prod_key, [])) == 0:
        bot.send_message(chat_id, "⚠️ عذراً، نفدت كمية هذا المنتج حالياً!")
        return

    order_id = message.text.strip() if message.content_type == 'text' else "صورة إيصال"
    order_token = f"{chat_id}_{int(time.time())}"
    PENDING_ORDERS[order_token] = {
        "chat_id": chat_id,
        "prod_key": prod_key,
        "order_id": order_id
    }
    
    USER_SELECTED_PRODUCT.pop(chat_id, None)
    
    # رسالة للزبون
    bot.send_message(chat_id, "⏳ <b>تم استلام بيانات الدفع بنجاح!</b>\nجاري مراجعة التحويل وإرسال بيانات الحساب إليك هنا خلال لحظات...", parse_mode="HTML")
    
    # رسالة للمدير (لك أنت) للموافقة الفورية
    admin_markup = InlineKeyboardMarkup(row_width=2)
    admin_markup.add(
        InlineKeyboardButton("✅ تأكيد وتسليم الطلب", callback_data="admin_approve_" + order_token),
        InlineKeyboardButton("❌ رفض", callback_data="admin_reject_" + order_token)
    )
    
    user_name = message.from_user.first_name or "عميل"
    user_username = f"@{message.from_user.username}" if message.from_user.username else f"ID: {chat_id}"
    
    admin_msg = f"""🔔 <b>طلب شراء جديد في متجر Pixora!</b>

👤 <b>العميل:</b> {user_name} ({user_username})
🛍️ <b>المنتج:</b> {info['name']}
💰 <b>المبلغ المطلوب:</b> {info['price']} USDT
🆔 <b>رقم العملية:</b> <code>{order_id}</code>

👇 <i>تأكد من تطبيق Binance ثم اضغط تأكيد:</i>"""

    try:
        if message.content_type == 'photo':
            photo_id = message.photo[-1].file_id
            bot.send_photo(ADMIN_ID, photo_id, caption=admin_msg, reply_markup=admin_markup, parse_mode="HTML")
        else:
            bot.send_message(ADMIN_ID, admin_msg, reply_markup=admin_markup, parse_mode="HTML")
    except Exception as e:
        print("Error notifying admin:", e)

def init_app():
    time.sleep(2)
    if BOT_TOKEN and RENDER_URL:
        try:
            target_url = f"{RENDER_URL}/{BOT_TOKEN}"
            bot.set_webhook(url=target_url)
            print(f"Webhook registered: {target_url}")
        except Exception as e:
            print("Webhook init error:", e)

threading.Thread(target=init_app, daemon=True).start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 1000
