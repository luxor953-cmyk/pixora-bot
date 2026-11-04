import os
import time
import json
import threading
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request
from products import PRODUCTS_INFO, STOCK_DATABASE

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_ID = 1004439571098
BINANCE_ID = "957483337"
RENDER_URL = os.environ.get("RENDER_URL", "").strip()
SUPPORT_WHATSAPP = "https://wa.me/213555668244"

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
app = Flask(__name__)

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

WELCOME_TEXT = """🔥 <b>أهلاً بك في متجر Pixora Store الرقمي!</b> 🚀

⚡ <i>نوفر لك أقوى الحسابات والاشتراكات الرقمية بأفضل الأسعار وأعلى ضمان رسمي.</i>
💎 <b>التسليم فوري</b> بعد إتمام الدفع عبر Binance Pay!

👇 <b>اختر منتجك أدناه، وابدأ طلبك الآن:</b>"""

def get_main_menu_markup():
    markup = InlineKeyboardMarkup(row_width=2)
    btns = []
    for k, info in PRODUCTS_INFO.items():
        stock_list = STOCK_DATABASE.get(k, [])
        if len(stock_list) == 0:
            btns.append(InlineKeyboardButton(f"❌ {info['name']}", callback_data=f"sold_out_{k}"))
        else:
            btns.append(InlineKeyboardButton(f"🟢 {info['name']} · ${info['price']}", callback_data=f"buy_{k}"))
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
    
    if data.startswith("admin_approve_"):
        order_key = data.replace("admin_approve_", "")
        if order_key in PENDING_ORDERS:
            order_info = PENDING_ORDERS.pop(order_key)
            u_chat_id = order_info["chat_id"]
            prod_key = order_info["prod_key"]
            p_name = PRODUCTS_INFO[prod_key]["name"]
            
            if len(STOCK_DATABASE.get(prod_key, [])) > 0:
                item = STOCK_DATABASE[prod_key].pop(0)
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
                
                success_text = f"""🎉 <b>تم تأكيد عملية الدفع بنجاح!</b>

📦 بيانات حسابك لمنتج <b>{p_name}</b>:
<code>{item}</code>

📜 تم حفظ طلبك في (سجل مشترياتي).
شكراً لتعاملك مع <b>Pixora Store</b> 💚"""
                bot.send_message(u_chat_id, success_text, parse_mode="HTML")
                bot.edit_message_text(f"✅ تم تأكيد وتسليم طلب ({p_name}) للعميل بنجاح.", chat_id, msg_id)
            else:
                bot.send_message(u_chat_id, f"⚠️ نفدت الكمية لهذا المنتج ({p_name})، تواصل مع الدعم الفني.")
                bot.edit_message_text("⚠️ المخزون فارغ!", chat_id, msg_id)
        else:
            bot.answer_callback_query(call.id, "تم اتخاذ إجراء مسبقاً.", show_alert=True)
        return

    elif data.startswith("admin_reject_"):
        order_key = data.replace("admin_reject_", "")
        if order_key in PENDING_ORDERS:
            order_info = PENDING_ORDERS.pop(order_key)
            u_chat_id = order_info["chat_id"]
            bot.send_message(u_chat_id, "❌ تعذر تأكيد عملية التحويل. يرجى التواصل مع الدعم الفني.")
            bot.edit_message_text("❌ تم رفض الطلب.", chat_id, msg_id)
        else:
            bot.answer_callback_query(call.id, "تم اتخاذ إجراء مسبقاً.", show_alert=True)
        return

    if data.startswith("sold_out_"):
        bot.answer_callback_query(call.id, "❌ عذراً، هذا المنتج غير متوفر في المخزن حالياً!", show_alert=True)
        
    elif data.startswith("buy_"):
        prod_key = data.replace("buy_", "")
        if prod_key in PRODUCTS_INFO:
            stock_list = STOCK_DATABASE.get(prod_key, [])
            stock_len = len(stock_list)
            if stock_len == 0:
                bot.answer_callback_query(call.id, "❌ عذراً، نفدت كمية هذا المنتج للتو!", show_alert=True)
                return
            bot.answer_callback_query(call.id)
            USER_SELECTED_PRODUCT[chat_id] = prod_key
            info = PRODUCTS_INFO[prod_key]
            markup = InlineKeyboardMarkup(row_width=1)
            markup.add(InlineKeyboardButton("🪙 إتمام الشراء / الدفع الفوري", callback_data=f"pay_steps_{prod_key}"))
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
        markup.add(InlineKeyboardButton("🔙 رجوع للمنتج", callback_data=f"buy_{prod_key}"), InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
        
        pay_msg = f"""🪙 <b>خطوات الدفع عبر Binance Pay:</b>

1️⃣ حول مبلغ (<code>{info['price']} USDT</code>) إلى Binance ID: <code>{BINANCE_ID}</code>

2️⃣ أرسل <b>رقم العملية (Order ID)</b> أو صورة الإشعار هنا في الشات لتأكيد طلبك واستلام حسابك فوراً!"""
        
        safe_delete_message(chat_id, msg_id)
        bot.send_message(chat_id, pay_msg, reply_markup=markup, parse_mode="HTML")
        
    elif data == "show_payments":
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
        pay_text = f"🪙 <b>معلومات الدفع في متجر Pixora Store:</b>\n\nBinance Pay ID: <code>{BINANCE_ID}</code>\n\nاختر منتجك أولاً ثم أرسل إثبات الدفع بعد التحويل."
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
                history_text += f"{idx}️⃣ <b>المنتج:</b> {order['product']}\n🔑 <b>البيانات:</b> <code>{order['item']}</code>\n🆔 <b>العملية:</b> <code>{order['order_id']}</code>\n📅 <b>الوقت:</b> {order['time']}\n------------------------\n"
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
        "chat
