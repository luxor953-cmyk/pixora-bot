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

RAW_PRODUCTS = [
    ("capcut_1m", "🎞️ CapCut Pro (شهر)", 1.30, "CapCut Pro 30 Days - اشتراك رسمي كامل.\n• إزالة العلامة المائية وتصدير بجودة 4K.\n• وصول لكافة القوالب وميزات الذكاء الاصطناعي."),
    ("capcut_1y", "🎞️ CapCut Pro (سنة)", 9.50, "CapCut Pro 1 Year - اشتراك سنوي رسمي.\n• يعمل على الحاسوب والهاتف.\n• ضمان كامل لكامل المدة."),
    ("filmora", "🎬 Wondershare Filmora 13", 8.00, "تفعيل برنامج Wondershare Filmora ترخيص كامل للكمبيوتر بدون علامة مائية مع جميع المؤثرات الاحترافية."),
    ("canva_pro", "🎨 Canva Pro (سنة)", 4.00, "اشتراك Canva Pro رسمي يتم تفعيله على إيميلك الخاص بميزات غير محدودة وتخزين سحابي وإزالة الخلفية بضغطة زر."),
    ("picsart", "📸 PicsArt Gold (سنة)", 3.00, "اشتراك PicsArt Gold لمدة 12 شهراً:\n• فتح كافة الأدوات والفلاتر بدون إعلانات وبأعلى دقة حفظ."),
    ("chatgpt_plus", "🤖 ChatGPT Plus (شهر)", 18.00, "حساب ChatGPT Plus مدفوع شهر كامل:\n• وصول غير محدود لموديل GPT-4o وتوليد الصور وتصفح الويب."),
    ("claude_pro", "🧠 Claude Pro (شهر)", 18.00, "اشتراك Claude Pro رسمي لمدة شهر:\n• استخدام نموذج Claude 3.5 Sonnet الخارق في كتابة الكود والتحليل بسعة رسائل مضاعفة."),
    ("gemini_adv", "💠 Google Gemini Advanced", 3.00, "خطة Gemini Advanced مع باقة Google One 2TB لمدة 18 شهراً وميزات الذكاء الاصطناعي الكاملة."),
    ("elevenlabs", "🎙️ ElevenLabs Starter", 5.00, "اشتراك ElevenLabs:\n• توليد أصوات واقعية واحترافية بالذكاء الاصطناعي واستنساخ الأصوات بدقة متناهية."),
    ("midjourney", "🎨 Midjourney Basic", 10.00, "اشتراك Midjourney رسمي لمدة شهر:\n• رصيد لتوليد وتصميم الصور الاحترافية عالية الدقة والواقعية."),
    ("runway", "📹 Runway Gen-2 (شهر)", 12.00, "اشتراك Runway Gen-2 لتوليد مقاطع الفيديو السينمائية بالذكاء الاصطناعي بجودة ممتازة."),
    ("perplexity", "🔍 Perplexity Pro (شهر)", 6.00, "اشتراك Perplexity Pro للبحث الذكي وتلخيص الوثائق المعتمد على أحدث نماذج الذكاء الاصطناعي."),
    ("office_365", "🟩 Microsoft Office 365", 0.30, "حساب رسمي مفعل Office 365 Plus يدعم 5 أجهزة مع مساحة تخزين سحابية 1TB على OneDrive."),
    ("windows_11", "🪟 Windows 11 Pro Key", 3.50, "مفتاح رقمي أصلي دائم لتفعيل Windows 11 Pro مدى الحياة مع دعم التحديثات الرسمية."),
    ("windows_10", "🪟 Windows 10 Pro Key", 2.50, "مفتاح رقمي أصلي دائم لتفعيل Windows 10 Pro مدى الحياة وتنشيط رسمي عبر الإنترنت."),
    ("autodesk", "🔺 Autodesk All Apps (سنة)", 3.00, "حساب أوتوديسك مع لوحة تحكم رسمية لمدة سنة لبرامج AutoCAD و Revit و 3ds Max وغيرها."),
    ("nordvpn", "🛡️ NordVPN Premium (سنة)", 3.50, "حساب NordVPN بريميوم لمدة سنة كاملة:\n• حماية للخصوصية وسرعة اتصال عالية مع فك الحجب."),
    ("expressvpn", "⚡ ExpressVPN (شهر)", 4.00, "حساب ExpressVPN فائق السرعة لتخطي الحظر الجغرافي ودعم البث المباشر والألعاب."),
    ("surfshark", "🦈 Surfshark VPN (سنة)", 3.00, "اشتراك Surfshark سنوي:\n• اتصال غير محدود للأجهزة مع أداة حجب الإعلانات المدمجة."),
    ("kaspersky", "🦠 Kaspersky Total Security", 5.00, "مفتاح تفعيل أصلي لـ Kaspersky Total Security لمدة سنة لحماية متكاملة من الفيروسات والتهديدات."),
    ("netflix_1m", "🍿 Netflix UHD (شهر)", 3.50, "بروفايل شخصي مقفل برمز PIN بدقة 4K Ultra HD لمدة شهر مع ضمان كامل."),
    ("netflix_3m", "🍿 Netflix UHD (3 أشهر)", 9.00, "بروفايل رسمي 4K UHD لمدة 3 أشهر بدون انقطاع مع ضمان لكامل الفترة."),
    ("spotify_ind", "🎵 Spotify Premium (شهر)", 2.00, "اشتراك سبوتيفاي بريميوم بدون أي إعلانات وميزة الاستماع بدون إنترنت وبأعلى نقاء."),
    ("spotify_1y", "🎵 Spotify Premium (سنة)", 11.00, "اشتراك Spotify بريميوم سنوي رسمي ومستقر لمدة 12 شهراً."),
    ("youtube_prem", "▶️ YouTube Premium (شهر)", 2.00, "تفعيل يوتيوب بريميوم رسمي على إيميلك الخاص:\n• بدون إعلانات مع تشغيل بالخلفية و YouTube Music."),
    ("youtube_6m", "▶️ YouTube Premium (6 أشهر)", 8.50, "تفعيل يوتيوب بريميوم رسمي لمدة 6 أشهر متواصلة بدون إعلانات على كافة أجهزتك."),
    ("crunchyroll", "🍥 Crunchyroll Mega Fan", 2.00, "حساب Crunchyroll باقة Mega Fan لمتابعة الأنمي بدون إعلانات وبأعلى دقة 1080p."),
    ("shahid_vip", "⭐ Shahid VIP (شهر)", 3.50, "اشتراك شاهد VIP رسمي للأفلام والمسلسلات الحصرية بدقة كاملة وبدون فواصل."),
    ("iptv_1y", "📺 اشتراك IPTV (سنة)", 12.00, "سيرفر IPTV بريميوم لمدة سنة يضم أكثر من 10,000 قناة رياضية وعالمية ومكتبة أفلام ضخمة."),
    ("duolingo", "🦉 Duolingo Super (سنة)", 4.50, "اشتراك دولينجو سوبر سنوي لتعلم اللغات بقلوب لا نهائية وبدون إعلانات."),
    ("github_pack", "🐙 GitHub Student Pack", 7.00, "باقة أدوات GitHub Student Developer Pack كاملة للمطورين مع استضافات ونطاقات مجانية.")
]

PRODUCTS_INFO = {k: {"name": n, "price": p, "description": d} for k, n, p, d in RAW_PRODUCTS}

STOCK_DATABASE = {k: [] for k in PRODUCTS_INFO}
STOCK_DATABASE["capcut_1m"] = ["CapCut_Key_1: user1@pixoras.com / pass123"]
STOCK_DATABASE["gemini_adv"] = ["https://g.co/gemini/share/sample_link_1"]
STOCK_DATABASE["office_365"] = ["Office365_Key_1: kc5921@o365pp.com / &$^2^jGq"]
STOCK_DATABASE["autodesk"] = ["Autodesk_Key_ABC123"]
STOCK_DATABASE["canva_pro"] = ["https://www.canva.com/brand/join?inv=sample_1"]

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

WELCOME_TEXT = "🔥 <b>أهلاً بك في متجر Pixora Store الرقمي!</b> 🚀\n\n⚡ <i>نوفر لك أقوى الحسابات والاشتراكات الرقمية المدفوعة بأفضل الأسعار وأعلى ضمان رسمي.</i>\n💎 <b>التسليم فوري</b> بعد إتمام الدفع عبر Binance Pay!\n\n👇 <b>اختر منتجك من القائمة أدناه:</b>"

def get_main_menu_markup():
    markup = InlineKeyboardMarkup(row_width=2)
    btns = []
    for k, info in PRODUCTS_INFO.items():
        if len(STOCK_DATABASE.get(k, [])) == 0:
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
    markup.add(InlineKeyboardButton("🛠️ الدعم الفني (WhatsApp)", url=SUPPORT_WHATSAPP))
    return markup

@app.route('/')
def home():
    return "Pixora Store Bot is Running!", 200

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
    bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=get_main_menu_markup(), parse_mode="HTML")

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
                msg = f"🎉 <b>تم تأكيد الدفع بنجاح!</b>\n\n📦 بيانات {p_name}:\n<code>{item}</code>\n\n📜 تم حفظ طلبك في (سجل مشترياتي).\nشكراً لتعاملك مع <b>Pixora Store</b> 💚"
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
        bot.answer_callback_query(call.id, "❌ عذراً، هذا المنتج غير متوفر في المخزن حالياً!", show_alert=True)

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
            markup.add(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"), InlineKeyboardButton("🛠️ الدعم الفني", url=SUPPORT_WHATSAPP))
            
            text = f"🏷️ <b>{info['name']}</b>\n💰 <b>Price:</b> <code>${info['price']}</code>\n\n📦 <b>Stock:</b> <code>{stock}</code>\n📰 <b>Description:</b>\n\n{info['description']}\n\n🛍️ <b>Buy Quantity:</b> 1"
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

    elif data.startswith("pay_steps_"):
        p_key = data.replace("pay_steps_", "")
        info = PRODUCTS_INFO[p_key]
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("🔙 رجوع للمنتج", callback_data=f"buy_{p_key}"), InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
        
        text = f"🪙 <b>خطوات الدفع عبر Binance Pay:</b>\n\n1️⃣ حول مبلغ (<code>{info['price']} USDT</code>) إلى Binance ID: <code>{BINANCE_ID}</code>\n\n2️⃣ أرسل <b>رقم العملية (Order ID)</b> أو صورة الإشعار هنا في الشات لتأكيد طلبك واستلام حسابك فوراً!"
        safe_delete_message(chat_id, msg_id)
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

    elif data == "show_payments":
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
        text = f"🪙 <b>معلومات الدفع في متجر Pixora Store:</b>\n\nBinance Pay ID: <code>{BINANCE_ID}</code>\n\nاختر منتجك أولاً من القائمة ثم أرسل إثبات الدفع بعد التحويل."
        safe_delete_message(chat_id, msg_id)
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

    elif data == "my_orders":
        bot.answer_callback_query(call.id)
        ords = load_orders().get(str(chat_id), [])
        if not ords:
            text = "📜 <b>سجل مشترياتي:</b>\n\nعذراً، ليس لديك أي عمليات شراء مسجلة حتى الآن."
        else:
            text = "📜 <b>سجل مشترياتي السابقة:</b>\n\n"
            for idx, o in enumerate(ords, 1):
                text += f"{idx}️⃣ <b>المنتج:</b> {o['product']}\n🔑 <b>البيانات:</b> <code>{o['item']}</code>\n🆔 <b>العملية:</b> <code>{o['order_id']}</code>\n📅 <b>الوقت:</b> {o['time']}\n------------------------\n"
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
        safe_delete_message(chat_id, msg_id)
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

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
