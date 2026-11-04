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

# قائمة الـ 31 منتجاً بتفاصيلها وأوصافها الكاملة
RAW_PRODUCTS = [
    # 1. المونتاج والتصميم
    ("capcut_1m", "🎞️ CapCut Pro (شهر)", 1.30, "اشتراك CapCut Pro رسمي لمدة 30 يوماً:\n• بدون علامة مائية وبأعلى دقة 4K.\n• وصول لجميع القوالب والمؤثرات وأدوات الذكاء الاصطناعي."),
    ("capcut_1y", "🎞️ CapCut Pro (سنة)", 9.50, "اشتراك CapCut Pro رسمي لمدة 12 شهراً:\n• يعمل على الهاتف والكمبيوتر.\n• ضمان لكامل المدة وفتح كافة الميزات."),
    ("filmora", "🎬 Wondershare Filmora 13", 8.00, "تفعيل Filmora ترخيص كامل للكمبيوتر:\n• إزالة العلامة المائية وتصدير عالي الدقة.\n• فتح مكتبة التأثيرات والانتقالات."),
    ("canva_pro", "🎨 Canva Pro (سنة)", 4.00, "تفعيل Canva Pro رسمي على إيميلك الخاص:\n• ملايين القوالب والتصاميم وإزالة الخلفية بضغطة زر.\n• مساحة سحابية وميزات الذكاء الاصطناعي."),
    ("picsart", "📸 PicsArt Gold (سنة)", 3.00, "اشتراك PicsArt Gold لمدة سنة:\n• فتح كافة الفلاتر الاحترافية وأدوات التعديل بدون إعلانات."),

    # 2. أدوات الذكاء الاصطناعي
    ("chatgpt_plus", "🤖 ChatGPT Plus (شهر)", 18.00, "حساب ChatGPT Plus مدفوع شهر:\n• وصول لموديل GPT-4o وتوليد الصور وتصفح الويب وتحليل الملفات."),
    ("claude_pro", "🧠 Claude Pro (شهر)", 18.00, "اشتراك Claude Pro لمدة شهر:\n• وصول كامل لموديل Claude 3.5 Sonnet المتقدم في البرمجة والتحليل."),
    ("gemini_adv", "💠 Google Gemini Advanced", 3.00, "خطة Gemini Advanced مع 2TB مساحة سحابية:\n• نموذج 1.5 Pro المتطور ودمج مع خدمات جوجل."),
    ("elevenlabs", "🎙️ ElevenLabs Starter", 5.00, "اشتراك ElevenLabs:\n• أصوات بشرية بالذكاء الاصطناعي بمختلف اللغات واستنساخ الصوت."),
    ("midjourney", "🎨 Midjourney Basic", 10.00, "اشتراك Midjourney رسمي لمدة شهر:\n• توليد أقوى الصور الفنية الواقعية برصيد Fast GPU."),
    ("runway", "📹 Runway Gen-2 (شهر)", 12.00, "اشتراك Runway لصناعة الفيديو:\n• تحويل النص والصورة إلى فيديو ومؤثرات سينمائية."),
    ("perplexity", "🔍 Perplexity Pro (شهر)", 6.00, "اشتراك محرك البحث الذكي Perplexity Pro:\n• بحث مدعوم بأحدث النماذج وتلخيص وتحليل الملفات."),

    # 3. برامج مايكروسوفت والإنتاجية
    ("office_365", "🟩 Microsoft Office 365", 0.30, "حساب مايكروسوفت أوفيس 365:\n• يشمل برامج Office كاملة لـ 5 أجهزة مع 1TB OneDrive."),
    ("windows_11", "🪟 Windows 11 Pro Key", 3.50, "مفتاح رقمي أصلي لتفعيل ويندوز 11 برو مدى الحياة عبر خوادم مايكروسوفت."),
    ("windows_10", "🪟 Windows 10 Pro Key", 2.50, "مفتاح تفعيل أصلي لويندوز 10 برو مدى الحياة مع التحديثات الرسمية."),
    ("autodesk", "🔺 Autodesk All Apps (سنة)", 3.00, "حساب أوتوديسك مع لوحة تحكم رسمية لمدة سنة لبرامج الهندسة والتصميم."),

    # 4. برامج الحماية والـ VPN
    ("nordvpn", "🛡️ NordVPN Premium (سنة)", 3.50, "حساب NordVPN بريميوم لمدة سنة:\n• خوادم سريعة وفك الحجب وحماية الخصوصية على 6 أجهزة."),
    ("expressvpn", "⚡ ExpressVPN (شهر)", 4.00, "حساب ExpressVPN فائق السرعة لتخطي الحجب والبث السريع والألعاب."),
    ("surfshark", "🦈 Surfshark VPN (سنة)", 3.00, "اشتراك Surfshark سنوي:\n• اتصالات غير محدودة للأجهزة ومانع إعلانات CleanWeb."),
    ("kaspersky", "🦠 Kaspersky Total Security", 5.00, "مفتاح تفعيل أصلي لكاسبرسكي لحماية شاملة من الفيروسات والفدية لمدة سنة."),

    # 5. الترفيه ومنصات البث
    ("netflix_1m", "🍿 Netflix UHD (شهر)", 3.50, "بروفايل شخصي برمز PIN بدقة 4K Ultra HD مع ضمان لكامل المدة."),
    ("netflix_3m", "🍿 Netflix UHD (3 أشهر)", 9.00, "بروفايل شخصي 4K لمدة 3 أشهر متواصلة بدون انقطاع مع الضمان."),
    ("spotify_ind", "🎵 Spotify Premium (شهر)", 2.00, "اشتراك سبوتيفاي فردي بدون إعلانات مع ميزة التنزيل والاستماع أوفلاين."),
    ("spotify_1y", "🎵 Spotify Premium (سنة)", 11.00, "اشتراك سبوتيفاي سنوي رسمي استماع دائم بدون إعلانات."),
    ("youtube_prem", "▶️ YouTube Premium (شهر)", 2.00, "تفعيل يوتيوب بريميوم رسمي على إيميلك (بدون إعلانات + YouTube Music)."),
    ("youtube_6m", "▶️ YouTube Premium (6 أشهر)", 8.50, "تفعيل رسمي لمدة 6 أشهر على إيميلك مع تشغيل بالخلفية وتنزيل مقاطع."),
    ("crunchyroll", "🍥 Crunchyroll Mega Fan", 2.00, "حساب Crunchyroll لمتابعة أحدث الأنميات بدون إعلانات وبأعلى دقة 1080p."),
    ("shahid_vip", "⭐ Shahid VIP (شهر)", 3.50, "اشتراك شاهد VIP رسمي للأفلام والمسلسلات الحصرية والبث المباشر."),
    ("iptv_1y", "📺 اشتراك IPTV (سنة)", 12.00, "سيرفر IPTV شامل لأكثر من 10,000 قناة رياضية وعالمية ومكتبة أفلام ضخمة."),

    # 6. التعليم والمطورين
    ("duolingo", "🦉 Duolingo Super (سنة)", 4.50, "اشتراك دولينجو سوبر سنوي لتعلم اللغات بقلوب غير محدودة وبدون إعلانات."),
    ("github_pack", "🐙 GitHub Student Pack", 7.00, "باقة أدوات جيت هب للطلاب والمطورين تشمل استضافات ودومينات وأدوات برمجية مجانية.")
]

PRODUCTS_INFO = {k: {"name": n, "price": p, "description": d} for k, n, p, d in RAW_PRODUCTS}

# قاعدة بيانات المخزون: الأصناف غير المتوفرة رصيدها فارغ []
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

WELCOME_TEXT = """🔥 <b>أهلاً بك في متجر Pixora Store الرقمي!</b> 🚀

⚡ <i>نوفر لك أقوى الحسابات والاشتراكات الرقمية بأفضل الأسعار وأعلى ضمان رسمي.</i>
💎 <b>التسليم فوري</b> بعد إتمام الدفع عبر Binance Pay!

👇 <b>اختر منتجك من القائمة أدناه:</b>"""

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
    return "Pixora Store is Live!", 200

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
                msg = f"🎉 <b>تم تأكيد الدفع بنجاح!</b>\n\n📦 بيانات {p_name}:\n<code>{item}</code>\n\nشكراً لتعاملك مع <b>Pixora Store</b> 💚"
                bot.send_message(u_id, msg, parse_mode="HTML")
                bot.edit_message_text(f"✅ تم تسليم {p_name} للعميل بنجاح.", chat_id, msg_id)
            else:
                bot.send_message(u_id, "⚠️ نفد المخزون، يرجى مراجعة الدعم الفني.")
                bot.edit_message_text("⚠️ المخزون فارغ!", chat_id, msg_id)
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
            
            text = f"""🏷️ <b>{info['name']}</b>
💰 <b>Price:</b> <code>${info['price']}</code>

📦 <b>Stock:</b> <code>{stock}</code>
📰 <b>Description:</b>

{info['description']}

🛍️ <b>Buy Quantity:</b> 1"""
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

    elif data.startswith("pay_steps_"):
        p_key = data.replace("pay_steps_", "")
        info = PRODUCTS_INFO[p_key]
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("🔙 رجوع للمنتج", callback_data=f"buy_{p_key}"), InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
        
        text = f"""🪙 <b>خطوات الدفع عبر Binance Pay:</b>

1️⃣ حول مبلغ (<code>{info['price']} USDT</code>) إلى Binance ID: <code>{BINANCE_ID}</code>

2️⃣ انسخ <b>رقم العملية (Order ID)</b> أو أرسل صورة الإشعار هنا لتأكيد طلبك واستلام حسابك فوراً!"""
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
    chat
