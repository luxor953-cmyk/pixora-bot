import os
import time
import sqlite3
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request

# --- الإعدادات والمتغيرات البيئية ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
# تأكد من وضع Telegram User ID الصحيح الخاص بك (رقمي فقط لحسابك الشخصي)
ADMIN_ID = int(os.environ.get("ADMIN_ID", "1004439571098"))
BINANCE_ID = os.environ.get("BINANCE_ID", "957483337")
RENDER_URL = os.environ.get("RENDER_URL", "https://pixora-bot-1.onrender.com").strip().rstrip('/')
SUPPORT_WHATSAPP = "https://wa.me/213555668244"

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
app = Flask(__name__)

# --- تهيئة وتجهيز قاعدة البيانات SQLite ---
DB_FILE = "pixora_store.db"

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # جدول المنتجات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                key TEXT PRIMARY KEY,
                name TEXT,
                category TEXT,
                price REAL,
                description TEXT
            )
        ''')
        # جدول المخزون (الأكواد / الحسابات / الروابط)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prod_key TEXT,
                item_data TEXT,
                is_used INTEGER DEFAULT 0
            )
        ''')
        # جدول الطلبات المكتملة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                user_id INTEGER,
                prod_key TEXT,
                prod_name TEXT,
                item_delivered TEXT,
                payment_proof TEXT,
                status TEXT,
                created_at TEXT
            )
        ''')
        # جدول الطلبات المعلقة (لتبقى محفوظة حتى لو تم عمل ريستارت للسيرفر)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_orders (
                token TEXT PRIMARY KEY,
                user_id INTEGER,
                user_name TEXT,
                prod_key TEXT,
                proof TEXT,
                created_at REAL
            )
        ''')
        conn.commit()

init_db()

# المنتجات والتصنيفات الأساسية
CATEGORIES = {
    "ai": "🤖 أدوات الذكاء الاصطناعي",
    "design": "🎨 التصميم والمونتاج",
    "vpn": "🛡️ برامج الحماية والـ VPN",
    "office_edu": "📚 التعليم والأعمال"
}

RAW_PRODUCTS = [
    ("capcut", "CapCut Pro (30 Days)", "design", 1.3, "اشتراك CapCut Pro رسمي لمدة 30 يوماً:\n• إزالة العلامة المائية وتصدير 4K.\n• وصول لجميع القوالب والمؤثرات المدفوعة."),
    ("gemini", "Google Gemini Advanced (18M)", "ai", 3.0, "خطة Gemini Advanced مع 2TB سحابية لمدة 18 شهراً."),
    ("office", "Microsoft Office 365 Pro", "office_edu", 0.30, "حساب رسمي مفعل لـ 5 أجهزة مع 1TB مساحة OneDrive."),
    ("autodesk", "Autodesk All Apps (1 Year)", "design", 3.0, "اشتراك رسمي لسنة كاملة يشمل AutoCAD و 3ds Max وغيرها."),
    ("canva", "Canva Pro Invite (1 Year)", "design", 4.0, "تفعيل Canva Pro رسمي على إيميلك الشخصي لمدة سنة."),
    ("chatgpt", "ChatGPT Plus", "ai", 3.0, "وصول لحساب ChatGPT Plus الرسمي."),
    ("nordvpn", "NordVPN Premium", "vpn", 2.0, "حساب NordVPN سريع ومحمي."),
    ("coursera", "Coursera Plus", "office_edu", 2.0, "وصول للكورسات والشهادات المعتمدة.")
]

def seed_default_data():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        for k, name, cat, price, desc in RAW_PRODUCTS:
            c.execute("INSERT OR IGNORE INTO products VALUES (?, ?, ?, ?, ?)", (k, name, cat, price, desc))
        
        # بذور أولية للمخزون للتجربة
        sample_stock = [
            ("capcut", "CapCut_Account: user1@pixoras.com / Pass123"),
            ("gemini", "https://g.co/gemini/share/sample_token_123"),
            ("office", "Office365: user_test@o365.com / Pass#2026"),
            ("autodesk", "AUTODESK-KEY-2026-XYZ"),
            ("canva", "https://www.canva.com/brand/join?inv=sample_key")
        ]
        for pkey, item in sample_stock:
            c.execute("SELECT COUNT(*) FROM stock WHERE prod_key = ? AND item_data = ?", (pkey, item))
            if c.fetchone()[0] == 0:
                c.execute("INSERT INTO stock (prod_key, item_data) VALUES (?, ?)", (pkey, item))
        conn.commit()

seed_default_data()

# --- دوال مساعدة لقاعدة البيانات ---
def get_stock_count(prod_key):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM stock WHERE prod_key = ? AND is_used = 0", (prod_key,))
        return c.fetchone()[0]

def get_product(prod_key):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT key, name, category, price, description FROM products WHERE key = ?", (prod_key,))
        row = c.fetchone()
        if row:
            return {"key": row[0], "name": row[1], "category": row[2], "price": row[3], "description": row[4]}
        return None

# حالة اختيار المستخدم المؤقتة قبل الدفع
USER_SELECTION = {}

# --- لوحات المفاتيح (Keyboards) ---
def get_categories_markup():
    markup = InlineKeyboardMarkup(row_width=2)
    btns = [InlineKeyboardButton(text, callback_data=f"cat_{cat_key}") for cat_key, text in CATEGORIES.items()]
    markup.add(*btns)
    markup.add(
        InlineKeyboardButton("📜 سجل مشترياتي", callback_data="my_orders"),
        InlineKeyboardButton("🪙 طرق الدفع", callback_data="show_payments")
    )
    markup.add(InlineKeyboardButton("🛠️ الدعم الفني (WhatsApp)", url=SUPPORT_WHATSAPP))
    return markup

def get_category_products_markup(cat_key):
    markup = InlineKeyboardMarkup(row_width=1)
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT key, name, price FROM products WHERE category = ?", (cat_key,))
        products = c.fetchall()
        
    for pkey, name, price in products:
        stock = get_stock_count(pkey)
        status_icon = "🟢" if stock > 0 else "❌"
        btn_text = f"{status_icon} {name} · ${price}"
        callback = f"buy_{pkey}" if stock > 0 else f"sold_out_{pkey}"
        markup.add(InlineKeyboardButton(btn_text, callback_data=callback))
        
    markup.add(InlineKeyboardButton("🔙 رجوع للأقسام", callback_data="main_menu"))
    return markup

# --- أوامر البوت وتفاعلاته ---
WELCOME_TEXT = (
    "🔥 <b>أهلاً بك في متجر Pixora Store الرقمي!</b> 🚀\n\n"
    "⚡ نوفر لك أقوى الحسابات والاشتراكات بأفضل الأسعار وأعلى ضمان.\n"
    "💎 <b>التسليم فوري وتلقائي</b> بعد مراجعة إيصال التحويل عبر Binance Pay!\n\n"
    "👇 <b>اختر القسم الذي يناسبك لتصفح المنتجات:</b>"
)

@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    USER_SELECTION.pop(message.chat.id, None)
    bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=get_categories_markup(), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def on_callback(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    data = call.data

    # 1. القائمة الرئيسية
    if data == "main_menu":
        bot.answer_callback_query(call.id)
        USER_SELECTION.pop(chat_id, None)
        try:
            bot.edit_message_text(WELCOME_TEXT, chat_id, msg_id, reply_markup=get_categories_markup(), parse_mode="HTML")
        except Exception:
            bot.send_message(chat_id, WELCOME_TEXT, reply_markup=get_categories_markup(), parse_mode="HTML")

    # 2. تصفح تصنيف معين
    elif data.startswith("cat_"):
        bot.answer_callback_query(call.id)
        cat_key = data.replace("cat_", "")
        cat_name = CATEGORIES.get(cat_key, "المنتجات")
        markup = get_category_products_markup(cat_key)
        bot.edit_message_text(f"📁 <b>قسم: {cat_name}</b>\nاختر المنتج الذي ترغب بشرائه:", chat_id, msg_id, reply_markup=markup, parse_mode="HTML")

    # 3. منتج غير متوفر
    elif data.startswith("sold_out_"):
        bot.answer_callback_query(call.id, "❌ عذراً، هذا المنتج غير متوفر في المخزن حالياً!", show_alert=True)

    # 4. تفاصيل المنتج وزر الشراء
    elif data.startswith("buy_"):
        prod_key = data.replace("buy_", "")
        prod = get_product(prod_key)
        if not prod:
            bot.answer_callback_query(call.id, "المنتج غير موجود!")
            return
            
        stock = get_stock_count(prod_key)
        if stock == 0:
            bot.answer_callback_query(call.id, "❌ عذراً، نفدت الكمية للتو!", show_alert=True)
            return

        bot.answer_callback_query(call.id)
        USER_SELECTION[chat_id] = prod_key
        
        text = (
            f"🏷️ <b>{prod['name']}</b>\n"
            f"💰 <b>السعر:</b> <code>${prod['price']} USDT</code>\n"
            f"📦 <b>المتوفر بالمخزن:</b> <code>{stock}</code>\n\n"
            f"📝 <b>الوصف:</b>\n{prod['description']}\n\n"
            f"⚡ اضغط بالأسفل للذهاب لخطوات الدفع:"
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🪙 متابعة الدفع عبر Binance Pay", callback_data=f"pay_{prod_key}"))
        markup.add(InlineKeyboardButton("🔙 رجوع للأقسام", callback_data="main_menu"))
        
        bot.edit_message_text(text, chat_id, msg_id, reply_markup=markup, parse_mode="HTML")

    # 5. خطوات الدفع
    elif data.startswith("pay_"):
        prod_key = data.replace("pay_", "")
        prod = get_product(prod_key)
        bot.answer_callback_query(call.id)
        USER_SELECTION[chat_id] = prod_key

        pay_msg = (
            f"🪙 <b>خطوات الدفع عبر Binance Pay:</b>\n\n"
            f"1️⃣ قم بتحويل مبلغ: <b>{prod['price']} USDT</b>\n"
            f"إلى Binance ID الخاص بنا: <code>{BINANCE_ID}</code> (اضغط للنسخ)\n\n"
            f"2️⃣ <b>بعد إتمام التحويل:</b>\n"
            f"أرسل هنا في المحادثة <b>رقم العملية (Order/TxID)</b> أو <b>صورة إشعار التحويل</b> لتأكيد طلبك وتسليمه فوراً."
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 إلغاء والرجوع", callback_data=f"buy_{prod_key}"))
        bot.edit_message_text(pay_msg, chat_id, msg_id, reply_markup=markup, parse_mode="HTML")

    # 6. سجل مشترياتي
    elif data == "my_orders":
        bot.answer_callback_query(call.id)
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("SELECT prod_name, item_delivered, created_at FROM orders WHERE user_id = ?", (chat_id,))
            orders = c.fetchall()

        if not orders:
            history_text = "📜 <b>سجل مشترياتك:</b>\n\nلا توجد عمليات شراء سابقة مسجلة بحسابك."
        else:
            history_text = "📜 <b>سجل مشترياتك السابقة:</b>\n\n"
            for idx, (p_name, item, created_at) in enumerate(orders, 1):
                history_text += (
                    f"{idx}️⃣ <b>المنتج:</b> {p_name}\n"
                    f"🔑 <b>البيانات:</b> <code>{item}</code>\n"
                    f"📅 <b>التاريخ:</b> {created_at}\n"
                    f"------------------------\n"
                )

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
        bot.edit_message_text(history_text, chat_id, msg_id, reply_markup=markup, parse_mode="HTML")

    # 7. استعراض الدفع
    elif data == "show_payments":
        bot.answer_callback_query(call.id)
        pay_info = (
            f"🪙 <b>بيانات الدفع المعتمدة:</b>\n\n"
            f"• <b>Binance Pay ID:</b> <code>{BINANCE_ID}</code>\n"
            f"• العملة المقبولة: USDT\n\n"
            f"اختر المنتج من القائمة أولاً ثم أرسل إثبات الدفع."
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
        bot.edit_message_text(pay_info, chat_id, msg_id, reply_markup=markup, parse_mode="HTML")

    # 8. موافقة الأدمن على الطلب (Admin Approve)
    elif data.startswith("admin_approve_"):
        token = data.replace("admin_approve_", "")
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("SELECT user_id, prod_key, proof FROM pending_orders WHERE token = ?", (token,))
            row = c.fetchone()
            
            if not row:
                bot.answer_callback_query(call.id, "تمت معالجة هذا الطلب بالفعل سابقاً!", show_alert=True)
                return
                
            u_id, p_key, proof = row
            prod = get_product(p_key)

            # جلب عنصر من المخزون
            c.execute("SELECT id, item_data FROM stock WHERE prod_key = ? AND is_used = 0 LIMIT 1", (p_key,))
            stock_row = c.fetchone()

            if stock_row:
                stock_id, item_data = stock_row
                c.execute("UPDATE stock SET is_used = 1 WHERE id = ?", (stock_id,))
                
                # حفظ في سجل المبيعات
                c.execute(
                    "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (token, u_id, p_key, prod['name'], item_data, proof, "completed", time.strftime("%Y-%m-%d %H:%M:%S"))
                )
                c.execute("DELETE FROM pending_orders WHERE token = ?", (token,))
                conn.commit()

                # إرسال البيانات للعميل
                success_msg = (
                    f"🎉 <b>تم تأكيد الدفع بنجاح!</b>\n\n"
                    f"📦 بيانات حسابك لمنتج <b>{prod['name']}</b>:\n"
                    f"<code>{item_data}</code>\n\n"
                    f"📜 يمكنك الوصول لبياناتك دائماً عبر (سجل مشترياتي).\n"
                    f"شكراً لتعاملك مع <b>Pixora Store</b> 💚"
                )
                bot.send_message(u_id, success_msg, parse_mode="HTML")
                bot.edit_message_text(f"✅ تم تسليم {prod['name']} للعميل ({u_id}) بنجاح.", chat_id, msg_id)
            else:
                bot.send_message(u_id, f"⚠️ عذراً! نفد المخزون لمنتج {prod['name']}. سيقوم الدعم بمراسلتك في أقرب وقت.")
                bot.edit_message_text("⚠️ المخزون فارغ لهذا المنتج!", chat_id, msg_id)

    # 9. رفض طلب الشراء (Admin Reject)
    elif data.startswith("admin_reject_"):
        token = data.replace("admin_reject_", "")
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("SELECT user_id FROM pending_orders WHERE token = ?", (token,))
            row = c.fetchone()
            if row:
                u_id = row[0]
                c.execute("DELETE FROM pending_orders WHERE token = ?", (token,))
                conn.commit()
                bot.send_message(u_id, "❌ تعذر تأكيد عملية التحويل. يرجى مراجعة الدعم الفني وتزويدهم بالمعاملة.")
                bot.edit_message_text("❌ تم رفض الطلب.", chat_id, msg_id)
            else:
                bot.answer_callback_query(call.id, "تم اتخاذ إجراء مسبقاً.", show_alert=True)

# --- استقبال رسائل التحويل والصور من المشتري ---
@bot.message_handler(content_types=['text', 'photo'])
def handle_payment_submission(message):
    chat_id = message.chat.id
    if message.content_type == 'text' and message.text.startswith('/'):
        return

    if chat_id not in USER_SELECTION:
        bot.send_message(chat_id, "⚠️ يرجى اختيار المنتج الذي ترغب بشرائه أولاً من القائمة /start")
        return

    prod_key = USER_SELECTION.pop(chat_id)
    prod = get_product(prod_key)
    
    if get_stock_count(prod_key) == 0:
        bot.send_message(chat_id, "⚠️ عذراً، نفدت كمية هذا المنتج حالياً!")
        return

    proof_data = message.text.strip() if message.content_type == 'text' else "صورة إيصال تحويل"
    token = f"{chat_id}_{int(time.time())}"
    user_name = message.from_user.first_name or "عميل"
    user_handle = f"@{message.from_user.username}" if message.from_user.username else f"ID: {chat_id}"

    # حفظ الطلب في قاعدة البيانات كطلب معلق
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO pending_orders VALUES (?, ?, ?, ?, ?, ?)", 
                  (token, chat_id, user_name, prod_key, proof_data, time.time()))
        conn.commit()

    bot.send_message(chat_id, "⏳ <b>تم استلام بيانات التحويل بنجاح!</b>\nجاري مراجعة الطلب وسيتم تسليم الحساب لك هنا فوراً.", parse_mode="HTML")

    # إشعار المدير
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✅ تأكيد وتسليم", callback_data=f"admin_approve_{token}"),
        InlineKeyboardButton("❌ رفض", callback_data=f"admin_reject_{token}")
    )
    admin_msg = (
        f"🔔 <b>طلب شراء جديد!</b>\n\n"
        f"👤 <b>العميل:</b> {user_name} ({user_handle})\n"
        f"🛍️ <b>المنتج:</b> {prod['name']}\n"
        f"💰 <b>المبلغ:</b> {prod['price']} USDT\n"
        f"🆔 <b>الإثبات:</b> <code>{proof_data}</code>\n\n"
        f"تحقق من حساب بينانس ثم اختر الإجراء:"
    )

    try:
        if message.content_type == 'photo':
            bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=admin_msg, reply_markup=markup, parse_mode="HTML")
        else:
            bot.send_message(ADMIN_ID, admin_msg, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        print("خطأ في إشعار المدير:", e)

# --- إعدادات Flask و Webhook للعمل التلقائي على Render ---
@app.route('/')
def home():
    return "Pixora Bot is Running Smoothly with SQLite!", 200

@app.route('/webhook', methods=['POST'])
def receive_update():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    return "Forbidden", 403

def setup_webhook_once():
    if BOT_TOKEN and RENDER_URL:
        try:
            bot.remove_webhook()
            time.sleep(1)
            target = f"{RENDER_URL}/webhook"
            res = bot.set_webhook(url=target)
            print(f"Webhook connected to: {target} (Status: {res})")
        except Exception as e:
            print("Webhook setup error:", e)

# يتم تشغيل الويب هوك حتى لو اشتغل الخادم عبر Gunicorn
if RENDER_URL and BOT_TOKEN:
    setup_webhook_once()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
