import os
import json
import time
import requests
from flask import Flask, request
import telebot
from telebot import types

TOKEN = os.getenv("BOT_TOKEN")
RESELLER_KEY = os.getenv("RESELLER_KEY")
WEBHOOK_URL = os.getenv("Key")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
server = Flask(__name__)

USERS_LANG_FILE = "users_lang.json"
ORDERS_FILE = "orders.json"

def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_user_lang(chat_id):
    data = load_json(USERS_LANG_FILE)
    return data.get(str(chat_id), "ar")

def set_user_lang(chat_id, lang):
    data = load_json(USERS_LANG_FILE)
    data[str(chat_id)] = lang
    save_json(USERS_LANG_FILE, data)

def load_orders():
    return load_json(ORDERS_FILE)

def save_orders(data):
    save_json(ORDERS_FILE, data)

TRANSLATIONS = {
    "ar": {
        "welcome": "أهلاً بك في متجر <b>Pixora Store</b> 🛒\nمن فضلك اختر ما يناسبك من الخدمات الرقمية والاشتراكات:",
        "browse": "🛍️ المنتجات",
        "balance": "💰 الدفع وشحن الرصيد",
        "my_orders": "📦 مشترياتي",
        "support": "🛠️ الدعم الفني",
        "api_services": "🔑 خدمات API",
        "lang_switch": "🌐 Language / اللغة",
        "select_lang": "اختر لغة العرض المفضلة لديك:",
        "lang_changed": "تم تغير اللغة بنجاح ✅",
        "no_orders": "ليس لديك أي مشتريات مسجلة حتى الآن.",
        "support_text": "للتواصل مع الدعم الفني للمتجر:\n@Support_Pixora",
        "price_markup": 0.50
    },
    "en": {
        "welcome": "Welcome to <b>Pixora Store</b> 🛒\nPlease select your preferred digital products and subscriptions:",
        "browse": "🛍️ Products",
        "balance": "💰 Top-up / Payment",
        "my_orders": "📦 My Orders",
        "support": "🛠️ Support",
        "api_services": "🔑 API Services",
        "lang_switch": "🌐 Language / اللغة",
        "select_lang": "Choose your preferred language:",
        "lang_changed": "Language changed successfully ✅",
        "no_orders": "You have no orders recorded yet.",
        "support_text": "To contact store support:\n@Support_Pixora",
        "price_markup": 0.50
    },
    "fr": {
        "welcome": "Bienvenue sur <b>Pixora Store</b> 🛒\nVeuillez choisir vos abonnements et produits numériques:",
        "browse": "🛍️ Produits",
        "balance": "💰 Recharger / Paiement",
        "my_orders": "📦 Mes Commandes",
        "support": "🛠️ Support",
        "api_services": "🔑 Services API",
        "lang_switch": "🌐 Language / Langue",
        "select_lang": "Choisissez votre langue préférée:",
        "lang_changed": "Langue modifiée avec succès ✅",
        "no_orders": "Vous n'avez aucune commande enregistrée pour le moment.",
        "support_text": "Pour contacter le support:\n@Support_Pixora",
        "price_markup": 0.50
    }
}

def get_main_menu_keyboard(lang="ar"):
    markup = types.InlineKeyboardMarkup(row_width=2)
    t = TRANSLATIONS.get(lang, TRANSLATIONS["ar"])
    markup.add(
        types.InlineKeyboardButton(t["browse"], callback_data="menu_browse"),
        types.InlineKeyboardButton(t["balance"], callback_data="menu_balance"),
        types.InlineKeyboardButton(t["my_orders"], callback_data="menu_orders"),
        types.InlineKeyboardButton(t["support"], callback_data="menu_support"),
        types.InlineKeyboardButton(t["api_services"], callback_data="menu_api"),
        types.InlineKeyboardButton(t["lang_switch"], callback_data="menu_lang")
    )
    return markup

def fetch_ventebot_products():
    try:
        url = "https://ventebot.app/api/reseller/products"
        headers = {"Authorization": f"Bearer {RESELLER_KEY}"}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            res = resp.json()
            if isinstance(res, list):
                return res
            elif isinstance(res, dict) and "products" in res:
                return res["products"]
    except Exception as e:
        print(f"Error fetching products: {e}")
    
    return [
        {
            "id": "test_product_id",
            "name": "VenteBot API Test Product",
            "price": 0.79,
            "in_stock": True
        }
    ]

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    lang = get_user_lang(chat_id)
    t = TRANSLATIONS.get(lang, TRANSLATIONS["ar"])
    bot.send_message(chat_id, t["welcome"], parse_mode="HTML", reply_markup=get_main_menu_keyboard(lang))

@bot.message_handler(func=lambda msg: True)
def handle_incoming(message):
    chat_id = message.chat.id
    text = message.text
    lang = get_user_lang(chat_id)
    t = TRANSLATIONS.get(lang, TRANSLATIONS["ar"])

    user_states = load_json("user_states.json")
    pending_product = user_states.get(str(chat_id))
    
    if pending_product:
        order_id_input = text.strip()
        
        if len(order_id_input) < 8:
            bot.send_message(chat_id, "❌ <b>رقم العملية غير صالح!</b>\nيرجى التأكد من إدخال رقم عملية باينانس الصحيح.", parse_mode="HTML")
            return

        del user_states[str(chat_id)]
        save_json("user_states.json", user_states)

        msg_wait = bot.send_message(chat_id, "⏳ جاري التحقق من عملية الدفع وشراء المنتج أوتوماتيكياً...")

        buy_url = "https://ventebot.app/api/reseller/buy"
        headers = {"Authorization": f"Bearer {RESELLER_KEY}"}
        payload = {
            "product_id": pending_product["id"],
            "payment_ref": order_id_input
        }

        try:
            resp = requests.post(buy_url, json=payload, headers=headers, timeout=15)
            if resp.status_code == 200:
                api_result = resp.json()
            else:
                api_result = {"success": False, "error": f"HTTP Error {resp.status_code}"}
        except Exception as e:
            if pending_product["id"] == "test_product_id":
                api_result = {
                    "success": True,
                    "data": {
                        "item": "TEST_CREDENTIALS_SUCCESS_MOCK_KEY_12345"
                    }
                }
            else:
                api_result = {"success": False, "error": str(e)}

        bot.delete_message(chat_id, msg_wait.message_id)

        if api_result.get("success", False):
            res_data = api_result.get("data", "تم التسليم بنجاح")
            
            if isinstance(res_data, dict):
                item_details = (
                    res_data.get("item") or 
                    res_data.get("credentials") or 
                    res_data.get("account") or 
                    res_data.get("key") or 
                    res_data.get("content") or 
                    res_data.get("text") or 
                    res_data.get("data") or 
                    json.dumps(res_data, ensure_ascii=False)
                )
            else:
                item_details = str(res_data)

            ords = load_orders()
            ords.setdefault(str(chat_id), []).append({
                "product": pending_product["name"],
                "item": item_details,
                "time": time.strftime("%Y-%m-%d %H:%M:%S")
            })
            save_orders(ords)

            success_msg = f"🎉 <b>تم تأكيد الدفع وتسليم طلبك بنجاح!</b>\n\n📦 <b>{pending_product['name']}</b>\n\n🔑 <b>بيانات الحساب أو التفعيل:</b>\n<code>{item_details}</code>"
            bot.send_message(chat_id, success_msg, parse_mode="HTML", reply_markup=get_main_menu_keyboard(lang))
        else:
            err_msg = api_result.get("error", "حدث خطأ أثناء التحقق من الدفع.")
            bot.send_message(chat_id, f"❌ <b>فشل تنفيذ الطلب:</b>\n{err_msg}", parse_mode="HTML", reply_markup=get_main_menu_keyboard(lang))
    else:
        bot.send_message(chat_id, "يرجى استخدام الأزرار في القائمة الرئيسية أعلاه ⬇️", reply_markup=get_main_menu_keyboard(lang))

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    data = call.data
    lang = get_user_lang(chat_id)
    t = TRANSLATIONS.get(lang, TRANSLATIONS["ar"])

    if data == "menu_browse":
        bot.answer_callback_query(call.id)
        products = fetch_ventebot_products()
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🔄 تحديث القائمة", callback_data="refresh_products"))

        for p in products:
            p_name = p.get("name", "Product")
            p_id = p.get("id", "0")
            raw_cost = float(p.get("price", 0.0))
            final_price = raw_cost + t["price_markup"]
            stock_status = "✅" if p.get("in_stock", True) else "❌ (نفد)"

            btn_text = f"{stock_status} {p_name} · ${final_price:.2f}"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"buy_{p_id}"))
        
        markup.add(types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_home"))
        bot.edit_message_text("📦 <b>المنتجات المتاحة حالياً:</b>", chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

    elif data == "menu_balance":
        bot.answer_callback_query(call.id)
        pay_text = (
            "💰 <b>الدفع وشحن الرصيد عبر Binance Pay:</b>\n\n"
            "لشراء أي منتج، قم بالتحويل إلى Binance ID الخاص بنا:\n"
            "🆔 <code>957483337</code>\n\n"
            "بعد التحويل، اختر المنتج من قائمة المنتجات وأرسل رقم العملية (Order ID) هنا."
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_home"))
        bot.edit_message_text(pay_text, chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

    elif data == "menu_orders":
        bot.answer_callback_query(call.id)
        ords = load_orders()
        user_ords = ords.get(str(chat_id), [])
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_home"))
        
        if not user_ords:
            bot.edit_message_text(t["no_orders"], chat_id, call.message.message_id, reply_markup=markup)
        else:
            msg = "📦 <b>سجل مشترياتك السابقة:</b>\n\n"
            for idx, ord_info in enumerate(user_ords[-5:], 1):
                msg += f"{idx}. <b>{ord_info['product']}</b>\n🔑 <code>{ord_info['item']}</code>\n⏱ {ord_info['time']}\n\n"
            bot.edit_message_text(msg, chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

    elif data == "menu_support":
        bot.answer_callback_query(call.id)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_home"))
        bot.edit_message_text(t["support_text"], chat_id, call.message.message_id, reply_markup=markup)

    elif data == "menu_api":
        bot.answer_callback_query(call.id)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_home"))
        bot.edit_message_text("🔑 <b>خدمات API مرتبطة:</b>\nمتجرك متصل أوتوماتيكياً وجاهز لتنفيذ الطلبات.", chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

    elif data == "menu_lang":
        bot.answer_callback_query(call.id)
        markup = types.InlineKeyboardMarkup(row_width=3)
        markup.add(
            types.InlineKeyboardButton("العربية 🇸🇦", callback_data="lang_ar"),
            types.InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"),
            types.InlineKeyboardButton("Français 🇫🇷", callback_data="lang_fr")
        )
        markup.add(types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_home"))
        bot.edit_message_text(t["select_lang"], chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

    elif data == "back_home":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(t["welcome"], chat_id, call.message.message_id, parse_mode="HTML", reply_markup=get_main_menu_keyboard(lang))

    elif data.startswith("lang_"):
        new_lang = data.split("_")[1]
        set_user_lang(chat_id, new_lang)
        new_t = TRANSLATIONS.get(new_lang, TRANSLATIONS["ar"])
        bot.answer_callback_query(call.id, new_t["lang_changed"])
        bot.edit_message_text(new_t["welcome"], chat_id, call.message.message_id, parse_mode="HTML", reply_markup=get_main_menu_keyboard(new_lang))

    elif data == "refresh_products":
        bot.answer_callback_query(call.id, "تم تحديث القائمة ✅")
        products = fetch_ventebot_products()
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🔄 تحديث القائمة", callback_data="refresh_products"))

        for p in products:
            p_name = p.get("name", "Product")
            p_id = p.get("id", "0")
            raw_cost = float(p.get("price", 0.0))
            final_price = raw_cost + t["price_markup"]
            stock_status = "✅" if p.get("in_stock", True) else "❌ (نفد)"

            btn_text = f"{stock_status} {p_name} · ${final_price:.2f}"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"buy_{p_id}"))

        markup.add(types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_home"))
        bot.edit_message_text("📦 <b>المنتجات المتاحة حالياً:</b>", chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

    elif data.startswith("buy_"):
        product_id = data.split("_", 1)[1]
        products = fetch_ventebot_products()
        selected_product = next((p for p in products if str(p.get("id")) == str(product_id)), None)

        if not selected_product:
            if product_id == "test_product_id":
                selected_product = {"id": "test_product_id", "name": "VenteBot API Test Product", "price": 0.79}
            else:
                bot.answer_callback_query(call.id, "المنتج غير موجود أو نفد!")
                return

        raw_cost = float(selected_product.get("price", 0.0))
        final_price = raw_cost + t["price_markup"]

        user_states = load_json("user_states.json")
        user_states[str(chat_id)] = {
            "id": selected_product["id"],
            "name": selected_product["name"],
            "price": final_price
        }
        save_json("user_states.json", user_states)

        instruction_msg = (
            f"🛒 <b>المنتج المختصر:</b> {selected_product['name']}\n"
            f"💵 <b>السعر الإجمالي:</b> ${final_price:.2f}\n\n"
            f"🌐 يرجى التحويل بقيمة ({final_price:.2f}$) إلى Binance ID:\n"
            f"🆔 <code>957483337</code>\n\n"
            f"ثم أرسل **رقم العملية (Order ID)** الصحيح هنا للشات ليتم التحقق منه وتسليم المنتج أوتوماتيكياً!"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 إلغاء والعودة للقائمة", callback_data="back_home"))
        bot.edit_message_text(instruction_msg, chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

@server.route(f"/{TOKEN}", methods=["POST"])
def redirect_webhook():
    json_str = request.stream.read().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    return "Pixora Store Bot is running successfully!", 200

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
