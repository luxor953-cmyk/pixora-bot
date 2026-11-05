import os
import time
import sqlite3
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request

# --- الإعدادات ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
# ضع Telegram ID الرقمي الحقيقي لحسابك (تأكد منه عبر @userinfobot)
ADMIN_ID = int(os.environ.get("ADMIN_ID", "1004439571098"))
BINANCE_ID = os.environ.get("BINANCE_ID", "957483337")
RENDER_URL = os.environ.get("RENDER_URL", "https://pixora-bot-1.onrender.com").strip().rstrip('/')
SUPPORT_WHATSAPP = "https://wa.me/213555668244"

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
app = Flask(__name__)
DB_FILE = "pixora_store.db"

# صورة افتراضية في حال لم تتوفر صورة لمنتج معين
DEFAULT_IMAGE = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&q=80"

# --- تجهيز قاعدة البيانات الدائمة ---
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        # جدول المنتجات مع دعم رابط الصورة (image_url)
        c.execute('''
            CREATE TABLE IF NOT EXISTS products (
                key TEXT PRIMARY KEY,
                name TEXT,
                category TEXT,
                price REAL,
                description TEXT,
                image_url TEXT
            )
        ''')
        # جدول المخزون
        c.execute('''
            CREATE TABLE IF NOT EXISTS stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prod_key TEXT,
                item_data TEXT,
                is_used INTEGER DEFAULT 0
            )
        ''')
        # جدول المبيعات الناجحة
        c.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                user_id INTEGER,
                prod_key TEXT,
                prod_name TEXT,
                item_delivered TEXT,
                created_at TEXT
            )
        ''')
        # جدول الطلبات المعلقة (محفوظة في الداتابيز لحين موافقة الأدمن)
        c.execute('''
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

# قائمة المنتجات مع صور وشعارات رسمية مباشرة
RAW_PRODUCTS = [
    (
        "capcut", "🎞️ CapCut Pro (30 Days)", "design", 1.3,
        "اشتراك CapCut Pro رسمي لمدة 30 يوماً:\n• إزالة العلامة المائية وتصدير 4K.\n• وصول لجميع المؤثرات والقوالب المدفوعة.\n⚡ التسليم: فوري بعد الدفع.",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Capcut-logo.svg/800px-Capcut-logo.svg.png"
    ),
    (
        "gemini", "💠 Google Gemini Advanced (18M)", "ai", 3.0,
        "خطة Gemini Advanced مع 2TB مساحة سحابية لمدة 18 شهراً:\n• استخدام نموذج Gemini 1.5 Pro.\n• تكامل مع Gmail و Google Drive.",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Google_Gemini_logo.svg/800px-Google_Gemini_logo.svg.png"
    ),
    (
        "office", "🟩 Microsoft Office 365 Pro", "office", 0.30,
        "حساب رسمي مفعل لـ 5 أجهزة (Windows, Mac, Phone):\n• Word, Excel, PowerPoint كاملة.\n• مساحة 1TB سحابية على OneDrive.",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Microsoft_Office_logo_%282019%E2%80%93present%29.svg/800px-Microsoft_Office_logo_%282019%E2%80%93present%29.svg.png"
    ),
    (
        "canva", "🎨 Canva Pro Invite (1 Year)", "design", 4.0,
        "اشتراك Canva Pro رسمي يتم تفعيله على إيميلك الخاص لمدة سنة:\n• ملايين القوالب والخطوط المدفوعة.\n• إزالة الخلفيات بالذكاء الاصطناعي بنقرة واحدة.",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Canva_icon_2021.svg/800px-Canva_icon_2021.svg.png"
    ),
    (
        "chatgpt", "🟢 ChatGPT Plus (1 Month)", "ai", 3.0,
        "حساب ChatGPT Plus مدفوع:\n• استخدام GPT-4o بدون قيود وسرعة فائقة.\n• توليد الصور عبر DALL-E وإنشاء الـ GPTs المخصصة.",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/ChatGPT_logo.svg/800px-ChatGPT_logo.svg.png"
    ),
    (
        "nordvpn", "🛡️ NordVPN (1 Year)", "vpn", 2.0,
        "اشتراك NordVPN عالي السرعة والأمان:\n• فتح المواقع المحجوبة وسيرفرات فائقة السرعة.\n• تشفير تام وحماية الخصوصية.",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/NordVPN_horizontal_logo.svg/800px-NordVPN_horizontal_logo.svg.png"
    )
]

def seed_database():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        for key, name, cat, price, desc, img in RAW_PRODUCTS:
            c.execute('''
                INSERT INTO products (key, name, category, price, description, image_url)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET image_url=excluded.image_url, description=excluded.description
            ''', (key, name, cat, price, desc, img))
            
            # مخزون افتراضي للتجربة لكل منتج
            c.execute("SELECT COUNT(*) FROM stock WHERE prod_key = ?", (key,))
            if c.fetchone()[0] == 0:
                c.execute("INSERT INTO stock (prod_key, item_data) VALUES (?, ?)", 
                          (key, f"Account_{key.upper()}: user_vip@pixoras.com / Pass#2026@Secure"))
        conn.commit()

seed_database()

# دالة مساعدة لجلب تفاصيل المنتج
def get_product(prod_key):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT key, name, category, price, description, image_url FROM products WHERE key = ?", (prod_key,))
        row = c.fetchone()
        if row:
            return {
                "key": row[0], "name": row[1], "category": row[2],
                "price": row[3], "description": row[4], "image_url": row[5] or DEFAULT_IMAGE
            }
    return None

def get_stock_count(prod_key):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM stock WHERE prod_key = ? AND is_used = 0", (prod_key,))
        return c.fetchone()[0]

# تخزين مؤقت لاختيار العميل للمنتج قبل إرسال إيصال الدفع
USER_SELECTION = {}

def get_catalog_markup():
    markup = InlineKeyboardMarkup()
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT key, name, price FROM products")
        products = c.fetchall()

    btns = []
    for key, name, price in products:
        stock = get_stock_count(key)
        icon = "🟢" if stock > 0 else "❌"
        btns.append(InlineKeyboardButton(f"{icon} {name} · ${price}", callback_data=f"view_{key}"))
        
    for i in range(0, len(btns), 2):
        if i + 1 < len(btns):
            markup.row(btns[i], btns[i+1])
        else:
            markup.row(btns[i])

    markup.row(
        InlineKeyboardButton("📜 سجل مشترياتي", callback_data="my_orders"),
        InlineKeyboardButton("🪙 بيانات الدفع", callback_data="show_payments")
    )
    markup.add(InlineKeyboardButton("🛠️ الدعم الفني (WhatsApp)", url=SUPPORT_WHATSAPP))
    return markup

WELCOME_TEXT = (
    "🔥 <b>أهلاً بك في متجر Pixora Store الرقمي!</b> 🚀\n\n"
    "⚡ نوفر لك أقوى الحسابات والاشتراكات الرقمية بأسعار منافسة وتسليم فوري.\n"
    "👇 <b>اختر المنتج الذي ترغب بالاطلاع على تفاصيله وصورته:</b>"
)

@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    USER_SELECTION.pop(message.chat.id, None)
    bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=get_catalog_markup(), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    data = call.data

    # 1. عرض تفاصيل المنتج مع صورته
    if data.startswith("view_"):
        prod_key = data.replace("view_", "")
        prod = get_product(prod_key)
        if not prod:
            bot.answer_callback_query(call.id, "المنتج غير متوفر حالياً!")
            return

        stock = get_stock_count(prod_key)
        bot.answer_callback_query(call.id)
        USER_SELECTION[chat_id] = prod_key

        caption = (
            f"🏷️ <b>{prod['name']}</b>\n"
            f"💰 <b>السعر:</b> <code>${prod['price']} USDT</code>\n"
            f"📦 <b>المتوفر بالمخزن:</b> <code>{stock}</code>\n\n"
            f"📝 <b>التفاصيل والميزات:</b>\n{prod['description']}\n\n"
            f"⚡ <i>اضغط بالأسفل للتحويل والدفع الفوري:</i>"
        )
        markup = InlineKeyboardMarkup()
        if stock > 0:
            markup.add(InlineKeyboardButton("🪙 شراء الآن (Binance Pay)", callback_data=f"pay_{prod_key}"))
        else:
            markup.add(InlineKeyboardButton("❌ نفدت الكمية حالياً", callback_data="sold_out_alert"))
            
        markup.add(InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="back_to_menu"))

        try:
            bot.delete_message(chat_id, msg_id)
        except Exception:
            pass

        # إرسال صورة المنتج مع الكابشن والأزرار
        bot.send_photo(chat_id, prod['image_url'], caption=caption, reply_markup=markup, parse_mode="HTML")

    # 2. خطوات الدفع
    elif data.startswith("pay_"):
        prod_key = data.replace("pay_", "")
        prod = get_product(prod_key)
        bot.answer_callback_query(call.id)
        USER_SELECTION[chat_id] = prod_key

        pay_text = (
            f"🪙 <b>خطوات إتمام الدفع لمنتج: {prod['name']}</b>\n\n"
            f"1️⃣ قم بتحويل مبلغ: <b>{prod['price']} USDT</b>\n"
            f"إلى Binance Pay ID: <code>{BINANCE_ID}</code> (اضغط للنسخ)\n\n"
            f"2️⃣ <b>بعد إتمام التحويل:</b>\n"
            f"أرسل هنا في المحادثة <b>رقم العملية (TxID / Order ID)</b> أو <b>صورة إشعار التحويل</b> لتأكيد طلبك واستلام بياناتك فوراً."
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 رجوع لتفاصيل المنتج", callback_data=f"view_{prod_key}"))
        
        try:
            bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
        bot.send_message(chat_id, pay_text, reply_markup=markup, parse_mode="HTML")

    # 3. الرجوع للقائمة الرئيسية
    elif data == "back_to_menu":
        bot.answer_callback_query(call.id)
        USER_SELECTION.pop(chat_id, None)
        try:
            bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
        bot.send_message(chat_id, WELCOME_TEXT, reply_markup=get_catalog_markup(), parse_mode="HTML")

    elif data == "sold_out_alert":
        bot.answer_callback_query(call.id, "❌ عذراً، الكمية غير متوفرة حالياً بالمخزن. تواصل مع الدعم لطلبها.", show_alert=True)

    # 4. سجل المشتريات
    elif data == "my_orders":
        bot.answer_callback_query(call.id)
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("SELECT prod_name, item_delivered, created_at FROM orders WHERE user_id = ?", (chat_id,))
            orders = c.fetchall()

        if not orders:
            history_text = "📜 <b>سجل مشترياتك:</b>\n\nليس لديك أي مشتريات سابقة حتى الآن."
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
        markup.add(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_to_menu"))
        try:
            bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
        bot.send_message(chat_id, history_text, reply_markup=markup, parse_mode="HTML")

    # 5. استعراض الدفع
    elif data == "show_payments":
        bot.answer_callback_query(call.id)
        pay_info = (
            f"🪙 <b>بيانات الدفع المعتمدة لدى Pixora Store:</b>\n\n"
            f"• <b>Binance Pay ID:</b> <code>{BINANCE_ID}</code>\n"
            f"• العملة: USDT\n\n"
            f"اختر أي منتج ثم اضغط شراء لإرسال إيصال الدفع."
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_to_menu"))
        try:
            bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
        bot.send_message(chat_id, pay_info, reply_markup=markup, parse_mode="HTML")

    # 6. تأكيد وتسليم الطلب من قِبل المدير (Admin Approve)
    elif data.startswith("admin_approve_"):
        token = data.replace("admin_approve_", "")
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("SELECT user_id, prod_key, proof FROM pending_orders WHERE token = ?", (token,))
            row = c.fetchone()

            if not row:
                bot.answer_callback_query(call.id, "⚠️ تم اتخاذ إجراء على هذا الطلب مسبقاً!", show_alert=True)
                return

            u_id, p_key, proof = row
            prod = get_product(p_key)

            # سحب كود من المخزون
            c.execute("SELECT id, item_data FROM stock WHERE prod_key = ? AND is_used = 0 LIMIT 1", (p_key,))
            stock_row = c.fetchone()

            if stock_row:
                stock_id, item_data = stock_row
                c.execute("UPDATE stock SET is_used = 1 WHERE id = ?", (stock_id,))
                c.execute(
                    "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)",
                    (token, u_id, p_key, prod['name'], item_data, time.strftime("%Y-%m-%d %H:%M:%S"))
                )
                c.execute("DELETE FROM pending_orders WHERE token = ?", (token,))
                conn.commit()

                # إرسال بيانات المنتج فورا للمشتري
                delivery_message = (
                    f"🎉 <b>تم تأكيد عملية الدفع بنجاح!</b>\n\n"
                    f"📦 <b>المنتج:</b> {prod['name']}\n"
                    f"🔑 <b>بيانات حسابك / كود التفعيل:</b>\n"
                    f"<code>{item_data}</code>\n\n"
                    f"⚡ <i>ملاحظة: يمكنك دائماً استرجاع هذه البيانات من زر (سجل مشترياتي).</i>\n"
                    f"شكراً لثقتك بمتجر <b>Pixora Store</b> 💚"
                )
                try:
                    bot.send_message(u_id, delivery_message, parse_mode="HTML")
                    bot.edit_message_caption(f"✅ تم تسليم {prod['name']} بنجاح للمشتري ({u_id}).", chat_id, msg_id) if call.message.photo else bot.edit_message_text(f"✅ تم تسليم {prod['name']} بنجاح للمشتري ({u_id}).", chat_id, msg_id)
                except Exception as err:
                    print(f"Delivery send error: {err}")
                    bot.send_message(chat_id, f"⚠️ حدث خطأ أثناء مراسلة العميل: {err}")
            else:
                bot.send_message(u_id, f"⚠️ عذراً عزيزي العميل! نفد المخزون لمنتج {prod['name']}. سيقوم الدعم بمراسلتك فوراً.")
                bot.send_message(chat_id, f"⚠️ تنبيه: لا يوجد مخزون لـ {prod['name']} لتسليمه للعميل {u_id}!")

    # 7. رفض الطلب من قِبل المدير
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
                bot.send_message(u_id, "❌ تعذر تأكيد عملية التحويل. يرجى التواصل مع الدعم الفني لمراجعة الدفعة.")
                try:
                    bot.edit_message_caption("❌ تم رفض الطلب.", chat_id, msg_id) if call.message.photo else bot.edit_message_text("❌ تم رفض الطلب.", chat_id, msg_id)
                except Exception:
                    pass
            else:
                bot.answer_callback_query(call.id, "تم اتخاذ إجراء مسبقاً.", show_alert=True)

# --- استقبال رسائل التحويل والصور من المشتري ---
@bot.message_handler(content_types=['text', 'photo'])
def handle_customer_submission(message):
    chat_id = message.chat.id
    if message.content_type == 'text' and message.text.startswith('/'):
        return

    # التحقق من أن العميل اختار منتجاً أولاً
    if chat_id not in USER_SELECTION:
        bot.send_message(chat_id, "⚠️ يرجى الضغط على المنتج الذي ترغب بشرائه أولاً من القائمة /start قبل إرسال بيانات الدفع.")
        return

    prod_key = USER_SELECTION.pop(chat_id)
    prod = get_product(prod_key)
    stock = get_stock_count(prod_key)

    if stock == 0:
        bot.send_message(chat_id, "⚠️ عذراً، نفدت كمية هذا المنتج من المخزن حالياً!")
        return

    proof = message.text.strip() if message.content_type == 'text' else "صورة إشعار تحويل مرفقة"
    token = f"{chat_id}_{int(time.time())}"
    user_name = message.from_user.first_name or "عميل"
    user_handle = f"@{message.from_user.username}" if message.from_user.username else f"ID: {chat_id}"

    # حفظ الطلب في جدول الطلبات المعلقة في SQLite
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO pending_orders VALUES (?, ?, ?, ?, ?, ?)",
                  (token, chat_id, user_name, prod_key, proof, time.time()))
        conn.commit()

    bot.send_message(chat_id, "⏳ <b>تم استلام بيانات التحويل بنجاح!</b>\nجاري مراجعة الدفعة وتسليم المنتج لك هنا في الحال...", parse_mode="HTML")

    # إرسال إشعار للمدير يحتوي على كامل التفاصيل وصورة التحويل إن وجدت
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✅ تأكيد وتسليم المنتج", callback_data=f"admin_approve_{token}"),
        InlineKeyboardButton("❌ رفض", callback_data=f"admin_reject_{token}")
    )
    admin_caption = (
        f"🔔 <b>طلب شراء جديد وصلك الآن!</b>\n\n"
        f"🛍️ <b>المنتج المطلوب:</b> {prod['name']}\n"
        f"💰 <b>المبلغ المطلوب:</b> {prod['price']} USDT\n"
        f"👤 <b>المشتري:</b> {user_name} ({user_handle})\n"
        f"🆔 <b>آيدي المشتري:</b> <code>{chat_id}</code>\n"
        f"📝 <b>الإثبات:</b> <code>{proof}</code>\n\n"
        f"👇 <i>تأكد من استلام المبلغ في Binance ثم اضغط تأكيد:</i>"
    )

    try:
        if message.content_type == 'photo':
            photo_id = message.photo[-1].file_id
            bot.send_photo(ADMIN_ID, photo_id, caption=admin_caption, reply_markup=markup, parse_mode="HTML")
        else:
            bot.send_message(ADMIN_ID, admin_caption, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        print(f"Error alerting admin: {e}")

# --- خادم Flask وإعداد Webhook لـ Render ---
@app.route('/')
def home():
    return "Pixora Store is Online & Working with SQLite!", 200

@app.route('/webhook', methods=['POST'])
def receive_webhook():
    if request.headers.get('content-type') == 'application/json':
        data = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(data)
        bot.process_new_updates([update])
        return "OK", 200
    return "Forbidden", 403

def setup_webhook_safe():
    if BOT_TOKEN and RENDER_URL:
        try:
            bot.remove_webhook()
            time.sleep(1)
            target = f"{RENDER_URL}/webhook"
            bot.set_webhook(url=target)
            print(f"Webhook linked to: {target}")
        except Exception as e:
            print("Webhook Error:", e)

if BOT_TOKEN and RENDER_URL:
    setup_webhook_safe()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
