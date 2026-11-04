import os
import time
import json
import threading
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_ID = 1004439571098  # معرّف الإدارة لتلقي طلبات التأكيد الفوري
BINANCE_ID = "957483337"
RENDER_URL = os.environ.get("RENDER_URL", "").strip()
SUPPORT_WHATSAPP = "https://wa.me/213555668244"

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
app = Flask(__name__)

# قائمة الـ 31 منتجاً الخاصة بمتجر Pixora Store
RAW_PRODUCTS = [
    # 1. المونتاج وصناعة المحتوى
    ("capcut_1m", "🎞️ CapCut Pro (شهر)", 1.30, "اشتراك CapCut Pro لمدة شهر كامل."),
    ("capcut_1y", "🎞️ CapCut Pro (سنة)", 9.50, "اشتراك CapCut Pro لمدة سنة رسمية."),
    ("filmora", "🎬 Wondershare Filmora", 8.00, "تفعيل Filmora ترخيص كامل."),
    ("canva_pro", "🎨 Canva Pro (سنة)", 4.00, "تفعيل Canva Pro رسمي على إيميلك الخاص."),
    ("picsart", "📸 PicsArt Gold", 3.00, "اشتراك PicsArt Gold لمدة سنة."),
    
    # 2. أدوات الذكاء الاصطناعي
    ("chatgpt_plus", "🤖 ChatGPT Plus (شهر)", 18.00, "حساب ChatGPT Plus مدفوع شهر."),
    ("claude_pro", "🧠 Claude Pro (شهر)", 18.00, "اشتراك Claude Pro رسمي لمدة شهر."),
    ("gemini_adv", "💠 Google Gemini Advanced", 3.00, "خطة Gemini Advanced مع مساحة 2TB."),
    ("elevenlabs", "🎙️ ElevenLabs Starter", 5.00, "اشتراك ElevenLabs لتوليد الأصوات بالذكاء الاصطناعي."),
    ("midjourney", "🎨 Midjourney Basic", 10.00, "اشتراك Midjourney رسمي لتوليد الصور."),
    ("runway", "📹 Runway Gen-2", 12.00, "اشتراك Runway لصناعة الفيديو بالذكاء الاصطناعي."),
    ("perplexity", "🔍 Perplexity Pro", 6.00, "اشتراك Perplexity Pro للبحث الذكي."),

    # 3. برامج وحزم الإنتاجية والمايكروسوفت
    ("office_365", "🟩 Microsoft Office 365", 0.30, "حساب Office 365 لـ 5 أجهزة + 1TB OneDrive."),
    ("windows_11", "🪟 Windows 11 Pro Key", 3.50, "مفتاح أصلي رقمي لتفعيل ويندوز 11 برو مدى الحياة."),
    ("windows_10", "🪟 Windows 10 Pro Key", 2.50, "مفتاح أصلي لتفعيل ويندوز 10 برو مدى الحياة."),
    ("autodesk", "🔺 Autodesk All Apps (سنة)", 3.00, "حساب أوتوديسك مع لوحة تحكم رسمية 1 سنة."),

    # 4. برامج الحماية والـ VPN
    ("nordvpn", "🛡️ NordVPN (سنة)", 3.50, "حساب NordVPN بريميوم لمدة سنة كاملة."),
    ("expressvpn", "⚡ ExpressVPN (شهر)", 4.00, "حساب ExpressVPN فائق السرعة."),
    ("surfshark", "🦈 Surfshark VPN (سنة)", 3.00, "اشتراك Surfshark VPN لعدة أجهزة."),
    ("kaspersky", "🦠 Kaspersky Total Security", 5.00, "مفتاح ترخيص كاسبرسكي أصلي لمدة سنة."),

    # 5. الترفيه ومنصات البث
    ("netflix_1m", "🍿 Netflix UHD (شهر)", 3.50, "بروفايل خاص بجودة 4K UHD لمدة شهر."),
    ("netflix_3m", "🍿 Netflix UHD (3 أشهر)", 9.00, "بروفايل رسمي 4K لمدة 3 أشهر."),
    ("spotify_ind", "🎵 Spotify Premium (شهر)", 2.00, "اشتراك Spotify بريميوم بدون إعلانات."),
    ("spotify_1y", "🎵 Spotify Premium (سنة)", 11.00, "اشتراك سنوي Spotify رسمي."),
    ("youtube_prem", "▶️ YouTube Premium (شهر)", 2.00, "تفعيل يوتيوب بريميوم رسمي على إيميلك."),
    ("youtube_6m", "▶️ YouTube Premium (6 أشهر)", 8.50, "تفعيل يوتيوب بريميوم رسمي 6 أشهر."),
    ("crunchyroll", "🍥 Crunchyroll Mega Fan", 2.00, "حساب Crunchyroll بدون إعلانات شهر كامل."),
    ("shahid_vip", "⭐ Shahid VIP (شهر)", 3.50, "اشتراك شاهد VIP لمتابعة المسلسلات والأفلام."),
    ("iptv_1y", "📺 اشتراك IPTV (سنة)", 12.00, "سيرفر IPTV شامل القنوات والمباريات بجودة عالية."),

    # 6. التعليم والمطورين
    ("duolingo", "🦉 Duolingo Plus (سنة)", 4.50, "اشتراك دولينجو بلس لتعلم اللغات."),
    ("github_pack", "🐙 GitHub Student Developer Pack", 7.00, "باقة أدوات جيت هب للطلاب والمطورين.")
]

PRODUCTS_INFO = {k: {"name": n, "price": p, "description": d} for k, n, p, d in RAW_PRODUCTS}

# قاعدة بيانات المخزون: يتم ملء المتوفر فقط، والباقي يبقى فارغاً [] ليعتبر رصيده 0
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
        print("Error saving orders:", e)

WELCOME_TEXT = """🔥 <b>أهلاً بك في متجر Pixora Store الرقمي!</b> 🚀

⚡ <i>نوفر لك أقوى الحسابات والاشتراكات الرقمية بأفضل الأسعار وأعلى ضمان رسمي.</i>
💎 <b>التسليم فوري</b> عبر Binance Pay!

👇 <b>تصفح قائمة الـ 31 منتجاً واختر طلبك الآن:</b>"""

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
                bot.send_message(u_chat_id, f"⚠️ تم تأكيد الدفع ولكن المنتج ({p_name}) نفد حالياً، تواصل معنا عبر الدعم الفني.")
                bot.edit_message_text(f"⚠️ المخزون فارغ لهذا الصنف!", chat_id, msg_id)
        else:
            bot.answer_callback_query(call.id, "تم اتخاذ إجراء مسبقاً بشأن هذا الطلب.", show_alert=True)
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
            stock_len = len(STOCK_DATABASE.get(prod_key,
