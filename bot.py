import os
import json
import time
import requests
from flask import Flask, request
import telebot
from telebot import types

# قراءة المتغيرات من إعدادات Render
TOKEN = os.getenv("BOT_TOKEN")
RESELLER_KEY = os.getenv("RESELLER_KEY")
WEBHOOK_URL = os.getenv("Key")  # رابط السيرفر على Render إن وجد

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
server = Flask(__name__)

# ملفات تخزين بيانات المستخدمين واللغات والطلبات محلياً على السيرفر
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

# النصوص متعددة اللغات
TRANSLATIONS = {
    "ar": {
        "welcome": "أهلاً بك في متجر <b>Pixora Store</b> 🛒\nمن فضلك اختر ما يناسبك من الخدمات الرقمية والاشتراكات:",
        "browse": "🛍️ تصفف المنتجات",
        "balance": "💰 شحن الرصيد / الدفع",
        "my_orders": "📦 مشترياتي",
        "support": "🛠️ الدعم الفني",
        "api_services": "🔑 خدمات API",
        "lang_switch": "🌐 Language / اللغة",
        "select_lang": "اختر لغة العرض المفضلة لديك:",
        "lang_changed": "تم تغير اللغة بنجاح ✅",
        "no_orders": "ليس لديك أي مشتريات مسجلة حتى الآن.",
        "support_text": "للتواصل مع الدعم الفني للمتجر:\n@Support_Pixora",
        "price_markup": 0.50  # مكسبك المضاف فوق سعر التكلفة
    },
    "en": {
        "welcome": "Welcome to <b>Pixora Store</b> 🛒\nPlease select your preferred digital products and subscriptions:",
        "browse": "🛍️ Browse Products",
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
        "browse": "🛍️ Parcourir",
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

def get_permanent_reply_keyboard(lang="ar"):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    t = TRANSLATIONS.get(lang, TRANSLATIONS["ar"])
    markup.add(
        types.KeyboardButton(t["browse"]),
        types.KeyboardButton(t["api_services"]),
        types.KeyboardButton(t["balance"]),
        types.KeyboardButton(t["lang_switch"]),
        types.KeyboardButton(t["my_orders"]),
        types.KeyboardButton(t["support"])
    )
    return markup

# جلب المنتجات من VenteBot API
def fetch_ventebot_products():
    try:
        url = "https://ventebot.app/api/reseller/products" # رابط المزود الافتراضي أو المعدل
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
    
    # منتج تجريبي افتراضي في حال تعذر الاتصال مؤقتاً
    return [
        {
            "id": "test_product_id",
            "name": "VenteBot API Test Product",
            "price": 0.0,
            "in_stock": True
        }
    ]

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    lang = get_user_lang(chat_id)
    t = TRANSLATIONS.get(lang, TRANSLATIONS["ar"])
    bot.send_message(chat_id, t["welcome"], parse_mode="HTML", reply_markup=get_permanent_reply_keyboard(lang))

@bot.message_handler(func=lambda msg: True)
def handle_incoming(message):
    chat_id = message.chat.id
    text = message.text
    lang = get_user_lang(chat_id)
    t = TRANSLATIONS.get(lang, TRANSLATIONS["ar"])

    if text in [TRANSLATIONS["ar"]["browse"], TRANSLATIONS["en"]["browse"], TRANSLATIONS["fr"]["browse"]]:
        products = fetch_ventebot_products()
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🔄 تحديث القائمة / Refresh", callback_data="refresh_products"))

        for p in products:
            p_name = p.get("name", "Product")
            p_id = p.get("id", "0")
            raw_cost = float(p.get("price", 0.0))
            final_price = raw_cost + t["price_markup"]
            stock_status = "✅" if p.get("in_stock", True) else "❌ (نفد)"

            btn_text = f"{stock_status} {p_name} · ${final_price:.2f}"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"buy_{p_id}"))

        bot.send_message(chat_id, "📦 <b>المنتجات المتاحة حالياً:</b>", parse_mode="HTML", reply_markup=markup)

    elif text in [TRANSLATIONS["ar"]["balance"], TRANSLATIONS["en"]["balance"], TRANSLATIONS["fr"]["balance"]]:
        pay_text = (
            "💰 <b>شحـن الرصيد والدفع:</b>\n\n"
            "لشراء أي منتج، قم بالتحويل إلى Binance Pay ID الخاص بنا:\n"
            "🆔 <code>957483337</code>\n\n"
            "بعد إتمام التحويل، تواصل مع الدعم أو اختر المنتج واضغط شراء لإرسال رقم العملية (Order ID)."
        )
        bot.send_message(chat_id, pay_text, parse_mode="HTML", reply_markup=get_permanent_reply_keyboard(lang))

    elif text in [TRANSLATIONS["ar"]["my_orders"], TRANSLATIONS["en"]["my_orders"], TRANSLATIONS["fr"]["my_orders"]]:
        ords = load_orders()
        user_ords = ords.get(str(chat_id), [])
        if not user_ords:
            bot.send_message(chat_id, t["no_orders"], reply_markup=get_permanent_reply_keyboard(lang))
        else:
            msg = "📦 <b>سجل مشترياتك السابقة:</b>\n\n"
            for idx, ord_info in enumerate(user_ords[-5:], 1):
                msg += f"{idx}. <b>{ord_info['product']}</b>\n🔑 <code>{ord_info['item']}</code>\n⏱ {ord_info['time']}\n\n"
            bot.send_message(chat_id, msg, parse_mode="HTML", reply_markup=get_permanent_reply_keyboard(lang))

    elif text in [TRANSLATIONS["ar"]["support"], TRANSLATIONS["en"]["support"], TRANSLATIONS["fr"]["support"]]:
        bot.send_message(chat_id, t["support_text"], reply_markup=get_permanent_reply_keyboard(lang))

    elif text in [TRANSLATIONS["ar"]["lang_switch"], TRANSLATIONS["en"]["lang_switch"], TRANSLATIONS["fr"]["lang_switch"]]:
        markup = types.InlineKeyboardMarkup(row_width=3)
        markup.add(
            types.InlineKeyboardButton("العربية 🇸🇦", callback_data="lang_ar"),
            types.InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"),
            types.InlineKeyboardButton("Français 🇫🇷", callback_data="lang_fr")
        )
        bot.send_message(chat_id, t["select_lang"], reply_markup=markup)

    elif text in [TRANSLATIONS["ar"]["api_services"], TRANSLATIONS["en"]["api_services"], TRANSLATIONS["fr"]["api_services"]]:
        bot.send_message(chat_id, "🔑 <b>خدمات API مرتبطة:</b>\nمتجرك متصل أوتوماتيكياً بمزود الخدمات الرقمية وجاهز لتنفيذ الطلبات الفورية.", parse_mode="HTML", reply_markup=get_permanent_reply_keyboard(lang))

    else:
        # التحقق مما إذا كان المستخدم يرسل رقم عملية (Order ID) لشراء معلق
        user_states = load_json("user_states.json")
        pending_product = user_states.get(str(chat_id))
        
        if pending_product:
            # مسح الحالة المؤقتة
            del user_states[str(chat_id)]
            save_json("user_states.json", user_states)

            order_id_input = text.strip()
            msg_wait = bot.send_message(chat_id, "⏳ جاري التحقق من عملية الدفع وشراء المنتج من المزود أوتوماتيكياً...")

            # طلب الشراء من VenteBot API
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
                # في حالة كان منتج تجريبي محلياً للاختبار
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
                
                # استخراج تفاصيل الحساب أو الرابط بدقة من الاستجابة
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
                bot.send_message(chat_id, success_msg, parse_mode="HTML", reply_markup=get_permanent_reply_keyboard(lang))
            else:
                err_msg = api_result.get("error", "حدث خطأ غير معروف أثناء تنفيذ الطلب لدى المزود.")
                bot.send_message(chat_id, f"❌ <b>فشل تنفيذ الطلب:</b>\n{err_msg}", parse_mode="HTML", reply_markup=get_permanent_reply_keyboard(lang))
        else:
            bot.send_message(chat_id, "يرجى استخدام الأزرار في الأسفل لتصفح المتجر والخدمات ⬇️", reply_markup=get_permanent_reply_keyboard(lang))

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    data = call.data
    lang = get_user_lang(chat_id)
    t = TRANSLATIONS.get(lang, TRANSLATIONS["ar"])

    if data.startswith("lang_"):
        new_lang = data.split("_")[1]
        set_user_lang(chat_id, new_lang)
        new_t = TRANSLATIONS.get(new_lang, TRANSLATIONS["ar"])
        bot.answer_callback_query(call.id, new_t["lang_changed"])
        bot.send_message(chat_id, new_t["welcome"], parse_mode="HTML", reply_markup=get_permanent_reply_keyboard(new_lang))

    elif data == "refresh_products":
        bot.answer_callback_query(call.id, "تم تحديث القائمة ✅")
        # إعادة إرسال قائمة المنتجات
        products = fetch_ventebot_products()
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🔄 تحديث القائمة / Refresh", callback_data="refresh_products"))

        for p in products:
            p_name = p.get("name", "Product")
            p_id = p.get("id", "0")
            raw_cost = float(p.get("price", 0.0))
            final_price = raw_cost + t["price_markup"]
            stock_status = "✅" if p.get("in_stock", True) else "❌ (نفد)"

            btn_text = f"{stock_status} {p_name} · ${final_price:.2f}"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"buy_{p_id}"))

        bot.edit_message_text("📦 <b>المنتجات المتاحة حالياً:</b>", chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

    elif data.startswith("buy_"):
        product_id = data.split("_", 1)[1]
        products = fetch_ventebot_products()
        selected_product = next((p for p in products if str(p.get("id")) == str(product_id)), None)

        if not selected_product:
            # إذا كان منتج الاختبار
            if product_id == "test_product_id":
                selected_product = {"id": "test_product_id", "name": "VenteBot API Test Product", "price": 0.0}
            else:
                bot.answer_callback_query(call.id, "المنتج غير موجود أو نفد!")
                return

        raw_cost = float(selected_product.get("price", 0.0))
        final_price = raw_cost + t["price_markup"]

        # تخزين حالة المستخدم أنه ينتظر إدخال رقم العملية لهذا المنتج
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
            f"🌐 تحويل ({final_price:.2f}$) إلى Binance ID:\n"
            f"<code>957483337</code>\n\n"
            f"ثم أرسل رقم العملية (Order ID) هنا للشات ليتم الشراء والتسليم أوتوماتيكياً فوراً!"
        )
        bot.send_message(chat_id, instruction_msg, parse_mode="HTML")

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
