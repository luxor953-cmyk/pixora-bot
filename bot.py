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

if not BOT_TOKEN or ":" not in BOT_TOKEN:
    raise ValueError("⚠️ خطأ: متغير البيئة BOT_TOKEN غير موجود أو صيغته خاطئة في لوحة تحكم Render!")

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# قائمة المنتجات الـ 31 الكاملة
RAW_PRODUCTS = [
    (
        "capcut",
        "🎞️ CapCut Pro 1 Month FW",
        1.47,
        "📰 Description:\n"
        "- Full 30 days private Pro Team account.\n"
        "- Maximum 2 devices , with full warranty.\n"
        "- Stable Account full 30 days (no 7days renew ).\n"
        "- Login to mobile App first next to laptop (desktop App no web) via QR code ."
    ),
    (
        "gemini",
        "💠 Gemini Ai · Gemini Pro 18 Months Link",
        3.0,
        "Description\n"
        "⚡ 18 Months Plan\n"
        "⚡ 5TB cloud storage included\n"
        "⚡ You can add 5 users\n"
        "⚡ No Shared\n"
        "⚡ 100% Private \n"
        "⚡ NO NEED ANY CARD\n"
        "⚡ The link is delivered via a verified custom domain and redirects to the official Google Gemini website for activation.\n"
        "🔥 Works in any country, no verification required\n"
        "🚫 Non Warranty After 1H of Delivery\n\n"
        "⚡ 100% Genuine Gemini AI Pro Subscription Activated on Your Own Gmail."
    ),
    (
        "office",
        "📱 Microsoft 365 · Microsoft Office 365 1Tb 5 Devices Lifetime",
        1.0,
        "Description\n"
        "✔️ Microsoft 365 Plus – 100GB/1000GB | 5 Devices\n\n"
        "📱 Full access to Microsoft Office apps.\n\n"
        "✔️ Format : Email | Password\n\n"
        "✔️ Word, Excel, PowerPoint, Outlook & more\n"
        "✔️ Activate on up to 5 devices\n"
        "✔️ Compatible with Windows, Mac, Android & iOS\n"
        "✔️ 100GB/1000GB OneDrive cloud storage\n"
        "✔️ Automatic updates & premium features\n"
        "✔️ Instant & automatic delivery\n\n"
        "🛡 2-Year Warranty & Activation Support\n\n"
        "⚠️ Important Notes :\n"
        "- Keep your login credentials safe, forgotten password in not covered by Warranty.\n"
        "- OneDrive Storage is not covered by Warranty always keep backup for your files."
    ),
    (
        "autodesk",
        "🔺 Autodesk all Apps 1 Year",
        0.60,
        "📰 Description:\n"
        "🎓 1 year subscription to Autodesk Student.\n"
        "📧 Invitation in customer's email to Autodesk.\n"
        "💻 Almost all apps are included (3ds Max, AutoCAD, Fusion 360, Maya, Revit...)\n"
        "💬 If you want to add a specific app (message us)"
    ),
    (
        "canva",
        "🎨 Canva Education Panel — Quick Setup Guide",
        4.0,
        "🚀 Canva Education Panel — Quick Setup Guide 🎓\n"
        "1️⃣ Secure the Email ✉️\n"
        "Log in to the provided Outlook account and add your personal email or phone number as a recovery method 🔒 (do not change the original account details).\n"
        "2️⃣ First Login 🕵️‍♂️\n"
        "Open an Incognito / Private window and sign in using the main Canva account 🔑.\n"
        "3️⃣ Add Your Personal Account 👨‍🏫\n"
        "Go to Team Settings ⚙️ → Members 👥 → Invite Members, and invite your personal Canva email as a Teacher / Co-Teacher 📩.\n"
        "4️⃣ Log Out & Manage 🎛\n"
        "Accept the invite from your personal email ✅, log out of the main account completely 🚪, and use your personal account to manage the panel (add/remove members) from now on 💻.\n"
        "⚠️ Important Reminders 🛑\n"
        "❌ Do not delete the main account or change the team/panel name.\n"
        "📈 Add members gradually to keep the account safe.\n"
        "🌍 Keep your login location/IP consistent (avoid switching VPNs frequently)."
    ),
    ("adobe", "🔴 Adobe", 2.5, "Full Adobe Creative Cloud access."),
    ("avira", "🔴 Avira", 2.0, "Premium Antivirus & Security subscription."),
    ("chatgpt", "🔴 ChatGPT", 3.0, "ChatGPT Plus account access."),
    ("coursera", "🔴 Coursera", 2.0, "Coursera subscription for certificates."),
    ("duolingo", "🔴 Duolingo", 0.75, "Duolingo Super 12 Months."),
    ("elevenlabs", "🔴 ElevenLabs", 3.5, "AI Voice Generator premium plan."),
    ("expressvpn", "🔴 ExpressVPN", 2.5, "High-speed secure VPN subscription."),
    ("figma", "🔴 Figma", 2.0, "Figma Pro team access for designers."),
    ("framer", "🔴 Framer", 2.0, "Framer Pro web building subscription."),
    ("gamma", "🔴 Gamma", 2.0, "AI presentations and docs generator."),
    ("grok", "🔴 Grok", 2.5, "xAI Grok premium access."),
    ("hmavpn", "🔴 HMA VPN", 0.55, "HideMyAss VPN secure access."),
    ("jetbrain", "🔴 JetBrain", 3.0, "All Products Pack license access."),
    ("kaspersky", "🔴 Kaspersky", 2.0, "Kaspersky Total Security license."),
    ("linkedin", "🔴 LinkedIn", 3.0, "LinkedIn Premium Career/Business access."),
    ("lovable", "🔴 Lovable", 2.5, "Full stack AI web app builder."),
    ("muse", "🔴 Muse", 2.0, "Muse AI premium tools access."),
    ("notion", "🔴 Notion", 2.0, "Notion Pro workspace subscription."),
    ("youtube", "🔴 YouTube", 2.0, "YouTube Premium ad-free subscription."),
    ("ilovepdf", "🔴 iLovePdf", 1.5, "iLovePDF Premium tools access."),
    ("api", "🔴 API", 5.0, "High limit developer API keys."),
    ("grammarly", "🔴 Grammarly", 2.0, "Grammarly Premium writing assistant."),
    ("nordvpn", "🔴 Nord Vpn", 2.0, "NordVPN secure high-speed servers."),
    ("scribd", "🔴 Scribd", 2.0, "Scribd ebooks and audiobooks access."),
    ("wispr", "🔴 Wispr", 2.0, "Wispr Flow voice dictation tool."),
    ("udemy", "🔴 Udemy", 2.0, "Premium courses access plan.")
]

PRODUCTS_INFO = {k: {"name": n, "price": p, "description": d} for k, n, p, d in RAW_PRODUCTS}

# ضبط المخزون: أول منتجين (CapCut و Gemini) رصيدهم 0 (فارغ)، والباقي متوفر
STOCK_DATABASE = {}
for idx, (k, _, _, _) in enumerate(RAW_PRODUCTS):
    if idx in [0, 1]:  
        STOCK_DATABASE[k] = []
    else:
        STOCK_DATABASE[k] = [f"بيانات اشتراك - مفعل وفوري"]

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

WELCOME_TEXT = (
    "🔥 **أهلاً بك في متجر Pixora Store الرقمي الأول!** 🚀\n\n"
    "⚡ *نوفر لك أقوى الحسابات والاشتراكات الرقمية المدفوعة بأفضل الأسعار وأعلى ضمان رسمي.*\n"
    "💎 **التسليم فوري** بعد إتمام الدفع عبر Binance Pay!\n\n"
    "👇 **اختر منتجك أدناه، وابدأ تطوير أعمالك أو أدواتك الآن:**"
)

def get_main_menu_markup():
    markup = InlineKeyboardMarkup()
    in_stock_btns = []
    for k, info in PRODUCTS_INFO.items():
        clean_name = info['name'].replace("🔴", "").replace("🟢", "").replace("🎞️", "").replace("💠", "").replace("📱", "").replace("🔺", "").replace("🎨", "").strip()
        if len(STOCK_DATABASE.get(k, [])) > 0:
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
        InlineKeyboardButton("🛍️ المنتجات", callback_data="main_menu")
    )
    markup.row(
        InlineKeyboardButton("📜 سجل مشترياتي", callback_data="my_orders"),
        InlineKeyboardButton("🪙 Binance Pay", callback_data="show_payments")
    )
    markup.add(
        InlineKeyboardButton("🛠️ الدعم الفني (WhatsApp)", url=SUPPORT_WHATSAPP)
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
                msg = (
                    f"🎉 <b>تم تأكيد الدفع وتسليم طلبك بنجاح!</b>\n\n"
                    f"📦 بيانات حسابك لمنتج <b>{p_name}</b>:\n"
                    f"<code>{item}</code>\n\n"
                    f"📜 تم حفظ طلبك في (سجل مشترياتي).\n\n"
                    f"شكراً لثقتك بمتجر <b>Pixora Store</b> 💚"
                )
                bot.send_message(u_id, msg, parse_mode="HTML")
                bot.edit_message_text(f"✅ تم تسليم {p_name} للعميل بنجاح.", chat_id, msg_id)
            else:
                bot.send_message(u_id, f"⚠️ نفدت الكمية لمنتج {p_name}، يرجى مراجعة الدعم الفني.")
                bot.edit_message_text("⚠️ المخزون فارغ!", chat_id, msg_id)
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
        if prod_key in PRODUCTS_INFO:
            stock_len = len(STOCK_DATABASE.get(prod_key, []))
            if stock_len == 0:
                bot.answer_callback_query(call.id, "❌ عذراً، نفدت كمية هذا المنتج للتو!", show_alert=True)
                return
            bot.answer_callback_query(call.id)
            USER_SELECTED_PRODUCT[chat_id] = prod_key
            info = PRODUCTS_INFO[prod_key]
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🪙 إتمام الشراء / الدفع الفوري", callback_data="pay_steps_" + prod_key))
            markup.row(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"), InlineKeyboardButton("🛠️ الدعم الفني", url=SUPPORT_WHATSAPP))
            msg_text = f"🏷️ **{info['name']}**\n💰 **Price:** `${info['price']}`\n\n📦 **Stock:** `{stock_len}`\n📰 **Description:**\n\n{info['description']}\n\n🛍️ **Buy Quantity:** 1"
            
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, msg_text, reply_markup=markup, parse_mode="Markdown")
            
    elif data.startswith("pay_steps_"):
        prod_key = data.replace("pay_steps_", "")
        info = PRODUCTS_INFO[prod_key]
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
    info = PRODUCTS_INFO[prod_key]
    
    if len(STOCK_DATABASE.get(prod_key, [])) == 0:
        bot.send
