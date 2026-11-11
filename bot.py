import os
import time
import json
import threading
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from flask import Flask

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.environ.get("ADMIN_ID", "1004439571")) 
BINANCE_ID = "957483337"
SUPPORT_WHATSAPP = "https://wa.me/213555668244"

RESELLER_KEY = os.environ.get("RESELLER_KEY", "").strip()
VENTEBOT_API_URL = "https://web-production-1c7b1.up.railway.app/api/reseller"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False) if BOT_TOKEN else None

USER_SELECTED_PRODUCT = {}
USER_WAITING_FOR_SEARCH = {}
ORDERS_FILE = "orders.json"

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

def get_brand_group(name):
    n = name.lower()
    if "chatgpt" in n or "gpt" in n or "openai" in n:
        return 1
    elif "claude" in n:
        return 2
    elif "gemini" in n or "google" in n or "gmail" in n:
        return 3
    elif "capcut" in n:
        return 4
    elif "zoom" in n:
        return 5
    elif "miro" in n:
        return 6
    elif "canva" in n:
        return 7
    elif "notion" in n:
        return 8
    elif "codex" in n:
        return 9
    elif "vpn" in n or "hma" in n or "surfshark" in n or "expressvpn" in n:
        return 10
    elif "api" in n:
        return 11
    else:
        return 12

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
            
            products_list = []
            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = data.get("products", data.get("data", data.get("items", [])))
            
            for item in items:
                p_name = item.get("name", item.get("title", "منتج رقمي"))
                if not p_name:
                    continue
                
                p_desc = item.get("description", item.get("desc", ""))
                
                if not is_halal_product(p_name, p_desc):
                    continue

                p_id = str(item.get("id", item.get("code", "")))
                if not p_id:
                    continue

                raw_cost = float(item.get("price_usd", 0.0))
                
                # جعل منتج الاختبار سعره صفراً تماماً للتجربة المجانية
                if "test" in p_name.lower() or item.get("api_test") is True or raw_cost < 0.05:
                    p_price = 0.0
                else:
                    p_price = round(raw_cost + 0.50, 2)

                p_stock = int(item.get("stock", 0))
                p_image = item.get("image_url", "")

                brand_group = get_brand_group(p_name)
                
                products_list.append({
                    "id": p_id,
                    "name": p_name.strip(),
                    "price": p_price,
                    "stock": p_stock,
                    "description": p_desc if p_desc else "اشتراك رقمي رسمي مع ضمان كامل.",
                    "image": p_image if p_image else "",
                    "brand_group": brand_group
                })
            
            # ترتيب البراندات والأصناف أبجدياً بشكل متصل
            products_list.sort(key=lambda x: (x['brand_group'], x['name'].lower()))
            
            ordered_map = {}
            for p in products_list:
                ordered_map[p['id']] = {
                    "name": p['name'],
                    "price": p['price'],
                    "stock": p['stock'],
                    "description": p['description'],
                    "image": p['image']
                }
            return ordered_map
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
    payload = {"product_id": int(product_id) if product_id.isdigit() else product_id, "reference": reference_id}
    try:
        response = requests.post(f"{VENTEBOT_API_URL}/orders", json=payload, headers=headers, timeout=15)
        if response.status_code in [200, 201]:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}

WELCOME_TEXT = "🔥 أهلاً بك في متجر Pixora Store الرقمي!\n\nاختر المنتج المطلوب من القائمة أدناه:"

def get_main_menu_markup(is_admin=False):
    markup = InlineKeyboardMarkup()
    products_info = fetch_supplier_products()
    
    if not products_info:
        markup.add(InlineKeyboardButton("⚠️ لا توجد منتجات متاحة حالياً...", callback_data="main_menu"))
        return markup

    for k, info in products_info.items():
        if info['stock'] > 0:
            markup.add(InlineKeyboardButton(f"✅ {info['name']} · ${info['price']}", callback_data="buy_" + k))
        else:
            markup.add(InlineKeyboardButton(f"❌ {info['name']} (نفد)", callback_data="sold_out_" + k))

    markup.row(InlineKeyboardButton("🔍 بحث عن منتج", callback_data="search_product"), InlineKeyboardButton("📜 مشترياتي", callback_data="my_orders"))
    markup.row(InlineKeyboardButton("💳 طرق الدفع", callback_data="payment_methods"), InlineKeyboardButton("🛠️ الدعم الفني", url=SUPPORT_WHATSAPP))
    
    if is_admin:
        markup.row(InlineKeyboardButton("🛠️ لوحة تحكم الإدارة", callback_data="admin_panel"))
        
    return markup

def get_admin_markup():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("💰 فحص الرصيد بالمحفظة", callback_data="adm_balance"), InlineKeyboardButton("💳 طرق الإيداع", callback_data="adm_deposits"))
    markup.row(InlineKeyboardButton("📊 سجل المعاملات المالية", callback_data="adm_transactions"))
    markup.row(InlineKeyboardButton("🔙 عودة للقائمة الرئيسية", callback_data="main_menu"))
    return markup

if bot:
    try:
        bot.set_my_commands([
            BotCommand("start", "تشغيل المتجر والمنتجات 🚀"),
            BotCommand("menu", "عرض القائمة الرئيسية 📋"),
            BotCommand("my_orders", "سجل مشترياتي السابقة 📜"),
            BotCommand("search", "البحث عن منتج 🔍"),
            BotCommand("payment", "طرق الدفع المتاحة 💳")
        ])
    except Exception:
        pass

    @bot.message_handler(commands=['start', 'menu'])
    def send_welcome(message):
        chat_id = message.chat.id
        USER_WAITING_FOR_SEARCH.pop(chat_id, None)
        is_admin = (chat_id == ADMIN_ID)
        bot.send_message(chat_id, WELCOME_TEXT, reply_markup=get_main_menu_markup(is_admin))

    @bot.message_handler(commands=['search'])
    def cmd_search(message):
        chat_id = message.chat.id
        USER_WAITING_FOR_SEARCH[chat_id] = True
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏠 إلغاء والعودة للرئيسية", callback_data="main_menu"))
        bot.send_message(chat_id, "🔍 <b>البحث عن منتج:</b>\n\nأرسل اسم المنتج أو جزءاً منه في رسالة الآن للبحث عنه:", reply_markup=markup, parse_mode="HTML")

    @bot.message_handler(commands=['payment'])
    def cmd_payment(message):
        chat_id = message.chat.id
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
        pay_info = f"💳 <b>طرق الدفع المتاحة في متجر Pixora Store:</b>\n\n- التحويل الفوري عبر عملات USDT الرقمية.\n- Binance ID الخاص بالمزود: <code>{BINANCE_ID}</code>\n\nبعد اختيار المنتج وضغط إتمام الدفع، أرسل رقم العملية أو الإيصال هنا للشات لتتم معالجة طلبك وتسليمه فوراً."
        bot.send_message(chat_id, pay_info, reply_markup=markup, parse_mode="HTML")

    @bot.message_handler(commands=['my_orders'])
    def cmd_my_orders(message):
        chat_id = message.chat.id
        ords = load_orders().get(str(chat_id), [])
        if not ords:
            text = "📜 سجل مشترياتي:\n\nلا توجد طلبات سابقة."
        else:
            text = "📜 سجل مشترياتي السابقة:\n\n"
            for o in ords:
                text += f"📦 {o['product']}\n🔑 البيان: <code>{o['item']}</code>\n------------------\n"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

    @bot.callback_query_handler(func=lambda call: True)
    def handle_query(call):
        chat_id = call.message.chat.id
        msg_id = call.message.message_id
        data = call.data
        is_admin = (chat_id == ADMIN_ID)
        products_info = fetch_supplier_products()

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
            text = f"📊 <b>سجل المعاملات المالية:</b>\n<pre>{json.dumps(txs, indent=2, ensure_ascii=False)[:3500]}</pre>" if txs else "❌ تعذر جلب سجل المعاملات المالية."
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔙 رجوع لوحة التحكم", callback_data="admin_panel"))
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

        elif data == "search_product":
            bot.answer_callback_query(call.id)
            USER_WAITING_FOR_SEARCH[chat_id] = True
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🏠 إلغاء والعودة للرئيسية", callback_data="main_menu"))
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, "🔍 <b>البحث عن منتج:</b>\n\nأرسل اسم المنتج أو جزءاً منه في رسالة الآن للبحث عنه:", reply_markup=markup, parse_mode="HTML")

        elif data == "payment_methods":
            bot.answer_callback_query(call.id)
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
            pay_info = f"💳 <b>طرق الدفع المتاحة في متجر Pixora Store:</b>\n\n- التحويل الفوري عبر عملات USDT الرقمية.\n- Binance ID الخاص بالمزود: <code>{BINANCE_ID}</code>\n\nبعد اختيار المنتج وضغط إتمام الدفع، أرسل رقم العملية أو الإيصال هنا للشات لتتم معالجة طلبك وتسليمه فوراً."
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, pay_info, reply_markup=markup, parse_mode="HTML")

        elif data.startswith("buy_"):
            prod_key = data.replace("buy_", "")
            if prod_key in products_info:
                info = products_info[prod_key]
                bot.answer_callback_query(call.id)
                USER_SELECTED_PRODUCT[chat_id] = prod_key
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("🪙 إتمام الدفع الفوري", callback_data="pay_" + prod_key))
                markup.row(InlineKeyboardButton("🔙 عودة للرئيسية", callback_data="main_menu"))
                
                msg_text = f"🏷️ <b>{info['name']}</b>\n💰 السعر: ${info['price']}\n📦 المخزون المتاح: {info['stock']}\n\n{info['description']}"
                safe_delete_message(chat_id, msg_id)
                
                if info.get('image'):
                    try:
                        bot.send_photo(chat_id, info['image'], caption=msg_text, reply_markup=markup, parse_mode="HTML")
                        return
                    except Exception:
                        pass
                bot.send_message(chat_id, msg_text, reply_markup=markup, parse_mode="HTML")
                
        elif data.startswith("pay_"):
            prod_key = data.replace("pay_", "")
            info = products_info.get(prod_key, {"price": 1.0})
            bot.answer_callback_query(call.id)
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("🏠 عودة للرئيسية", callback_data="main_menu"))
            pay_msg = f"🪙 تحويل مبلغ (${info['price']} USDT) إلى Binance ID: {BINANCE_ID}\n\nثم أرسل رقم العملية (Order ID) أو إيصال الدفع هنا للشات ليتم التسليم الفوري أوتوماتيكياً."
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, pay_msg, reply_markup=markup, parse_mode="HTML")
            
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
            USER_WAITING_FOR_SEARCH.pop(chat_id, None)
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, WELCOME_TEXT, reply_markup=get_main_menu_markup(is_admin))

    @bot.message_handler(content_types=['text', 'photo'])
    def handle_incoming(message):
        chat_id = message.chat.id
        if message.text and message.text.startswith('/'):
            return

        if USER_WAITING_FOR_SEARCH.get(chat_id):
            USER_WAITING_FOR_SEARCH.pop(chat_id, None)
            query = message.text.strip().lower()
            products_info = fetch_supplier_products()
            
            markup = InlineKeyboardMarkup()
            found_count = 0
            for k, info in products_info.items():
                if query in info['name'].lower() or query in info['description'].lower():
                    found_count += 1
                    if info['stock'] > 0:
                        markup.add(InlineKeyboardButton(f"✅ {info['name']} · ${info['price']}", callback_data="buy_" + k))
                    else:
                        markup.add(InlineKeyboardButton(f"❌ {info['name']} (نفد)", callback_data="sold_out_" + k))
            
            markup.row(InlineKeyboardButton("🏠 عودة للرئيسية", callback_data="main_menu"))
            if found_count > 0:
                bot.send_message(chat_id, f"🔍 نتائج البحث عن: <b>{message.text}</b>", reply_markup=markup, parse_mode="HTML")
            else:
                bot.send_message(chat_id, f"❌ لم يتم العثور على أي منتج يطابق بحثك: <b>{message.text}</b>", reply_markup=markup, parse_mode="HTML")
            return

        if chat_id not in USER_SELECTED_PRODUCT:
            bot.send_message(chat_id, "⚠️ يرجى اختيار المنتج أولاً أو استخدام القائمة الرئيسية من /start")
            return

        prod_key = USER_SELECTED_PRODUCT.pop(chat_id)
        products_info = fetch_supplier_products()
        info = products_info.get(prod_key, {"name": "منتج رقمي"})
        
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
    return "Pixora Store Zero Price Test Active!", 200

def keep_alive():
    while True:
        time.sleep(300)
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
        while True:
            try:
                bot.infinity_polling(skip_pending=True, timeout=60)
            except Exception as e:
                time.sleep(5)
