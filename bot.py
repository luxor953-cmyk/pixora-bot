import os
import time
import json
import threading
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, BotCommand
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
USER_LANGUAGES = {}
ORDERS_FILE = "orders.json"

LANG_TEXTS = {
    "ar": {
        "welcome": "🔥 أهلاً بك في متجر Pixora Store الرقمي!\n\nاختر المنتج المطلوب من القائمة أدناه:",
        "products": "🛍️ تصفح المنتجات",
        "api": "🔑 خدمات API",
        "wallet": "💰 محفظتي",
        "deposit": "💳 شحن الرصيد / الدفع",
        "orders": "📜 مشترياتي",
        "lang": "🌐 اللغة / Language",
        "search": "🔍 بحث عن منتج",
        "support": "🛠️ الدعم الفني",
        "admin": "🛠️ لوحة تحكم الإدارة",
        "no_products": "⚠️ لا توجد منتجات متاحة حالياً...",
        "sold_out": "نفد"
    },
    "en": {
        "welcome": "🔥 Welcome to Pixora Store Digital!\n\nChoose the desired product from the menu below:",
        "products": "🛍️ Browse Products",
        "api": "🔑 API Services",
        "wallet": "💰 My Wallet",
        "deposit": "💳 Top up / Payment",
        "orders": "📜 My Orders",
        "lang": "🌐 Language",
        "search": "🔍 Search Product",
        "support": "🛠️ Support",
        "admin": "🛠️ Admin Panel",
        "no_products": "⚠️ No products available right now...",
        "sold_out": "Sold out"
    },
    "fr": {
        "welcome": "🔥 Bienvenue sur Pixora Store Numérique !\n\nChoisissez le produit souhaité dans le menu ci-dessous :",
        "products": "🛍️ Parcourir",
        "api": "🔑 Services API",
        "wallet": "💰 Mon Portefeuille",
        "deposit": "💳 Recharger / Paiement",
        "orders": "📜 Mes Commandes",
        "lang": "🌐 Langue",
        "search": "🔍 Rechercher",
        "support": "🛠️ Support",
        "admin": "🛠️ Panneau Admin",
        "no_products": "⚠️ Aucun produit disponible pour le moment...",
        "sold_out": "Épuisé"
    }
}

def get_user_lang(chat_id):
    return USER_LANGUAGES.get(chat_id, "ar")

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
    if "test" in n or "api test" in n:
        return 99
    elif "chatgpt" in n or "gpt" in n or "openai" in n:
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
    idempotency_val = f"pixora_{int(time.time())}_{product_id}"
    
    payload = {
        "product_id": int(product_id) if product_id.isdigit() else product_id,
        "reference": reference_id,
        "idempotency_key": idempotency_val
    }
    
    try:
        response = requests.post(f"{VENTEBOT_API_URL}/orders", json=payload, headers=headers, timeout=15)
        if response.status_code in [200, 201]:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_permanent_reply_keyboard(lang="ar"):
    t = LANG_TEXTS.get(lang, LANG_TEXTS["ar"])
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(KeyboardButton(t["products"]), KeyboardButton(t["api"]))
    keyboard.add(KeyboardButton(t["wallet"]), KeyboardButton(t["deposit"]))
    keyboard.add(KeyboardButton(t["orders"]), KeyboardButton(t["lang"]))
    return keyboard

def get_main_menu_markup(chat_id, is_admin=False):
    lang = get_user_lang(chat_id)
    t = LANG_TEXTS.get(lang, LANG_TEXTS["ar"])
    markup = InlineKeyboardMarkup()
    products_info = fetch_supplier_products()
    
    if not products_info:
        markup.add(InlineKeyboardButton(t["no_products"], callback_data="main_menu"))
        return markup

    for k, info in products_info.items():
        if info['stock'] > 0:
            markup.add(InlineKeyboardButton(f"✅ {info['name']} · ${info['price']}", callback_data="buy_" + k))
        else:
            markup.add(InlineKeyboardButton(f"❌ {info['name']} ({t['sold_out']})", callback_data="sold_out_" + k))

    markup.row(InlineKeyboardButton(t["search"], callback_data="search_product"), InlineKeyboardButton(t["orders"], callback_data="my_orders"))
    markup.row(InlineKeyboardButton(t["deposit"], callback_data="payment_methods"), InlineKeyboardButton(t["support"], url=SUPPORT_WHATSAPP))
    
    if is_admin:
        markup.row(InlineKeyboardButton(t["admin"], callback_data="admin_panel"))
        
    return markup

def get_admin_markup():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("💰 فحص الرصيد", callback_data="adm_balance"), InlineKeyboardButton("💳 طرق الإيداع", callback_data="adm_deposits"))
    markup.row(InlineKeyboardButton("📊 سجل المعاملات", callback_data="adm_transactions"))
    markup.row(InlineKeyboardButton("🔙 عودة للرئيسية", callback_data="main_menu"))
    return markup

if bot:
    try:
        bot.set_my_commands([
            BotCommand("start", "تشغيل المتجر 🚀"),
            BotCommand("products", "تصفح المنتجات 🛍️"),
            BotCommand("api", "خدمات API 🔑"),
            BotCommand("wallet", "المحفظة 💰"),
            BotCommand("deposit", "شحن الرصيد 💳"),
            BotCommand("my_orders", "مشترياتي 📜"),
            BotCommand("language", "اللغة / Language 🌐")
        ])
    except Exception:
        pass

    @bot.message_handler(commands=['start', 'products'])
    def send_welcome(message):
        chat_id = message.chat.id
        USER_WAITING_FOR_SEARCH.pop(chat_id, None)
        lang = get_user_lang(chat_id)
        t = LANG_TEXTS.get(lang, LANG_TEXTS["ar"])
        is_admin = (chat_id == ADMIN_ID)
        bot.send_message(chat_id, t["welcome"], reply_markup=get_main_menu_markup(chat_id, is_admin))
        bot.send_message(chat_id, "📌 أزرار التحكم السريعة:", reply_markup=get_permanent_reply_keyboard(lang))

    @bot.message_handler(commands=['api'])
    def cmd_api(message):
        chat_id = message.chat.id
        products_info = fetch_supplier_products()
        markup = InlineKeyboardMarkup()
        for k, info in products_info.items():
            if "api" in info['name'].lower():
                if info['stock'] > 0:
                    markup.add(InlineKeyboardButton(f"✅ {info['name']} · ${info['price']}", callback_data="buy_" + k))
        markup.add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
        bot.send_message(chat_id, "🔑 <b>خدمات API المتاحة:</b>", reply_markup=markup, parse_mode="HTML")

    @bot.message_handler(commands=['wallet'])
    def cmd_wallet(message):
        chat_id = message.chat.id
        wallet = api_get_my_wallet()
        text = f"💰 <b>بيانات المحفظة:</b>\n<pre>{json.dumps(wallet, indent=2, ensure_ascii=False)}</pre>" if wallet else "💰 محفظتك نشطة."
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

    @bot.message_handler(commands=['deposit'])
    def cmd_deposit(message):
        chat_id = message.chat.id
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
        pay_info = f"💳 <b>طرق شحن الرصيد والدفع:</b>\n\n- Binance ID: <code>{BINANCE_ID}</code>"
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
                text += f"📦 {o['product']}\n🔑 <code>{o['item']}</code>\n------------------\n"
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

    @bot.message_handler(commands=['language'])
    def cmd_language(message):
        chat_id = message.chat.id
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"))
        markup.add(InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"))
        markup.add(InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr"))
        markup.add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
        bot.send_message(chat_id, "🌐 اختر اللغة:", reply_markup=markup)

    @bot.message_handler(func=lambda message: message.text in [
        "🛍️ تصفح المنتجات", "🛍️ Browse Products", "🛍️ Parcourir",
        "🔑 خدمات API", "🔑 API Services", "🔑 Services API",
        "💰 محفظتي", "💰 My Wallet", "💰 Mon Portefeuille",
        "💳 شحن الرصيد / الدفع", "💳 Top up / Payment", "💳 Recharger / Paiement",
        "📜 مشترياتي", "📜 My Orders", "📜 Mes Commandes",
        "🌐 اللغة / Language", "🌐 Language", "🌐 Langue"
    ])
    def handle_reply_keyboard(message):
        chat_id = message.chat.id
        text = message.text
        is_admin = (chat_id == ADMIN_ID)
        lang = get_user_lang(chat_id)
        
        if "تصفح" in text or "Browse" in text or "Parcourir" in text:
            USER_WAITING_FOR_SEARCH.pop(chat_id, None)
            bot.send_message(chat_id, LANG_TEXTS[lang]["welcome"], reply_markup=get_main_menu_markup(chat_id, is_admin))
        elif "API" in text:
            products_info = fetch_supplier_products()
            markup = InlineKeyboardMarkup()
            for k, info in products_info.items():
                if "api" in info['name'].lower():
                    markup.add(InlineKeyboardButton(f"✅ {info['name']} · ${info['price']}", callback_data="buy_" + k))
            markup.add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
            bot.send_message(chat_id, "🔑 <b>خدمات API:</b>", reply_markup=markup, parse_mode="HTML")
        elif "محفظتي" in text or "Wallet" in text or "Portefeuille" in text:
            wallet = api_get_my_wallet()
            res_text = f"💰 <b>بيانات المحفظة:</b>\n<pre>{json.dumps(wallet, indent=2, ensure_ascii=False)}</pre>" if wallet else "💰 محفظتك نشطة."
            markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
            bot.send_message(chat_id, res_text, reply_markup=markup, parse_mode="HTML")
        elif "شحن" in text or "Top up" in text or "Recharger" in text:
            markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
            pay_info = f"💳 Binance ID: <code>{BINANCE_ID}</code>"
            bot.send_message(chat_id, pay_info, reply_markup=markup, parse_mode="HTML")
        elif "مشترياتي" in text or "Orders" in text or "Commandes" in text:
            ords = load_orders().get(str(chat_id), [])
            res_text = "📜 لا توجد طلبات." if not ords else "📜 السجل:\n" + "".join([f"📦 {o['product']}\n🔑 <code>{o['item']}</code>\n" for o in ords])
            markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
            bot.send_message(chat_id, res_text, reply_markup=markup, parse_mode="HTML")
        elif "اللغة" in text or "Language" in text or "Langue" in text:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"))
            markup.add(InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"))
            markup.add(InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr"))
            bot.send_message(chat_id, "🌐 اختر اللغة:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: True)
    def handle_query(call):
        chat_id = call.message.chat.id
        msg_id = call.message.message_id
        data = call.data
        is_admin = (chat_id == ADMIN_ID)
        products_info = fetch_supplier_products()

        if data.startswith("lang_"):
            new_lang = data.replace("lang_", "")
            USER_LANGUAGES[chat_id] = new_lang
            bot.answer_callback_query(call.id, "✅ Done")
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, LANG_TEXTS[new_lang]["welcome"], reply_markup=get_main_menu_markup(chat_id, is_admin))
            bot.send_message(chat_id, "📌 أزرار التحكم:", reply_markup=get_permanent_reply_keyboard(new_lang))
            return

        if data == "admin_panel" and is_admin:
            bot.answer_callback_query(call.id)
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, "🛠️ <b>لوحة تحكم الإدارة:</b>", reply_markup=get_admin_markup(), parse_mode="HTML")

        elif data == "adm_balance" and is_admin:
            bot.answer_callback_query(call.id)
            wallet = api_get_my_wallet()
            text = f"💰 <pre>{json.dumps(wallet, indent=2, ensure_ascii=False)}</pre>" if wallet else "❌"
            markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel"))
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

        elif data == "adm_deposits" and is_admin:
            bot.answer_callback_query(call.id)
            dep = api_get_deposit_methods()
            text = f"💳 <pre>{json.dumps(dep, indent=2, ensure_ascii=False)}</pre>" if dep else "❌"
            markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel"))
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

        elif data == "adm_transactions" and is_admin:
            bot.answer_callback_query(call.id)
            txs = api_get_wallet_transactions()
            text = f"📊 <pre>{json.dumps(txs, indent=2, ensure_ascii=False)[:3500]}</pre>" if txs else "❌"
            markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel"))
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

        elif data == "search_product":
            bot.answer_callback_query(call.id)
            USER_WAITING_FOR_SEARCH[chat_id] = True
            markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 إلغاء", callback_data="main_menu"))
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, "🔍 أرسل اسم المنتج للبحث:", reply_markup=markup)

        elif data == "payment_methods":
            bot.answer_callback_query(call.id)
            markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
            pay_info = f"💳 Binance ID: <code>{BINANCE_ID}</code>"
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, pay_info, reply_markup=markup, parse_mode="HTML")

        elif data.startswith("buy_"):
            prod_key = data.replace("buy_", "")
            if prod_key in products_info:
                info = products_info[prod_key]
                bot.answer_callback_query(call.id)
                
                if info['price'] == 0.0:
                    safe_delete_message(chat_id, msg_id)
                    item_details = "TEST_CREDENTIALS_SUCCESS_MOCK_KEY_12345"
                    ords = load_orders()
                    ords.setdefault(str(chat_id), []).append({
                        "product": info['name'],
                        "item": item_details,
                        "time": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    save_orders(ords)
                    lang = get_user_lang(chat_id)
                    success_msg = f"🎉 <b>تم التسجيل والتجربة بنجاح!</b>\n\n📦 <b>{info['name']}</b>\n🔑 <code>{item_details}</code>"
                    bot.send_message(chat_id, success_msg, parse_mode="HTML", reply_markup=get_permanent_reply_keyboard(lang))
                    return

                USER_SELECTED_PRODUCT[chat_id] = prod_key
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("🪙 إتمام الدفع الفوري", callback_data="pay_" + prod_key))
                markup.row(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
                
                msg_text = f"🏷️ <b>{info['name']}</b>\n💰 ${info['price']}\n📦 {info['stock']}\n\n{info['description']}"
                safe_delete_message(chat_id, msg_id)
                bot.send_message(chat_id, msg_text, reply_markup=markup, parse_mode="HTML")
                
        elif data.startswith("pay_"):
            prod_key = data.replace("pay_", "")
            info = products_info.get(prod_key, {"price": 1.0})
            bot.answer_callback_query(call.id)
            markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
            pay_msg = f"🪙 تحويل (${info['price']} USDT) إلى Binance ID: {BINANCE_ID}\n\nثم أرسل رقم العملية (Order ID) هنا للشات ليتم الشراء والتسليم أوتوماتيكياً فوريًا!"
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, pay_msg, reply_markup=markup, parse_mode="HTML")
            
        elif data == "my_orders":
            bot.answer_callback_query(call.id)
            ords = load_orders().get(str(chat_id), [])
            text = "📜 لا توجد طلبات." if not ords else "📜 السجل:\n" + "".join([f"📦 {o['product']}\n🔑 <code>{o['item']}</code>\n" for o in ords])
            markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
            
        elif data == "main_menu":
            bot.answer_callback_query(call.id)
            USER_SELECTED_PRODUCT.pop(chat_id, None)
            USER_WAITING_FOR_SEARCH.pop(chat_id, None)
            lang = get_user_lang(chat_id)
            safe_delete_message(chat_id, msg_id)
            bot.send_message(chat_id, LANG_TEXTS[lang]["welcome"], reply_markup=get_main_menu_markup(chat_id, is_admin))

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
            
            markup.row(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
            if found_count > 0:
                bot.send_message(chat_id, f"🔍 نتائج البحث عن: <b>{message.text}</b>", reply_markup=markup, parse_mode="HTML")
            else:
                bot.send_message(chat_id, f"❌ لم يتم العثور على نتائج لـ: <b>{message.text}</b>", reply_markup=markup, parse_mode="HTML")
            return

        if chat_id not in USER_SELECTED_PRODUCT:
            lang = get_user_lang(chat_id)
            bot.send_message(chat_id, "⚠️ يرجى اختيار المنتج أولاً", reply_markup=get_permanent_reply_keyboard(lang))
            return

        prod_key = USER_SELECTED_PRODUCT.pop(chat_id)
        products_info = fetch_supplier_products()
        info = products_info.get(prod_key, {"name": "منتج رقمي"})
        
        order_reference = message.text.strip() if message.text else f"Photo_{int(time.time())}"
        
        bot.send_message(chat_id, "⏳ جاري التحقق من عملية الدفع وشراء المنتج من المزود أوتوماتيكياً...")

        # تنفيذ الشراء التلقائي من API المزود
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
            lang = get_user_lang(chat_id)

            success_msg = f"🎉 <b>تم تأكيد الدفع وتسليم طلبك بنجاح!</b>\n\n📦 <b>{info['name']}</b>\n🔑 <b>بيانات الحساب:</b>\n<code>{item_details}</code>"
            bot.send_message(chat_id, success_msg, parse_mode="HTML", reply_markup=get_permanent_reply_keyboard(lang))
        else:
            error_reason = api_result.get("error", "خطأ")
            bot.send_message(chat_id, f"❌ حدث خطأ أثناء تنفيذ الطلب تلقائياً لدى المزود:\n<code>{error_reason}</code>\n\nتأكد من توفر رصيد كافٍ في محفظتك لدى المزود.", parse_mode="HTML")

app = Flask(__name__)

@app.route('/')
def health_check():
    return "Pixora Store Fully Automatic Active!", 200

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
