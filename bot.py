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

if not BOT_TOKEN or ":" not in BOT_TOKEN:
    raise ValueError("⚠️ خطأ: متغير البيئة BOT_TOKEN غير موجود أو صيغته خاطئة في لوحة تحكم Render!")

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

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

# جلب المنتجات وإضافة هامش ربح 20% تلقائياً
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
                
                # سعر التاجر الأساسي
                raw_price = float(item.get("price", 1.0))
                # إضافة هامش ربح 20% وتقريب الناتج لرقمين عشريين
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

WELCOME_TEXT = (
    "🔥 **أهلاً بك في متجر Pixora Store الرقمي الأول!** 🚀\n\n"
    "⚡ *نوفر لك أقوى الحسابات والاشتراكات الرقمية المدفوعة بأفضل الأسعار وأعلى ضمان رسمي.*\n"
    "💎 **التسليم فوري** بعد إتمام الدفع عبر Binance Pay!\n\n"
    "👇 **اختر منتجك أدناه، وابدأ تطوير أعمالك أو أدواتك الآن:**"
)

def get_main_menu_markup():
    markup = InlineKeyboardMarkup()
    products_info = fetch_supplier_products()
    
    if not products_info:
        markup.add(InlineKeyboardButton("⚠️ جارِ تحديث المنتجات من المزود...", callback_data="main_menu"))
        return markup

    in_stock_btns = []
    for k, info in products_info.items():
        clean_name = info['name'].replace("🔴", "").replace("🟢", "").replace("🎞️", "").replace("💠", "").strip()
        if info['stock'] > 0:
            in_stock_btns.append(InlineKeyboardButton(f"✅ {clean_name} · ${info['price']}", callback_data="buy_" + k))
        else:
            in_stock_btns.append(InlineKeyboardButton(f"❌ {clean_name} (نفد)", callback_data="sold_out_" + k))
    
    for i in range(0, len(in_stock_btns), 2):
        if i + 1 < len(in_stock_btns):
            markup.row(in_stock_btns[i], in_stock_btns[i+1])
        else:
            markup.row(in_stock_btns[i])

    markup.row(
        InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"),
        InlineKeyboardButton("📜 سجل مشترياتي", callback_data="my_orders")
    )
    markup.row(
        InlineKeyboardButton("🪙 Binance Pay", callback_data="show_payments"),
        InlineKeyboardButton("🛠️ الدعم الفني", url=SUPPORT_WHATSAPP)
    )
    return markup

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=get_main_menu_markup(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    data = call.data
    
    products_info = fetch_supplier_products()

    if data.startswith("admin_approve_"):
        token = data.replace("admin_approve_", "")
        if token in PENDING_ORDERS:
            o = PENDING_ORDERS.pop(token)
            u_id, p_key = o["chat_id"], o["prod_key"]
            p_info = products_info.get(p_key, {"name": "منتج رقمي", "price": 1.0})
            p_name = p_info["name"]
            
            item_data = "بيانات الحساب المسلمة من الموزع الآلي - تم التحقق بنجاح"
            
            ords = load_orders()
            ords.setdefault(str(u_id), []).append({
                "product": p_name,
                "item": item_data,
                "order_id": o["order_id"],
                "time": time.strftime("%Y-%m-%d %H:%M:%S")
            })
            save_orders(ords)
            msg = (
                f"🎉 <b>تم تأكيد الدفع وتسليم طلبك بنجاح!</b>\n\n"
                f"📦 بيانات حسابك لمنتج <b>{p_name}</b>:\n"
                f"<code>{item_data}</code>\n\n"
                f"📜 تم حفظ طلبك في (سجل مشترياتي).\n\n"
                f"شكراً لثقتك بمتجر <b>Pixora Store</b> 💚"
            )
            bot.send_message(u_id, msg, parse_mode="HTML")
            bot.edit_message_text(f"✅ تم تسليم {p_name} للعميل بنجاح.", chat_id, msg_id)
        else:
            bot.answer_callback_query(call.id, "تم اتخاذ إجراء مسبقاً على هذا الطلب.", show_alert=True)
        return

    elif data.startswith("admin_reject_"):
        token = data.replace("admin_reject_", "")
        if token in PENDING_ORDERS:
            o = PENDING_ORDERS.pop(token)
            bot.send_message(o["chat_id"], "❌ تعذر تأكيد عملية التحويل. يرجى التواصل مع الدعم الفني للتأكد من المعاملة.")
            bot.edit_message_text("❌ تم رفض الطلب.", chat_id, msg_id)
        else:
            bot.answer_callback_query(call.id, "تم اتخاذ إجراء مسبقاً.", show_alert=True)
        return

    if data.startswith("sold_out_"):
        bot.answer_callback_query(call.id, "❌ عذراً، هذا المنتج غير متوفر في المخزن حالياً!", show_alert=True)
        
    elif data.startswith("buy_"):
        prod_key = data.replace("buy_", "")
        if prod_key in products_info:
            info = products_info[prod_key]
            if info['stock'] <= 0:
                bot.answer_callback_query(call.id, "❌ عذراً، نفدت كمية هذا المنتج للتو!", show_alert=True)
                return
            bot.answer_callback_query(call.id)
            USER_SELECTED_PRODUCT[chat_id] = prod_key
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🪙 إتمام الشراء / الدفع الفوري", callback_data="pay_steps_" + prod_key))
            markup.row(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"), InlineKeyboardButton("🛠️ الدعم الفني", url=SUPPORT_WHATSAPP))
            msg_text = f"🏷️ **{info['name']}**\n💰 **Price:** `${info['price']}`\n\n📦 **Stock:** `{info['stock']}`\n📰 **Description:**\n\n{info['description']}"
            
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, msg_text, reply_markup=markup, parse_mode="Markdown")
            
    elif data.startswith("pay_steps_"):
        prod_key = data.replace("pay_steps_", "")
        info = products_info.get(prod_key, {"price": 1.0})
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("🔙 رجوع للمنتج", callback_data="buy_" + prod_key), InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
        pay_msg = f"🪙 **خطوات الدفع الفوري عبر Binance Pay:**\n\n1️⃣ حول مبلغ (`{info['price']} USDT`) إلى Binance ID: `{BINANCE_ID}`\n\n2️⃣ أرسل **رقم العملية (Order ID)** أو صورة إشعار التحويل هنا في الشات لتأكيد طلبك فوراً!"
        
        safe_delete_message(chat_id, msg_id)
        bot.send_message(chat_id, pay_msg, reply_markup=markup, parse_mode="Markdown")
        
    elif data == "show_payments":
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
        pay_text = f"🪙 **معلومات الدفع في متجر Pixora Store:**\n\nBinance Pay ID: `{BINANCE_ID}`\n\nاختر منتجك أولاً من القائمة الرئيسية ثم أرسل إثبات الدفع بعد التحويل."
        
        safe_delete_message(chat_id, msg_id)
        bot.send_message(chat_id, pay_text, reply_markup=markup, parse_mode="Markdown")

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
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
        
        safe_delete_message(chat_id, msg_id)
        bot.send_message(chat_id, history_text, reply_markup=markup, parse_mode="HTML")
        
    elif data == "main_menu":
        bot.answer_callback_query(call.id)
        USER_SELECTED_PRODUCT.pop(chat_id, None)
        safe_delete_message(chat_id, msg_id)
        bot.send_message(chat_id, WELCOME_TEXT, reply_markup=get_main_menu_markup(), parse_mode="Markdown")

@bot.message_handler(content_types=['text', 'photo'])
def handle_incoming(message):
    chat_id = message.chat.id
    if message.content_type == 'text' and message.text.startswith('/'):
        return

    if chat_id not in USER_SELECTED_PRODUCT:
        bot.send_message(chat_id, "⚠️ يرجى اختيار المنتج أولاً من القائمة الرئيسية (/start) قبل إرسال بيانات الدفع.")
        return

    prod_key = USER_SELECTED_PRODUCT[chat_id]
    products_info = fetch_supplier_products()
    info = products_info.get(prod_key, {"name": "منتج رقمي", "price": 1.0})

    order_id_input = message.text.strip() if message.content_type == 'text' else "صورة إيصال التحويل"
    token = f"{chat_id}_{int(time.time())}"

    PENDING_ORDERS[token] = {
        "chat_id": chat_id,
        "prod_key": prod_key,
        "order_id": order_id_input
    }
    USER_SELECTED_PRODUCT.pop(chat_id, None)
    
    bot.send_message(chat_id, "⏳ <b>تم استلام بيانات التحويل بنجاح!</b>\nجاري مراجعة الطلب وتسليم بيانات حسابك فور التأكيد...", parse_mode="HTML")

    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("✅ تأكيد وتسليم الطلب", callback_data=f"admin_approve_{token}"),
        InlineKeyboardButton("❌
