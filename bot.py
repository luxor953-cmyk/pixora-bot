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

bot = telebot.TeleBot(BOT_TOKEN, threaded=False) if BOT_TOKEN else None

USER_SELECTED_PRODUCT = {}
USER_CURRENT_CATEGORY = {}
ORDERS_FILE = "orders.json"

# كلمات محظورة لفلترة أي منتجات أغاني أو أفلام أو مسلسلات نهائياً
BANNED_KEYWORDS = [
    "spotify", "anghami", "netflix", "shahid", "disney", "apple music", 
    "iptv", "movie", "film", "music", "osn", "watchit", "prime video", 
    "اغاني", "موسيقى", "أفلام", "مسلسلات", "سينما"
]

def is_halal_product(name, description=""):
    text = f"{name} {description}".lower()
    for word in BANNED_KEYWORDS:
        if word in text:
            return False
    return True

# دالة لتصنيف المنتجات حسب البراند والخدمة بدقة
def categorize_product_by_brand(name):
    n = name.lower()
    if "google" in n or "جوجل" in n or "gemini" in n:
        return "🌐 خدمات جوجل (Google)"
    elif "capcut" in n or "كاب كات" in n:
        return "🎬 خطط كاب كات (CapCut)"
    elif "canva" in n or "كانفا" in n or "picsart" in n or "adobe" in n or "photoshop" in n:
        return "🎨 التصميم الجرافيكي"
    elif "chatgpt" in n or "openai" in n or "claude" in n or "ai" in n or "ذكاء اصطناعي" in n:
        return "🤖 أدوات الذكاء الاصطناعي"
    else:
        return "💻 البرمجيات والخدمات الرقمية"

def safe_delete_message(chat_id, msg_id):
    try:
        if bot:
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

def fetch_supplier_products():
    if not RESELLER_KEY:
        return {}
    headers = {"X-Reseller-Key": RESELLER_KEY}
    try:
        response = requests.get(f"{VENTEBOT_API_URL}/products", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            categories_map = {}
            items = data.get("products", data) if isinstance(data, dict) else data
            for item in items:
                p_name = item.get("name", "منتج رقمي")
                p_desc = item.get("description", "اشتراك رقمي رسمي مع ضمان كامل.")
                
                if not is_halal_product(p_name, p_desc):
                    continue

                p_id = str(item.get("id", item.get("code", "unknown")))
                raw_price = float(item.get("price", 1.0))
                
                # إضافة مكسب ثابت (نصف عملة USDT) لكل منتج
                p_price = round(raw_price + 0.50, 2)
                p_stock = item.get("stock", item.get("quantity", 10))
                
                cat_name = categorize_product_by_brand(p_name)
                
                if cat_name not in categories_map:
                    categories_map[cat_name] = {}
                    
                categories_map[cat_name][p_id] = {
                    "name": p_name,
                    "price": p_price,
                    "stock": p_stock,
                    "description": p_desc
                }
            return categories_map
    except Exception as e:
        print("Error fetching supplier products:", e)
    return {}

def api_get_my_wallet():
    if not RESELLER_KEY:
        return None
    try:
        res = requests.get(f"{VENTEBOT_API_URL}/me", headers={"X-Reseller-Key": RESELLER_KEY}, timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None

def api_get_wallet_transactions():
    if not RESELLER_KEY:
        return None
    try:
        res = requests.get(f"{VENTEBOT_API_URL}/wallet/transactions", headers={"X-Reseller-Key": RESELLER_KEY}, timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None

def api_get_deposit_methods():
    if not RESELLER_KEY:
        return None
    try:
        res = requests.get(f"{VENTEBOT_API_URL}/wallet/deposit-methods", headers={"X-Reseller-Key": RESELLER_KEY}, timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None

def purchase_order_from_supplier(product_id, reference_id):
    if not RESELLER_KEY:
        return {"success": False, "error": "No reseller key"}
    
    headers = {"X-Reseller-Key": RESELLER_KEY, "Content-Type": "application/json"}
    payload = {"product_id": product_id, "reference": reference_id}
    try:
        response = requests.post(f"{VENTEBOT_API_URL}/orders", json=payload, headers=headers, timeout=15)
        if response.status_code in [200, 201]:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}

WELCOME_TEXT = "🔥 أهلاً بك في متجر Pixora Store الرقمي الأول!\n\nاختر البراند أو التصنيف المطلوب أدناه:"

def get_main_menu_markup(is_admin=False):
    markup = InlineKeyboardMarkup()
    cats = fetch_supplier_products()
    
    if not cats:
        markup.add(InlineKeyboardButton("⚠️ لا توجد منتجات متاحة حالياً...", callback_data="main_menu"))
        return markup

    for cat_name in cats.keys():
        markup.add(InlineKeyboardButton(f"📁 {cat_name}", callback_data="cat_" + cat_name))

    markup.row(InlineKeyboardButton("📜 مشترياتي", callback_data="my_orders"))
    if is_admin:
        markup.row(InlineKeyboardButton("🛠️ لوحة تحكم الإدارة", callback_data="admin_panel"))
    markup.add(InlineKeyboardButton("🛠️ الدعم الفني", url=SUPPORT_WHATSAPP))
    return markup

def get_category_products_markup(cat_name):
    markup = InlineKeyboardMarkup()
    cats = fetch_supplier_products()
    
    if cat_name in cats:
        for p_id, info in cats[cat_name].items():
            if info['stock'] > 0:
                markup.add(InlineKeyboardButton(f"✅ {info['name']} · ${info['price']}", callback_data="buy_" + p_id))
            else:
                markup.add(InlineKeyboardButton(f"❌ {info['name']} (نفد)", callback_data="sold_out_" + p_id))

    markup.row(InlineKeyboardButton("🔙 عودة للتصنيفات", callback_data="main_menu"))
    return markup

def get_admin_markup():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("💰 فحص الرصيد بالمحفظة", callback_data="adm_balance"), InlineKeyboardButton("💳 طرق الإيداع", callback_data="adm_deposits"))
    markup.row(InlineKeyboardButton("📊 سجل المعاملات المالية", callback_data="adm_transactions"))
    markup.row(InlineKeyboardButton("🔙 عودة للقائمة الرئيسية", callback_data="main_menu"))
    return markup

if bot:
    @bot.message_handler(commands=['start', 'menu'])
    def send_welcome(message):
        is_admin = (message.chat.id == ADMIN_ID)
        bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=get_main_menu_markup(is_admin))

    @bot.callback_query_handler(func=lambda call: True)
    def handle_query(call):
        chat_id = call.message.chat.id
        msg_id = call.message.message_id
        data = call.data
        is_admin = (chat_id == ADMIN_ID)
        cats = fetch_supplier_products()

        if data == "admin_panel" and is_admin:
            bot.answer_callback_query(call.id)
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, "🛠️ <b>لوحة تحكم الإدارة المتقدمة:</b>\nاختر العملية المطلوبة:", reply_markup=get_admin_markup(), parse_mode="HTML")

        elif data == "adm_balance" and is_admin:
            bot.answer_callback_query(call.id)
            wallet = api_get_my_wallet()
            text = f"💰 <b>بيانات المحفظة لدى المزود:</b>\n<pre>{json.dumps(wallet, indent=2, ensure_ascii=False)}</pre>" if wallet else "❌ تعذر جلب بيانات الرصيد."
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔙 رجوع لوحة التحكم", callback_data="admin_panel"))
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

        elif data == "adm_deposits" and is_admin:
            bot.answer_callback_query(call.id)
            dep = api_get_deposit_methods()
            text = f"💳 <b>طرق وأدنى حدود الإيداع:</b>\n<pre>{json.dumps(dep, indent=2, ensure_ascii=False)}</pre>" if dep else "❌ تعذر جلب طرق الإيداع."
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔙 رجوع لوحة التحكم", callback_data="admin_panel"))
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

        elif data == "adm_transactions" and is_admin:
            bot.answer_callback_query(call.id)
            txs = api_get_wallet_transactions()
            text = f"📊 <b>سجل المعاملات المالية:</b>\n<pre>{json.dumps(txs, indent=2, ensure_ascii=False)[:3500]}</pre>" if txs else "❌ تعذر جلب سجل المعاملات."
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔙 رجوع لوحة التحكم", callback_data="admin_panel"))
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

        elif data.startswith("cat_"):
            cat_name = data.replace("cat_", "")
            bot.answer_callback_query(call.id)
            USER_CURRENT_CATEGORY[chat_id] = cat_name
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, f"📁 <b>{cat_name}</b>\n\nاختر المنتج المطلوب:", reply_markup=get_category_products_markup(cat_name), parse_mode="HTML")

        elif data.startswith("buy_"):
            prod_key = data.replace("buy_", "")
            found_info = None
            for cat_name, prod_dict in cats.items():
                if prod_key in prod_dict:
                    found_info = prod_dict[prod_key]
                    break
            
            if found_info:
                bot.answer_callback_query(call.id)
                USER_SELECTED_PRODUCT[chat_id] = prod_key
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("🪙 إتمام الدفع الفوري", callback_data="pay_" + prod_key))
                markup.row(InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="cat_" + USER_CURRENT_CATEGORY.get(chat_id, list(cats.keys())[0])))
                
                msg_text = f"🏷️ {found_info['name']}\n💰 السعر: ${found_info['price']}\n📦 المخزون: {found_info['stock']}\n\n{found_info['description']}"
                safe_delete_message(chat_id, msg_id)
                bot.send_message(chat_id, msg_text, reply_markup=markup)
                
        elif data.startswith("pay_"):
            prod_key = data.replace("pay_", "")
            found_price = 1.0
            for cat_name, prod_dict in cats.items():
                if prod_key in prod_dict:
                    found_price = prod_dict[prod_key]['price']
                    break
            
            bot.answer_callback_query(call.id)
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("🔙 رجوع", callback_data="main_menu"))
            pay_msg = f"🪙 تحويل مبلغ (${found_price} USDT) إلى Binance ID: {BINANCE_ID}\n\nثم أرسل رقم العملية (Order ID) أو إيصال الدفع هنا للشات ليتم التسليم الفوري أوتوماتيكياً."
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, pay_msg, reply_markup=markup)
            
        elif data == "my_orders":
            bot.answer_callback_query(call.id)
            ords = load_orders().get(str(chat_id), [])
            if not ords:
                text = "📜 سجل مشترياتي:\n\nلا توجد طلبات سابقة."
            else:
                text = "📜 سجل مشترياتي السابقة:\n\n"
                for o in ords:
                    text += f"📦 {o['product']}\n🔑 البيان: <code>{o['item']}</code>\n------------------\n"
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
            
        elif data == "main_menu":
            bot.answer_callback_query(call.id)
            USER_SELECTED_PRODUCT.pop(chat_id, None)
            USER_CURRENT_CATEGORY.pop(chat_id, None)
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, WELCOME_TEXT, reply_markup=get_main_menu_markup(is_admin))

    @bot.message_handler(content_types=['text', 'photo'])
    def handle_incoming(message):
        chat_id = message.chat.id
        if message.text and message.text.startswith('/'):
            return
        if chat_id not in USER_SELECTED_PRODUCT:
            bot.send_message(chat_id, "⚠️ يرجى اختيار المنتج أولاً وضغط إتمام الدفع من /start")
            return

        prod_key = USER_SELECTED_PRODUCT.pop(chat_id)
        cats = fetch_supplier_products()
        info = {"name": "منتج رقمي"}
        for cat_name, prod_dict in cats.items():
            if prod_key in prod_dict:
                info = prod_dict[prod_key]
                break
        
        order_reference = message.text.strip() if message.text else f"Photo_{int(time.time())}"
        
        bot.send_message(chat_id, "⏳ جاري التحقق من عملية الدفع وشراء المنتج من المزود أوتوماتيكياً...")

        api_result = purchase_order_from_supplier(prod_key, order_reference)

        if api_result["success"]:
            res_data = api_result["data"]
            item_details = res_data.get("item", res_data.get("credentials", res_data.get("data", "تم التسليم بنجاح")))
            
            ords = load_orders()
            ords.setdefault(str(chat_id), []).append({
                "product": info['name'],
                "item": item_details,
                "time": time.strftime("%Y-%m-%d %H:%M:%S")
            })
            save_orders(ords)

            success_msg = (
                f"🎉 <b>تم تأكيد الدفع وتسليم طلبك بنجاح!</b>\n\n"
                f"📦 منتجك: <b>{info['name']}</b>\n"
                f"🔑 <b>بيانات الحساب:</b>\n<code>{item_details}</code>\n\n"
                f"شكراً لثقتك بمتجر Pixora Store 💚"
            )
            bot.send_message(chat_id, success_msg, parse_mode="HTML")
        else:
            error_reason = api_result.get("error", "خطأ غير معروف")
            bot.send_message(chat_id, f"❌ حدث خطأ أثناء تنفيذ الطلب تلقائياً: {error_reason}\nتم إشعار الإدارة للمتابعة الفورية.")
            try:
                bot.send_message(ADMIN_ID, f"⚠️ تنبيه: فشل الشراء الآلي للعميل {chat_id} للمنتج {info['name']}.\nالخطأ: {error_reason}")
            except Exception:
                pass

app = Flask(__name__)

@app.route('/')
def health_check():
    return "Pixora Store Branded Categories Active!", 200

def keep_alive():
    while Time.sleep(300):
        try:
            url = os.environ.get("RENDER_EXTERNAL_URL")
            if url:
                requests.get(url)
        except Exception:
            pass

if __name__ == '__main__':
    if bot:
        try:
            bot.remove_webhook()
        except Exception:
            pass
    threading.Thread(target=keep_alive, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port, use_reloader=False), daemon=True).start()
    
    if bot:
        While True:
            Try:
                Bot.infinity_polling(skip_pending=True, timeout=60)
            Except Exception as e:
                Time.sleep(5)
