import os
import time
import json
import threading
import requests
import hmac
import hashlib
from urllib.parse import urlencode
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, BotCommand
from flask import Flask

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.environ.get("ADMIN_ID", "1004439571")) 
BINANCE_ID = "957483337"
SUPPORT_WHATSAPP = "https://wa.me/213555668244"

RESELLER_KEY = os.environ.get("RESELLER_KEY", "").strip()
VENTEBOT_API_URL = "https://web-production-1c7b1.up.railway.app/api/reseller"

BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY", "").strip()
BINANCE_SECRET_KEY = os.environ.get("BINANCE_SECRET_KEY", "").strip()

bot = telebot.TeleBot(BOT_TOKEN, threaded=False) if BOT_TOKEN else None

USER_SELECTED_PRODUCT = {}
USER_WAITING_FOR_SEARCH = {}
USER_LANGUAGES = {}
ORDERS_FILE = "orders.json"

LANG_TEXTS = {
    "ar": {
        "welcome": "🔥 أهلاً بك في متجر Pixora Store الرقمي!\n\nاختر القسم أو المنتج المطلوب من القائمة أدناه:",
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
        "welcome": "🔥 Welcome to Pixora Store Digital!\n\nChoose the desired category or product below:",
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
        "welcome": "🔥 Bienvenue sur Pixora Store Numérique !\n\nChoisissez la catégorie ou le produit ci-dessous :",
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

def get_product_family(name):
    n = name.lower()
    if "test" in n or "api test" in n:
        return "tests"
    elif "chatgpt" in n or "gpt" in n or "openai" in n:
        return "chatgpt"
    elif "claude" in n:
        return "claude"
    elif "gemini" in n or "google" in n or "gmail" in n:
        return "google"
    elif "capcut" in n:
        return "capcut"
    elif "canva" in n:
        return "canva"
    elif "zoom" in n:
        return "zoom"
    elif "elevenlabs" in n:
        return "elevenlabs"
    elif "gamma" in n:
        return "gamma"
    elif "lovable" in n:
        return "lovable"
    elif "microsoft" in n:
        return "microsoft"
    elif "miro" in n:
        return "miro"
    elif "notion" in n:
        return "notion"
    elif "quizlet" in n:
        return "quizlet"
    elif "railway" in n:
        return "railway"
    elif "wordwall" in n:
        return "wordwall"
    elif "api" in n:
        return "api_services"
    elif "vpn" in n or "hma" in n or "surfshark" in n or "expressvpn" in n:
        return "vpn"
    else:
        return None

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
            items = data if isinstance(data, list) else data.get("products", data.get("data", data.get("items", [])))
            
            for item in items:
                p_name = item.get("name", item.get("title", "منتج رقمي"))
                if not p_name: continue
                p_desc = item.get("description", item.get("desc", ""))
                if not is_halal_product(p_name, p_desc): continue
                p_id = str(item.get("id", item.get("code", "")))
                if not p_id: continue
                raw_cost = float(item.get("price_usd", 0.0))
                p_price = 0.0 if ("test" in p_name.lower() or item.get("api_test") is True or raw_cost < 0.05) else round(raw_cost + 0.50, 2)
                
                family = get_product_family(p_name)
                products_list.append({
                    "id": p_id,
                    "name": p_name.strip(),
                    "price": p_price,
                    "stock": int(item.get("stock", 0)),
                    "description": p_desc if p_desc else "اشتراك رقمي رسمي مع ضمان كامل.",
                    "image": item.get("image_url", ""),
                    "family": family
                })
            
            products_list.sort(key=lambda x: x['name'].lower())
            return {p['id']: p for p in products_list}
    except Exception as e:
        print("Error fetching supplier products:", e)
    return {}

def api_get_my_wallet():
    if not RESELLER_KEY: return None
    try:
        res = requests.get(f"{VENTEBOT_API_URL}/me", headers={"X-Reseller-Key": RESELLER_KEY}, timeout=10)
        if res.status_code == 200: return res.json()
    except Exception: pass
    return None

def api_get_wallet_transactions():
    if not RESELLER_KEY: return None
    try:
        res = requests.get(f"{VENTEBOT_API_URL}/wallet/transactions", headers={"X-Reseller-Key": RESELLER_KEY}, timeout=10)
        if res.status_code == 200: return res.json()
    except Exception: pass
    return None

def api_get_deposit_methods():
    if not RESELLER_KEY: return None
    try:
        res = requests.get(f"{VENTEBOT_API_URL}/wallet/deposit-methods", headers={"X-Reseller-Key": RESELLER_KEY}, timeout=10)
        if res.status_code == 200: return res.json()
    except Exception: pass
    return None

def purchase_order_from_supplier(product_id, reference_id):
    if not RESELLER_KEY: return {"success": False, "error": "No reseller key"}
    headers = {"X-Reseller-Key": RESELLER_KEY, "Content-Type": "application/json"}
    payload = {"product_id": int(product_id) if product_id.isdigit() else product_id, "reference": reference_id, "idempotency_key": f"pixora_{int(time.time())}_{product_id}"}
    try:
        response = requests.post(f"{VENTEBOT_API_URL}/orders", json=payload, headers=headers, timeout=15)
        if response.status_code in [200, 201]: return {"success": True, "data": response.json()}
        else: return {"success": False, "error": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}

def verify_binance_transaction(order_id, expected_amount):
    if not BINANCE_API_KEY or not BINANCE_SECRET_KEY:
        return {"success": False, "error": "لم يتم إضافة مفاتيح Binance API."}
    try:
        timestamp = int(time.time() * 1000)
        query_string = urlencode({"timestamp": timestamp, "limit": 50})
        signature = hmac.new(BINANCE_SECRET_KEY.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()
        url = f"https://api.binance.com/sapi/v1/pay/transactions?{query_string}&signature={signature}"
        response = requests.get(url, headers={"X-MBX-APIKEY": BINANCE_API_KEY}, timeout=10)
        
        if response.status_code == 200:
            transactions = response.json().get("data", [])
            for tx in transactions:
                if str(tx.get("orderId")) == str(order_id) or str(tx.get("transactionId")) == str(order_id):
                    actual_amount = float(tx.get("amount", 0))
                    if actual_amount >= float(expected_amount): return {"success": True}
                    else: return {"success": False, "error": f"المبلغ المحول (${actual_amount}) أقل من سعر المنتج (${expected_amount})."}
            return {"success": False, "error": "رقم العملية غير موجود أو لم يصل المبلغ بعد."}
        else:
            return {"success": False, "error": f"تعذر الاتصال بباينانس (الكود {response.status_code})."}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_main_menu_markup(chat_id, is_admin=False):
    t = LANG_TEXTS.get(get_user_lang(chat_id), LANG_TEXTS["ar"])
    markup = InlineKeyboardMarkup()
    products_info = fetch_supplier_products()
    
    if not products_info:
        markup.add(InlineKeyboardButton(t["no_products"], callback_data="main_menu"))
        return markup

    added_families = set()

    for k, info in products_info.items():
        fam = info['family']
        if fam:
            if fam not in added_families:
                added_families.add(fam)
                fam_names = {
                    "chatgpt": "🤖 عائلة اشتراكات ChatGPT",
                    "claude": "🧠 عائلة اشتراكات Claude AI",
                    "google": "✨ عائلة Google & Gmail",
                    "capcut": "🎬 عائلة أدوات CapCut",
                    "canva": "🎨 عائلة تصاميم Canva",
                    "zoom": "📹 عائلة اشتراكات Zoom",
                    "elevenlabs": "🎙️ عائلة أدوات ElevenLabs",
                    "gamma": "📊 عائلة عروض Gamma AI",
                    "lovable": "💻 عائلة منصة Lovable",
                    "microsoft": "🪟 عائلة منتجات Microsoft",
                    "miro": "📌 عائلة لوحات Miro",
                    "notion": "📝 عائلة أدوات Notion",
                    "quizlet": "📚 عائلة تعليم Quizlet",
                    "railway": "⚙️ عائلة استضافة Railway",
                    "wordwall": "🎮 عائلة أنشطة Wordwall",
                    "api_services": "🔑 خدمات وباقات API",
                    "vpn": "🔒 خدمات وشبكات VPN",
                    "tests": "🧪 منتجات التجربة"
                }
                display_name = fam_names.get(fam, f"📁 قسم {fam.upper()}")
                markup.add(InlineKeyboardButton(display_name, callback_data="fam_" + fam))
        else:
            if info['stock'] > 0:
                markup.add(InlineKeyboardButton(f"✅ {info['name']} · ${info['price']}", callback_data="buy_" + k))
            else:
                markup.add(InlineKeyboardButton(f"❌ {info['name']} ({t['sold_out']})", callback_data="sold_out_" + k))

    markup.row(InlineKeyboardButton(t["search"], callback_data="search_product"), InlineKeyboardButton(t["orders"], callback_data="my_orders"))
    markup.row(InlineKeyboardButton(t["deposit"], callback_data="payment_methods"), InlineKeyboardButton(t["support"], url=SUPPORT_WHATSAPP))
    markup.row(InlineKeyboardButton(t["api"], callback_data="show_apis"), InlineKeyboardButton(t["lang"], callback_data="menu_lang"))
    if is_admin: markup.row(InlineKeyboardButton(t["admin"], callback_data="admin_panel"))
    return markup

def get_admin_markup():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("💰 فحص الرصيد", callback_data="adm_balance"), InlineKeyboardButton("💳 طرق الإيداع", callback_data="adm_deposits"))
    markup.row(InlineKeyboardButton("📊 سجل المعاملات", callback_data="adm_transactions"), InlineKeyboardButton("🔙 الرئيسية", callback_data="main_menu"))
    return markup

if bot:
    try:
        bot.set_my_commands([
            BotCommand("start", "تشغيل المتجر 🚀"),
            BotCommand("products", "تصفح المنتجات 🛍️"),
            BotCommand("my_orders", "مشترياتي 📜"),
            BotCommand("language", "اللغة / Language 🌐")
        ])
    except Exception: pass

    @bot.message_handler(commands=['start', 'products'])
    def send_welcome(message):
        chat_id = message.chat.id
        USER_WAITING_FOR_SEARCH.pop(chat_id, None)
        
        msg_clear = bot.send_message(chat_id, "🔄", reply_markup=ReplyKeyboardRemove())
        try: bot.delete_message(chat_id, msg_clear.message_id)
        except: pass

        t = LANG_TEXTS.get(get_user_lang(chat_id), LANG_TEXTS["ar"])
        bot.send_message(chat_id, t["welcome"], reply_markup=get_main_menu_markup(chat_id, chat_id == ADMIN_ID))

    @bot.message_handler(commands=['my_orders'])
    def cmd_my_orders(message):
        chat_id = message.chat.id
        ords = load_orders().get(str(chat_id), [])
        text = "📜 لا توجد طلبات سابقة." if not ords else "📜 سجل مشترياتي السابقة:\n\n" + "".join([f"📦 {o['product']}\n🔑 <code>{o['item']}</code>\n------------------\n" for o in ords])
        bot.send_message(chat_id, text, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu")), parse_mode="HTML")

    @bot.message_handler(commands=['language'])
    def cmd_language(message):
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"), InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"), InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr"))
        bot.send_message(message.chat.id, "🌐 اختر اللغة:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: True)
    def handle_query(call):
        chat_id = call.message.chat.id
        msg_id = call.message.message_id
        data = call.data
        is_admin = (chat_id == ADMIN_ID)
        products_info = fetch_supplier_products()

        if data.startswith("lang_"):
            USER_LANGUAGES[chat_id] = data.replace("lang_", "")
            bot.answer_callback_query(call.id, "✅ Done")
            try:
                bot.edit_message_text(LANG_TEXTS[USER_LANGUAGES[chat_id]]["welcome"], chat_id, msg_id, reply_markup=get_main_menu_markup(chat_id, is_admin), parse_mode="HTML")
            except:
                bot.send_message(chat_id, LANG_TEXTS[USER_LANGUAGES[chat_id]]["welcome"], reply_markup=get_main_menu_markup(chat_id, is_admin), parse_mode="HTML")

        elif data.startswith("fam_"):
            fam_key = data.replace("fam_", "")
            bot.answer_callback_query(call.id)
            markup = InlineKeyboardMarkup()
            for k, info in products_info.items():
                if info['family'] == fam_key:
                    if info['stock'] > 0:
                        markup.add(InlineKeyboardButton(f"✅ {info['name']} · ${info['price']}", callback_data="buy_" + k))
                    else:
                        markup.add(InlineKeyboardButton(f"❌ {info['name']} (نفد)", callback_data="sold_out_" + k))
            markup.add(InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="main_menu"))
            try:
                bot.edit_message_text(f"📁 <b>خيارات وخطط القسم:</b>", chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
            except:
                bot.send_message(chat_id, f"📁 <b>خيارات وخطط القسم:</b>", chat_id, msg_id, reply_markup=markup, parse_mode="HTML")

        elif data == "menu_lang":
            bot.answer_callback_query(call.id)
            markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"), InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"), InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr"), InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
            try:
                bot.edit_message_text("🌐 اختر اللغة:", chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
            except:
                bot.send_message(chat_id, "🌐 اختر اللغة:", reply_markup=markup, parse_mode="HTML")

        elif data == "show_apis":
            bot.answer_callback_query(call.id)
            markup = InlineKeyboardMarkup()
            for k, info in products_info.items():
                if "api" in info['name'].lower() and info['stock'] > 0:
                    markup.add(InlineKeyboardButton(f"✅ {info['name']} · ${info['price']}", callback_data="buy_" + k))
            markup.add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
            try:
                bot.edit_message_text("🔑 <b>خدمات API المتاحة:</b>", chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
            except:
                bot.send_message(chat_id, "🔑 <b>خدمات API المتاحة:</b>", reply_markup=markup, parse_mode="HTML")

        elif data == "admin_panel" and is_admin:
            bot.answer_callback_query(call.id)
            try:
                bot.edit_message_text("🛠️ <b>لوحة تحكم الإدارة:</b>", chat_id, msg_id, reply_markup=get_admin_markup(), parse_mode="HTML")
            except:
                bot.send_message(chat_id, "🛠️ <b>لوحة تحكم الإدارة:</b>", reply_markup=get_admin_markup(), parse_mode="HTML")

        elif data == "adm_balance" and is_admin:
            bot.answer_callback_query(call.id)
            wallet = api_get_my_wallet()
            text = f"💰 <pre>{json.dumps(wallet, indent=2, ensure_ascii=False)}</pre>" if wallet else "❌"
            try:
                bot.edit_message_text(text, chat_id, msg_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")), parse_mode="HTML")
            except:
                bot.send_message(chat_id, text, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")), parse_mode="HTML")

        elif data == "adm_deposits" and is_admin:
            bot.answer_callback_query(call.id)
            dep = api_get_deposit_methods()
            text = f"💳 <pre>{json.dumps(dep, indent=2, ensure_ascii=False)}</pre>" if dep else "❌"
            try:
                bot.edit_message_text(text, chat_id, msg_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")), parse_mode="HTML")
            except:
                bot.send_message(chat_id, text, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")), parse_mode="HTML")

        elif data == "adm_transactions" and is_admin:
            bot.answer_callback_query(call.id)
            txs = api_get_wallet_transactions()
            text = f"📊 <pre>{json.dumps(txs, indent=2, ensure_ascii=False)[:3500]}</pre>" if txs else "❌"
            try:
                bot.edit_message_text(text, chat_id, msg_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")), parse_mode="HTML")
            except:
                bot.send_message(chat_id, text, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")), parse_mode="HTML")

        elif data == "search_product":
            bot.answer_callback_query(call.id)
            USER_WAITING_FOR_SEARCH[chat_id] = True
            try:
                bot.edit_message_text("🔍 أرسل اسم المنتج للبحث:", chat_id, msg_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 إلغاء", callback_data="main_menu")), parse_mode="HTML")
            except:
                bot.send_message(chat_id, "🔍 أرسل اسم المنتج للبحث:", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 إلغاء", callback_data="main_menu")), parse_mode="HTML")

        elif data == "payment_methods":
            bot.answer_callback_query(call.id)
            pay_info = f"💳 <b>شحن الرصيد / الدفع:</b>\n\n- Binance ID: <code>{BINANCE_ID}</code>"
            try:
                bot.edit_message_text(pay_info, chat_id, msg_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu")), parse_mode="HTML")
            except:
                bot.send_message(chat_id, pay_info, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu")), parse_mode="HTML")

        elif data.startswith("buy_"):
            prod_key = data.replace("buy_", "")
            if prod_key in products_info:
                info = products_info[prod_key]
                bot.answer_callback_query(call.id)
                
                if info['price'] == 0.0:
                    item_details = "TEST_CREDENTIALS_SUCCESS_MOCK_KEY_12345"
                    ords = load_orders()
                    ords.setdefault(str(chat_id), []).append({"product": info['name'], "item": item_details, "time": time.strftime("%Y-%m-%d %H:%M:%S")})
                    save_orders(ords)
                    success_txt = f"🎉 <b>تم التسليم بنجاح!</b>\n\n📦 <b>{info['name']}</b>\n🔑 <code>{item_details}</code>"
                    try:
                        bot.edit_message_text(success_txt, chat_id, msg_id, parse_mode="HTML", reply_markup=get_main_menu_markup(chat_id, is_admin))
                    except:
                        bot.send_message(chat_id, success_txt, parse_mode="HTML", reply_markup=get_main_menu_markup(chat_id, is_admin))
                    return

                USER_SELECTED_PRODUCT[chat_id] = prod_key
                markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🪙 إتمام الدفع الفوري", callback_data="pay_" + prod_key))
                markup.row(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
                msg_text = f"🏷️ <b>{info['name']}</b>\n💰 ${info['price']}\n📦 {info['stock']}\n\n{info['description']}"
                try:
                    bot.edit_message_text(msg_text, chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
                except:
                    bot.send_message(chat_id, msg_text, reply_markup=markup, parse_mode="HTML")
                
        elif data.startswith("pay_"):
            info = products_info.get(data.replace("pay_", ""), {"price": 1.0})
            bot.answer_callback_query(call.id)
            pay_msg = f"🪙 قم بتحويل (${info['price']} USDT) إلى Binance ID: <code>{BINANCE_ID}</code>\n\nثم أرسل رقم العملية (Order ID) هنا في الشات للاستلام الفوري!"
            try:
                bot.edit_message_text(pay_msg, chat_id, msg_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu")), parse_mode="HTML")
            except:
                bot.send_message(chat_id, pay_msg, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu")), parse_mode="HTML")
            
        elif data == "my_orders":
            bot.answer_callback_query(call.id)
            ords = load_orders().get(str(chat_id), [])
            text = "📜 لا توجد طلبات." if not ords else "📜 السجل:\n" + "".join([f"📦 {o['product']}\n🔑 <code>{o['item']}</code>\n" for o in ords])
            try:
                bot.edit_message_text(text, chat_id, msg_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu")), parse_mode="HTML")
            except:
                bot.send_message(chat_id, text, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu")), parse_mode="HTML")
            
        elif data == "main_menu":
            bot.answer_callback_query(call.id)
            USER_SELECTED_PRODUCT.pop(chat_id, None)
            USER_WAITING_FOR_SEARCH.pop(chat_id, None)
            try:
                bot.edit_message_text(LANG_TEXTS[get_user_lang(chat_id)]["welcome"], chat_id, msg_id, reply_markup=get_main_menu_markup(chat_id, is_admin), parse_mode="HTML")
            except:
                bot.send_message(chat_id, LANG_TEXTS[get_user_lang(chat_id)]["welcome"], reply_markup=get_main_menu_markup(chat_id, is_admin), parse_mode="HTML")

    @bot.message_handler(content_types=['text', 'photo'])
    def handle_incoming(message):
        chat_id = message.chat.id
        if message.text and message.text.startswith('/'): return

        if USER_WAITING_FOR_SEARCH.get(chat_id):
            USER_WAITING_FOR_SEARCH.pop(chat_id, None)
            query = message.text.strip().lower()
            products_info = fetch_supplier_products()
            markup = InlineKeyboardMarkup()
            found_count = 0
            for k, info in products_info.items():
                if query in info['name'].lower() or query in info['description'].lower():
                    found_count += 1
                    if info['stock'] > 0: markup.add(InlineKeyboardButton(f"✅ {info['name']} · ${info['price']}", callback_data="buy_" + k))
            markup.row(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
            bot.send_message(chat_id, f"🔍 نتائج البحث: <b>{message.text}</b>" if found_count > 0 else f"❌ لا يوجد نتائج لـ: <b>{message.text}</b>", reply_markup=markup, parse_mode="HTML")
            return

        if chat_id in USER_SELECTED_PRODUCT:
            order_reference = message.text.strip() if message.text else ""
            if not order_reference.isdigit() or len(order_reference) < 8:
                bot.send_message(chat_id, "❌ <b>رقم العملية غير صالح!</b>\nيجب أن يكون أرقام فقط ولا يقل عن 8 خانات.", parse_mode="HTML")
                return

            prod_key = USER_SELECTED_PRODUCT.get(chat_id)
            info = fetch_supplier_products().get(prod_key, {"name": "منتج", "price": 0.0})
            
            bot.send_message(chat_id, "⏳ جاري فحص حساب باينانس للتأكد من استلاستلام الدفع...")
            binance_check = verify_binance_transaction(order_reference, info.get("price", 0.0))
            
            if not binance_check["success"]:
                bot.send_message(chat_id, f"❌ <b>فشل التحقق:</b>\n{binance_check['error']}", parse_mode="HTML")
                return
            
            USER_SELECTED_PRODUCT.pop(chat_id)
            bot.send_message(chat_id, "✅ تم تأكيد استلام المبلغ! جاري استخراج المنتج...")

            api_result = purchase_order_from_supplier(prod_key, order_reference)
            if api_result["success"]:
                item_details = api_result["data"].get("item", api_result["data"].get("credentials", api_result["data"].get("data", "تم التسليم")))
                ords = load_orders()
                ords.setdefault(str(chat_id), []).append({"product": info['name'], "item": item_details, "time": time.strftime("%Y-%m-%d %H:%M:%S")})
                save_orders(ords)
                bot.send_message(chat_id, f"🎉 <b>تم تأكيد الدفع والتسليم بنجاح!</b>\n\n📦 <b>{info['name']}</b>\n🔑 <b>البيانات:</b>\n<code>{item_details}</code>", parse_mode="HTML", reply_markup=get_main_menu_markup(chat_id, chat_id == ADMIN_ID))
            else:
                bot.send_message(chat_id, f"❌ حدث خطأ من المزود:\n<code>{api_result.get('error', 'خطأ')}</code>", parse_mode="HTML")
            return
        
        bot.send_message(chat_id, "⚠️ يرجى اختيار المنتج أولاً من القائمة", reply_markup=get_main_menu_markup(chat_id, chat_id == ADMIN_ID))

app = Flask(__name__)
@app.route('/')
def health_check(): return "Pixora Store Active!", 200

def keep_alive():
    while True:
        time.sleep(300)
        try:
            url = os.environ.get("RENDER_EXTERNAL_URL")
            if url: requests.get(url)
        except: pass

if __name__ == '__main__':
    if bot:
        try: bot.remove_webhook()
        except: pass
    threading.Thread(target=keep_alive, daemon=True).start()
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), use_reloader=False), daemon=True).start()
    if bot:
        while True:
            try: bot.infinity_polling(skip_pending=True, timeout=60)
            except: time.sleep(5)
