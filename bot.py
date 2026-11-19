import os
import time
import json
import threading
import html
import re
import requests
import hmac
import hashlib
from urllib.parse import urlencode

import telebot
from telebot.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove, BotCommand
)
from flask import Flask

# =========================================================
# إعدادات البيئة - أضف القيم في Environment على Render
# =========================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.environ.get("ADMIN_ID", "1004439571"))
BINANCE_ID = os.environ.get("BINANCE_ID", "957483337").strip()
SUPPORT_WHATSAPP = os.environ.get(
    "SUPPORT_WHATSAPP", "https://wa.me/213555668244"
).strip()

RESELLER_KEY = os.environ.get("RESELLER_KEY", "").strip()
VENTEBOT_API_URL = os.environ.get(
    "VENTEBOT_API_URL",
    "https://web-production-1c7b1.up.railway.app/api/reseller"
).strip().rstrip("/")

BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY", "").strip()
BINANCE_SECRET_KEY = os.environ.get("BINANCE_SECRET_KEY", "").strip()

ORDERS_FILE = os.environ.get("ORDERS_FILE", "orders.json")
bot = telebot.TeleBot(BOT_TOKEN, threaded=False) if BOT_TOKEN else None

USER_SELECTED_PRODUCT = {}
USER_WAITING_FOR_SEARCH = {}
USER_LANGUAGES = {}
USER_PROCESSING = set()

# ===== Cache للمنتجات عشان البوت ميبقاش بطيء =====
_PRODUCTS_CACHE = {"data": {}, "time": 0}
CACHE_TTL = 60  # ثانية

LANG_TEXTS = {
    "ar": {
        "welcome": "🔥 أهلاً بك في متجر Pixora Store الرقمي!\n\nاختر القسم أو المنتج المطلوب:",
        "search": "🔍 بحث عن منتج", "orders": "📜 مشترياتي",
        "deposit": "💳 شحن الرصيد / الدفع", "support": "🛠 الدعم الفني",
        "api": "🔑 خدمات API", "lang": "🌐 اللغة / Language",
        "admin": "🛠 لوحة تحكم الإدارة", "no_products": "⚠ لا توجد منتجات متاحة حالياً...",
        "sold_out": "نفد"
    },
    "en": {
        "welcome": "🔥 Welcome to Pixora Store Digital!\n\nChoose a category or product:",
        "search": "🔍 Search Product", "orders": "📜 My Orders",
        "deposit": "💳 Top up / Payment", "support": "🛠 Support",
        "api": "🔑 API Services", "lang": "🌐 Language",
        "admin": "🛠 Admin Panel", "no_products": "⚠ No products available right now...",
        "sold_out": "Sold out"
    },
    "fr": {
        "welcome": "🔥 Bienvenue sur Pixora Store Numérique !\n\nChoisissez une catégorie ou un produit :",
        "search": "🔍 Rechercher", "orders": "📜 Mes Commandes",
        "deposit": "💳 Recharger / Paiement", "support": "🛠 Support",
        "api": "🔑 Services API", "lang": "🌐 Langue",
        "admin": "🛠 Panneau Admin", "no_products": "⚠ Aucun produit disponible...",
        "sold_out": "Épuisé"
    }
}

BANNED_KEYWORDS = [
    "spotify", "anghami", "netflix", "shahid", "disney", "apple music",
    "iptv", "movie", "film", "music", "osn", "watchit", "prime video",
    "اغاني", "موسيقى", "أفلام", "مسلسلات", "سينما"
]

FAMILY_NAMES = {
    "chatgpt": "🤖 عائلة اشتراكات ChatGPT",
    "claude": "🧠 عائلة اشتراكات Claude AI",
    "google": "✨ عائلة Google & Gmail",
    "capcut": "🎬 عائلة أدوات CapCut",
    "canva": "🎨 عائلة تصاميم Canva",
    "zoom": "📹 عائلة اشتراكات Zoom",
    "elevenlabs": "🎙 عائلة أدوات ElevenLabs",
    "gamma": "📊 عائلة عروض Gamma AI",
    "lovable": "💻 عائلة منصة Lovable",
    "microsoft": "🪟 عائلة منتجات Microsoft",
    "miro": "📌 عائلة لوحات Miro",
    "notion": "📝 عائلة أدوات Notion",
    "quizlet": "📚 عائلة تعليم Quizlet",
    "railway": "⚙ عائلة استضافة Railway",
    "wordwall": "🎮 عائلة أنشطة Wordwall",
    "api_services": "🔑 خدمات وباقات API",
    "vpn": "🔒 خدمات وشبكات VPN",
    "tests": "🧪 منتجات التجربة"
}

def user_lang(chat_id):
    return USER_LANGUAGES.get(chat_id, "ar")

def safe_html(value):
    return html.escape(str(value), quote=False)

def is_allowed_product(name, description=""):
    text = f"{name} {description}".lower()
    return not any(word in text for word in BANNED_KEYWORDS)

def get_product_family(name):
    n = str(name).lower()
    rules = [
        (("test", "api test"), "tests"),
        (("chatgpt", "gpt", "openai"), "chatgpt"),
        (("claude",), "claude"),
        (("gemini", "google", "gmail"), "google"),
        (("capcut",), "capcut"), (("canva",), "canva"),
        (("zoom",), "zoom"), (("elevenlabs",), "elevenlabs"),
        (("gamma",), "gamma"), (("lovable",), "lovable"),
        (("microsoft",), "microsoft"), (("miro",), "miro"),
        (("notion",), "notion"), (("quizlet",), "quizlet"),
        (("railway",), "railway"), (("wordwall",), "wordwall"),
        (("api",), "api_services"),
        (("vpn", "hma", "surfshark", "expressvpn"), "vpn")
    ]
    for words, family in rules:
        if any(word in n for word in words):
            return family
    return None

def load_orders():
    if not os.path.exists(ORDERS_FILE):
        return {}
    try:
        with open(ORDERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception as exc:
        print("ORDERS FILE READ ERROR:", str(exc))
        return {}

def save_orders(data):
    temp = ORDERS_FILE + ".tmp"
    try:
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(temp, ORDERS_FILE)
    except Exception as exc:
        print("ORDERS FILE SAVE ERROR:", str(exc))

def supplier_headers():
    return {"X-Reseller-Key": RESELLER_KEY}

def extract_image_url(item):
    """FIX 1: جرب كل أسماء الصور المحتملة من المورد"""
    # 1. حقول مباشرة
    for key in ["image_url", "image", "photo", "thumbnail", "cover", "img", "picture", "poster", "banner"]:
        v = item.get(key)
        if isinstance(v, str) and v.strip().startswith("http"):
            return v.strip()
        if isinstance(v, dict):
            # لو الصورة جاية dict زي {url: ...}
            for sub in ["url", "src", "link", "href"]:
                if isinstance(v.get(sub), str) and v.get(sub, "").startswith("http"):
                    return v[sub].strip()
    # 2. لو فيه list images
    for key in ["images", "photos", "gallery"]:
        v = item.get(key)
        if isinstance(v, list) and v:
            first = v[0]
            if isinstance(first, str) and first.startswith("http"):
                return first.strip()
            if isinstance(first, dict):
                for sub in ["url", "src"]:
                    if isinstance(first.get(sub), str) and first.get(sub, "").startswith("http"):
                        return first[sub].strip()
    # 3. دور في أي حقل فيه http وينتهي بصورة
    for v in item.values():
        if isinstance(v, str) and v.startswith("http") and any(v.lower().split("?")[0].endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]):
            return v.strip()
    return ""

def fetch_supplier_products(force_refresh=False):
    # استخدم الكاش عشان البوت ميبقاش بطيء
    now = time.time()
    if not force_refresh and _PRODUCTS_CACHE["data"] and (now - _PRODUCTS_CACHE["time"] < CACHE_TTL):
        return _PRODUCTS_CACHE["data"]
    if not RESELLER_KEY:
        print("CONFIG ERROR: RESELLER_KEY is empty")
        return _PRODUCTS_CACHE["data"] or {}
    try:
        response = requests.get(
            f"{VENTEBOT_API_URL}/products",
            headers=supplier_headers(), timeout=20
        )
        if response.status_code != 200:
            print("SUPPLIER PRODUCTS ERROR:", response.status_code, response.text[:1000])
            return _PRODUCTS_CACHE["data"] or {}
        payload = response.json()
        if isinstance(payload, list):
            items = payload
        elif isinstance(payload, dict):
            items = payload.get("products") or payload.get("data") or payload.get("items") or []
            if isinstance(items, dict):
                items = items.get("products") or items.get("items") or []
        else:
            items = []
        result = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            name = item.get("name") or item.get("title") or "منتج رقمي"
            desc = item.get("description") or item.get("desc") or ""
            if not is_allowed_product(name, desc):
                continue
            product_id = str(item.get("id") or item.get("code") or "").strip()
            if not product_id:
                continue
            try:
                cost = float(item.get("price_usd") or item.get("price") or item.get("cost") or 0)
                price = round(cost + 0.50, 2)
            except (TypeError, ValueError):
                price = 0.0
            result[product_id] = {
                "id": product_id,
                "name": str(name).strip(),
                "price": price,
                "stock": int(item.get("stock") or item.get("quantity") or 0),
                "description": str(desc or "اشتراك رقمي."),
                "image": extract_image_url(item),
                "family": get_product_family(name)
            }
        _PRODUCTS_CACHE["data"] = result
        _PRODUCTS_CACHE["time"] = now
        return result
    except Exception as exc:
        print("FETCH SUPPLIER PRODUCTS EXCEPTION:", repr(exc))
        return _PRODUCTS_CACHE["data"] or {}

def api_get(path):
    if not RESELLER_KEY:
        return None
    try:
        res = requests.get(
            f"{VENTEBOT_API_URL}{path}",
            headers=supplier_headers(), timeout=15
        )
        return res.json() if res.status_code == 200 else None
    except Exception as exc:
        print("SUPPLIER GET ERROR:", path, repr(exc))
        return None

def api_get_my_wallet():
    return api_get("/me")

def api_get_wallet_transactions():
    return api_get("/wallet/transactions")

def api_get_deposit_methods():
    return api_get("/wallet/deposit-methods")

def log_response_structure(value, depth=0):
    if depth > 6:
        return "..."
    if isinstance(value, dict):
        return {str(k): log_response_structure(v, depth + 1) for k, v in value.items()}
    if isinstance(value, list):
        return [log_response_structure(value[0], depth + 1)] if value else []
    return type(value).__name__

# =========================================================
# FIX 2: استخراج بيانات التسليم - نسخة مرنة تفهم أي شكل للمورد
# =========================================================
DELIVERY_KEYS = [
    "account_data", "credentials", "credential", "delivery",
    "login", "account", "key", "code", "license", "serial",
    "username", "email", "password", "content", "details",
    "product_data", "delivery_data", "info", "data",
    "account_info", "access", "activation", "pin", "token"
]
# مفاتيح نتجاهلها عشان منبعتش بيانات فاضية أو بيانات الطلب نفسه
IGNORE_KEYS = {"id", "product_id", "order_id", "status", "price", "quantity", "created_at", "updated_at", "idempotency_key", "request_status", "user_id", "reseller_id"}

def _format_value(v):
    if isinstance(v, dict):
        parts = []
        for kk, vv in v.items():
            if str(kk).lower() in IGNORE_KEYS:
                continue
            if vv is None or vv == "":
                continue
            parts.append(f"{kk}: {vv}")
        return "\n".join(parts) if parts else None
    if isinstance(v, list):
        parts = [_format_value(x) for x in v]
        parts = [p for p in parts if p]
        return "\n".join(parts) if parts else None
    if isinstance(v, str):
        v = v.strip()
        return v if len(v) >= 2 else None
    if isinstance(v, (int, float)):
        return str(v)
    return None

def _find_credentials(obj, depth=0):
    if depth > 5:
        return None
    if isinstance(obj, dict):
        # 1. دور على مفاتيح التسليم المباشرة
        for k in DELIVERY_KEYS:
            if k in obj and obj[k] not in (None, "", {}, []):
                formatted = _format_value(obj[k])
                # تأكد انها مش مجرد كلمة "completed" أو رقم الطلب
                if formatted and len(formatted) >= 3 and formatted.lower() not in ("completed", "success", "paid"):
                    return formatted
        # 2. لو مفيش، دور بعمق في كل القيم ماعدا اللي بنتجاهلها
        for k, v in obj.items():
            if str(k).lower() in IGNORE_KEYS:
                continue
            # تجاهل حقول الوصف والسعر
            if str(k).lower() in ("name", "title", "description", "desc"):
                continue
            r = _find_credentials(v, depth + 1)
            if r:
                return r
        return None
    if isinstance(obj, list):
        for v in obj:
            r = _find_credentials(v, depth + 1)
            if r:
                return r
        return None
    return None

def extract_delivery_data(response_data):
    """تستخرج بيانات التسليم من أي شكل يرجعه VenteBot"""
    if not isinstance(response_data, dict):
        return None
    order = response_data.get("order")
    if not isinstance(order, dict):
        order = response_data
    # لا ترفض الطلب لو الحالة مختلفة، حاول تستخرج البيانات على أي حال
    # لكن لو الحالة pending وواضح ان مفيش items، ارجع None
    items = order.get("items") or order.get("data") or []
    if isinstance(items, dict):
        items = [items]
    credentials = []
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            # حاول تلاقي بيانات في الـ item نفسه
            found = _find_credentials(item)
            if found and found not in credentials:
                credentials.append(found)
    # لو ملقيتش في items، دور في الـ order كله
    if not credentials:
        found = _find_credentials(order)
        if found:
            credentials.append(found)
    # لو لسه ملقيتش، دور في response كله
    if not credentials:
        found = _find_credentials(response_data)
        if found:
            credentials.append(found)
    if not credentials:
        return None
    if len(credentials) == 1:
        return credentials[0]
    return "\n\n".join(f"بيانات المنتج {i}:\n{v}" for i, v in enumerate(credentials, start=1))

def supplier_order_status(order_id):
    response = requests.get(
        f"{VENTEBOT_API_URL}/orders/{order_id}",
        headers=supplier_headers(),
        timeout=20
    )
    try:
        data = response.json()
    except Exception:
        data = {}
    return response.status_code, data

def lookup_supplier_order(idempotency_key):
    response = requests.get(
        f"{VENTEBOT_API_URL}/orders/lookup",
        headers=supplier_headers(),
        params={"idempotency_key": idempotency_key, "limit": 20, "offset": 0},
        timeout=20
    )
    try:
        data = response.json()
    except Exception:
        data = {}
    return response.status_code, data

def purchase_order_from_supplier(product_id, payment_reference):
    if not RESELLER_KEY:
        return {"success": False, "error": "RESELLER_KEY غير مضبوط."}
    product_value = int(product_id) if str(product_id).isdigit() else product_id
    idempotency_key = f"pixora_{payment_reference}_{product_id}"[:120]
    headers = {
        "X-Reseller-Key": RESELLER_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "product_id": product_value,
        "quantity": 1,
        "idempotency_key": idempotency_key
    }
    data = {}
    order = None
    order_id = None
    try:
        response = requests.post(
            f"{VENTEBOT_API_URL}/orders",
            json=payload,
            headers=headers,
            timeout=30
        )
        print("SUPPLIER CREATE STATUS:", response.status_code)
        try:
            data = response.json()
        except Exception:
            data = {}
        print("SUPPLIER CREATE STRUCTURE:", json.dumps(log_response_structure(data), ensure_ascii=False))
        # اطبع أول 2000 حرف من الرد الحقيقي للتشخيص (بدون كلمات سر لو كانت واضحة)
        try:
            print("SUPPLIER CREATE RAW PREVIEW:", str(data)[:2000])
        except Exception:
            pass
        if isinstance(data, dict):
            order = data.get("order")
            if isinstance(order, dict):
                order_id = order.get("id")
            elif isinstance(data.get("data"), dict):
                order = data.get("data")
                order_id = order.get("id")
    except requests.RequestException as exc:
        print("SUPPLIER CREATE REQUEST EXCEPTION:", repr(exc))

    if not isinstance(order, dict) or not order_id:
        try:
            lookup_status, lookup_data = lookup_supplier_order(idempotency_key)
            print("SUPPLIER LOOKUP STATUS:", lookup_status)
            print("SUPPLIER LOOKUP STRUCTURE:", json.dumps(log_response_structure(lookup_data), ensure_ascii=False))
            results = lookup_data.get("results", []) if isinstance(lookup_data, dict) else []
            for result in results if isinstance(results, list) else []:
                if not isinstance(result, dict):
                    continue
                if result.get("idempotency_key") != idempotency_key:
                    continue
                request_status = str(result.get("request_status", "")).lower()
                candidate = result.get("order")
                if isinstance(candidate, dict):
                    order = candidate
                    order_id = candidate.get("id")
                if request_status == "failed_no_charge":
                    return {"success": False, "error": "المورد أكد أن الطلب فشل دون خصم رصيد (failed_no_charge).", "idempotency_key": idempotency_key}
                break
        except requests.RequestException as exc:
            print("SUPPLIER LOOKUP EXCEPTION:", repr(exc))

    status = str(order.get("status", "")).upper() if isinstance(order, dict) else ""
    # Poll فقط لو الطلب موجود ولسه مش مكتمل
    if status not in ("COMPLETED", "DELIVERED", "SUCCESS", "DONE", "FULFILLED", "PAID", "READY") and order_id:
        for attempt in range(10):
            time.sleep(5)
            try:
                poll_http_status, poll_data = supplier_order_status(order_id)
                print("SUPPLIER ORDER POLL HTTP:", poll_http_status)
                candidate = None
                if isinstance(poll_data, dict):
                    candidate = poll_data.get("order") or poll_data.get("data")
                if isinstance(candidate, dict):
                    order = candidate
                    status = str(order.get("status", "")).upper()
                print("SUPPLIER ORDER STATE:", status or "UNKNOWN")
                if status in ("COMPLETED", "DELIVERED", "SUCCESS", "DONE", "FULFILLED", "PAID", "READY"):
                    break
                # لو لقينا بيانات تسليم حتى لو الحالة لسه pending، اعتبره جاهز
                if extract_delivery_data({"order": order}):
                    break
            except requests.RequestException as exc:
                print("SUPPLIER ORDER POLL EXCEPTION:", repr(exc))
    # FIX: لو الطلب مكتمل بس البيانات مش في رد الـ create، اعمل جلب أخير للطلب كامل
    if order_id and not extract_delivery_data({"order": order}):
        try:
            _, final_data = supplier_order_status(order_id)
            final_order = None
            if isinstance(final_data, dict):
                final_order = final_data.get("order") or final_data.get("data")
            if isinstance(final_order, dict):
                # ادمج البيانات الجديدة
                merged = dict(order)
                merged.update(final_order)
                # لو items موجودة في الجديد خدها
                if final_order.get("items"):
                    merged["items"] = final_order["items"]
                order = merged
                status = str(order.get("status", "")).upper()
                print("SUPPLIER FINAL FETCH DONE, STATUS:", status)
        except Exception as exc:
            print("SUPPLIER FINAL FETCH EXCEPTION:", repr(exc))

    # اعتبر الطلب ناجح لو الحالة مكتملة أو لو لقينا بيانات تسليم
    delivery_preview = extract_delivery_data({"order": order}) if isinstance(order, dict) else None
    if (status in ("COMPLETED", "DELIVERED", "SUCCESS", "DONE", "FULFILLED", "PAID", "READY") or delivery_preview) and isinstance(order, dict):
        return {"success": True, "data": {"success": True, "order": order}, "idempotency_key": idempotency_key, "order_id": order.get("id")}
    return {
        "success": False,
        "error": (f"المورد لم يؤكد حالة COMPLETED. لم تتم إعادة الشراء لتجنب الخصم المكرر. الحالة الحالية: {status or 'غير معروفة'}."),
        "idempotency_key": idempotency_key,
        "order_id": order_id
    }

def verify_binance_transaction(order_id, expected_amount):
    if not BINANCE_API_KEY or not BINANCE_SECRET_KEY:
        return {"success": False, "error": "مفاتيح Binance API غير مضبوطة على Render."}
    try:
        timestamp = int(time.time() * 1000)
        query_string = urlencode({"timestamp": timestamp, "limit": 50})
        signature = hmac.new(BINANCE_SECRET_KEY.encode(), query_string.encode(), hashlib.sha256).hexdigest()
        url = f"https://api.binance.com/sapi/v1/pay/transactions?{query_string}&signature={signature}"
        response = requests.get(url, headers={"X-MBX-APIKEY": BINANCE_API_KEY}, timeout=15)
        if response.status_code != 200:
            return {"success": False, "error": f"Binance HTTP {response.status_code}: {response.text[:500]}"}
        transactions = response.json().get("data", [])
        for tx in transactions:
            if (str(tx.get("orderId")) == str(order_id) or str(tx.get("transactionId")) == str(order_id)):
                actual = float(tx.get("amount", 0))
                if actual >= float(expected_amount):
                    return {"success": True}
                return {"success": False, "error": f"المبلغ المستلم ${actual} أقل من السعر ${expected_amount}."}
        return {"success": False, "error": "رقم العملية غير موجود ضمن آخر المعاملات."}
    except Exception as exc:
        return {"success": False, "error": str(exc)}

def notify_admin(text):
    if not bot:
        return
    try:
        bot.send_message(ADMIN_ID, text, parse_mode="HTML")
    except Exception as exc:
        print("ADMIN NOTIFICATION ERROR:", repr(exc))

def get_main_menu_markup(chat_id, is_admin=False):
    t = LANG_TEXTS.get(user_lang(chat_id), LANG_TEXTS["ar"])
    markup = InlineKeyboardMarkup()
    products = fetch_supplier_products()
    if not products:
        markup.add(InlineKeyboardButton(t["no_products"], callback_data="main_menu"))
        return markup
    families, singles = set(), []
    for key, info in products.items():
        if info["family"]:
            families.add(info["family"])
        else:
            singles.append((key, info))
    for fam in sorted(families, key=lambda x: FAMILY_NAMES.get(x, x)):
        markup.add(InlineKeyboardButton(FAMILY_NAMES.get(fam, f"📁 قسم {fam.upper()}"), callback_data="fam_" + fam))
    for key, info in sorted(singles, key=lambda x: x[1]["name"].lower()):
        label = (f"✅ {info['name']} · ${info['price']}" if info["stock"] > 0 else f"❌ {info['name']} ({t['sold_out']})")
        markup.add(InlineKeyboardButton(label, callback_data=("buy_" if info["stock"] > 0 else "sold_out_") + key))
    markup.row(InlineKeyboardButton(t["search"], callback_data="search_product"), InlineKeyboardButton(t["orders"], callback_data="my_orders"))
    markup.row(InlineKeyboardButton(t["deposit"], callback_data="payment_methods"), InlineKeyboardButton(t["support"], url=SUPPORT_WHATSAPP))
    markup.row(InlineKeyboardButton(t["api"], callback_data="show_apis"), InlineKeyboardButton(t["lang"], callback_data="menu_lang"))
    if is_admin:
        markup.row(InlineKeyboardButton(t["admin"], callback_data="admin_panel"))
    return markup

def get_admin_markup():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("💰 فحص الرصيد", callback_data="adm_balance"), InlineKeyboardButton("💳 طرق الإيداع", callback_data="adm_deposits"))
    markup.row(InlineKeyboardButton("📊 سجل المعاملات", callback_data="adm_transactions"), InlineKeyboardButton("🔙 الرئيسية", callback_data="main_menu"))
    return markup

def send_home(chat_id):
    bot.send_message(chat_id, LANG_TEXTS[user_lang(chat_id)]["welcome"], reply_markup=get_main_menu_markup(chat_id, chat_id == ADMIN_ID))

def send_product_card(chat_id, info, markup, reply_to_msg_id=None):
    """FIX 1: ابعت صورة المنتج لو موجودة، ولو فشلت ابعت نص"""
    msg = (f"🏷 <b>{safe_html(info['name'])}</b>\n"
           f"💰 السعر: <b>${info['price']}</b> | التوفر: <b>{info['stock']}</b>\n\n"
           f"📝 <b>تفاصيل المنتج:</b>\n{safe_html(info['description'])}")
    image = info.get("image", "")
    if image and image.startswith("http"):
        try:
            bot.send_photo(chat_id, image, caption=msg, reply_markup=markup, parse_mode="HTML")
            return True
        except Exception as exc:
            print("IMAGE SEND ERROR:", repr(exc), "URL:", image[:200])
    bot.send_message(chat_id, msg, reply_markup=markup, parse_mode="HTML")
    return False

if bot:
    try:
        bot.set_my_commands([
            BotCommand("start", "تشغيل المتجر 🚀"),
            BotCommand("products", "تصفح المنتجات 🛍"),
            BotCommand("my_orders", "مشترياتي 📜"),
            BotCommand("language", "اللغة / Language 🌐")
        ])
    except Exception as exc:
        print("BOT COMMANDS ERROR:", repr(exc))

    @bot.message_handler(commands=["start", "products"])
    def send_welcome(message):
        chat_id = message.chat.id
        USER_WAITING_FOR_SEARCH.pop(chat_id, None)
        USER_SELECTED_PRODUCT.pop(chat_id, None)
        try:
            msg = bot.send_message(chat_id, "🔄", reply_markup=ReplyKeyboardRemove())
            bot.delete_message(chat_id, msg.message_id)
        except Exception:
            pass
        send_home(chat_id)

    @bot.message_handler(commands=["my_orders"])
    def cmd_my_orders(message):
        chat_id = message.chat.id
        orders = load_orders().get(str(chat_id), [])
        if not orders:
            body = "📜 لا توجد طلبات سابقة."
        else:
            rows = []
            for order in orders[-30:]:
                rows.append(f"📦 <b>{safe_html(order.get('product', 'منتج'))}</b>\n🔑 <code>{safe_html(order.get('item', ''))}</code>\n🕒 {safe_html(order.get('time', ''))}\n──────────────")
            body = "📜 سجل مشترياتي السابقة:\n\n" + "\n".join(rows)
        bot.send_message(chat_id, body, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu")), parse_mode="HTML")

    @bot.message_handler(commands=["language"])
    def cmd_language(message):
        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr")
        )
        bot.send_message(message.chat.id, "🌐 اختر اللغة:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: True)
    def handle_query(call):
        chat_id = call.message.chat.id
        msg_id = call.message.message_id
        data = call.data or ""
        is_admin = chat_id == ADMIN_ID
        products = fetch_supplier_products()
        if data.startswith("lang_"):
            lang = data.replace("lang_", "")
            if lang not in LANG_TEXTS:
                lang = "ar"
            USER_LANGUAGES[chat_id] = lang
            bot.answer_callback_query(call.id, "✅")
            try:
                bot.edit_message_text(LANG_TEXTS[lang]["welcome"], chat_id, msg_id, reply_markup=get_main_menu_markup(chat_id, is_admin))
            except Exception:
                send_home(chat_id)
        elif data.startswith("fam_"):
            fam = data[4:]
            bot.answer_callback_query(call.id)
            markup = InlineKeyboardMarkup()
            found = [(k, v) for k, v in products.items() if v["family"] == fam]
            for key, info in sorted(found, key=lambda x: x[1]["name"].lower()):
                if info["stock"] > 0:
                    markup.add(InlineKeyboardButton(f"✅ {info['name']} · ${info['price']}", callback_data="buy_" + key))
                else:
                    markup.add(InlineKeyboardButton(f"❌ {info['name']} (نفد)", callback_data="sold_out_" + key))
            markup.add(InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="main_menu"))
            try:
                bot.delete_message(chat_id, msg_id)
            except Exception:
                pass
            bot.send_message(chat_id, "📁 <b>خيارات القسم:</b>", reply_markup=markup, parse_mode="HTML")
        elif data == "menu_lang":
            bot.answer_callback_query(call.id)
            markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"),
                InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
                InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr"),
                InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu")
            )
            bot.edit_message_text("🌐 اختر اللغة:", chat_id, msg_id, reply_markup=markup)
        elif data == "show_apis":
            bot.answer_callback_query(call.id)
            markup = InlineKeyboardMarkup()
            for key, info in products.items():
                if "api" in info["name"].lower() and info["stock"] > 0:
                    markup.add(InlineKeyboardButton(f"✅ {info['name']} · ${info['price']}", callback_data="buy_" + key))
            markup.add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
            bot.edit_message_text("🔑 <b>خدمات API المتاحة:</b>", chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
        elif data == "admin_panel" and is_admin:
            bot.answer_callback_query(call.id)
            bot.edit_message_text("🛠 <b>لوحة تحكم الإدارة:</b>", chat_id, msg_id, reply_markup=get_admin_markup(), parse_mode="HTML")
        elif data in ("adm_balance", "adm_deposits", "adm_transactions") and is_admin:
            bot.answer_callback_query(call.id)
            if data == "adm_balance":
                result = api_get_my_wallet()
                title = "💰 الرصيد"
            elif data == "adm_deposits":
                result = api_get_deposit_methods()
                title = "💳 طرق الإيداع"
            else:
                result = api_get_wallet_transactions()
                title = "📊 سجل المعاملات"
            body = safe_html(json.dumps(result, ensure_ascii=False, indent=2)[:3000]) if result else "تعذر جلب البيانات."
            bot.send_message(chat_id, f"{title}\n<pre>{body}</pre>", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")), parse_mode="HTML")
        elif data == "search_product":
            bot.answer_callback_query(call.id)
            USER_WAITING_FOR_SEARCH[chat_id] = True
            bot.edit_message_text("🔍 أرسل اسم المنتج للبحث:", chat_id, msg_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 إلغاء", callback_data="main_menu")))
        elif data == "payment_methods":
            bot.answer_callback_query(call.id)
            pay_info = f"💳 <b>شحن الرصيد / الدفع:</b>\n\n- Binance ID: <code>{safe_html(BINANCE_ID)}</code>"
            bot.edit_message_text(pay_info, chat_id, msg_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu")), parse_mode="HTML")
        elif data.startswith("sold_out_"):
            bot.answer_callback_query(call.id, "❌ المنتج نفد من المخزون.", show_alert=True)
        elif data.startswith("buy_"):
            key = data[4:]
            info = products.get(key)
            bot.answer_callback_query(call.id)
            if not info:
                bot.send_message(chat_id, "تعذر العثور على المنتج. حدّث القائمة وحاول مجدداً.")
                return
            if info["stock"] <= 0:
                bot.send_message(chat_id, "❌ المنتج نفد من المخزون.")
                return
            if info["price"] <= 0:
                bot.send_message(chat_id, "⚠ هذا المنتج مجاني/تجريبي ولم يتم تفعيل تسليمه. تواصل مع الإدارة.")
                notify_admin(f"⚠ محاولة شراء منتج سعره صفر: {safe_html(info['name'])} (ID: {safe_html(key)})")
                return
            USER_SELECTED_PRODUCT[chat_id] = key
            markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🪙 إتمام الدفع الفوري", callback_data="pay_" + key))
            markup.row(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
            try:
                bot.delete_message(chat_id, msg_id)
            except Exception:
                pass
            # FIX 1: ابعت كارت المنتج بالصورة
            send_product_card(chat_id, info, markup)
        elif data.startswith("pay_"):
            key = data[4:]
            info = products.get(key)
            bot.answer_callback_query(call.id)
            if not info or info["price"] <= 0:
                bot.send_message(chat_id, "تعذر تحديد المنتج. ارجع للقائمة وحاول مجدداً.")
                return
            USER_SELECTED_PRODUCT[chat_id] = key
            pay_msg = (f"🪙 قم بتحويل (${info['price']} USDT) إلى Binance ID: <code>{safe_html(BINANCE_ID)}</code>\n\nثم أرسل رقم العملية (Order ID) هنا في المحادثة.")
            bot.edit_message_text(pay_msg, chat_id, msg_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu")), parse_mode="HTML")
        elif data == "my_orders":
            bot.answer_callback_query(call.id)
            orders = load_orders().get(str(chat_id), [])
            if not orders:
                body = "📜 لا توجد طلبات."
            else:
                body = "📜 سجل مشترياتي:\n" + "\n".join(f"📦 {safe_html(o.get('product', 'منتج'))}\n🔑 <code>{safe_html(o.get('item', ''))}</code>" for o in orders[-30:])
            bot.edit_message_text(body, chat_id, msg_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu")), parse_mode="HTML")
        elif data == "main_menu":
            bot.answer_callback_query(call.id)
            USER_SELECTED_PRODUCT.pop(chat_id, None)
            USER_WAITING_FOR_SEARCH.pop(chat_id, None)
            try:
                bot.delete_message(chat_id, msg_id)
            except Exception:
                pass
            send_home(chat_id)

    @bot.message_handler(content_types=["text", "photo"])
    def handle_incoming(message):
        chat_id = message.chat.id
        if message.text and message.text.startswith("/"):
            return
        if USER_WAITING_FOR_SEARCH.get(chat_id):
            USER_WAITING_FOR_SEARCH.pop(chat_id, None)
            query = (message.text or "").strip().lower()
            if not query:
                bot.send_message(chat_id, "أرسل كلمة للبحث.")
                return
            products = fetch_supplier_products()
            markup = InlineKeyboardMarkup()
            found = 0
            for key, info in products.items():
                if query in info["name"].lower() or query in info["description"].lower():
                    found += 1
                    if info["stock"] > 0:
                        markup.add(InlineKeyboardButton(f"✅ {info['name']} · ${info['price']}", callback_data="buy_" + key))
            markup.row(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
            bot.send_message(chat_id, f"🔍 نتائج البحث: <b>{safe_html(message.text)}</b>" if found else f"❌ لا توجد نتائج لـ: <b>{safe_html(message.text)}</b>", reply_markup=markup, parse_mode="HTML")
            return
        if chat_id not in USER_SELECTED_PRODUCT:
            bot.send_message(chat_id, "⚠ يرجى اختيار المنتج أولاً من القائمة.", reply_markup=get_main_menu_markup(chat_id, chat_id == ADMIN_ID))
            return
        if chat_id in USER_PROCESSING:
            bot.send_message(chat_id, "⏳ طلبك قيد المعالجة، انتظر قليلاً.")
            return
        reference = (message.text or "").strip()
        # FIX: اقبل حروف وأرقام لأن Order ID بتاع Binance مش أرقام بس
        if not re.match(r"^[A-Za-z0-9_-]{8,}$", reference):
            bot.send_message(chat_id, "❌ رقم العملية غير صالح. يجب أن يكون 8 خانات على الأقل (حروف وأرقام).")
            return
        USER_PROCESSING.add(chat_id)
        try:
            product_key = USER_SELECTED_PRODUCT.get(chat_id)
            products = fetch_supplier_products()
            info = products.get(product_key)
            if not info:
                bot.send_message(chat_id, "تعذر العثور على المنتج. تواصل مع الدعم قبل إعادة الدفع.")
                return
            bot.send_message(chat_id, "⏳ جاري فحص عملية الدفع عبر Binance...")
            payment = verify_binance_transaction(reference, info["price"])
            if not payment["success"]:
                bot.send_message(chat_id, f"❌ <b>فشل التحقق:</b>\n{safe_html(payment['error'])}", parse_mode="HTML")
                return
            bot.send_message(chat_id, "✅ تم تأكيد الدفع. جارٍ إرسال الطلب إلى المورد...")
            result = purchase_order_from_supplier(product_key, reference)
            if not result["success"]:
                notify_admin(f"🚨 <b>دفع مؤكد لكن طلب المورد فشل</b>\nالزبون: <code>{chat_id}</code>\nالمنتج: {safe_html(info['name'])}\nمرجع الدفع: <code>{safe_html(reference)}</code>\nالخطأ: <code>{safe_html(result.get('error', 'غير معروف')[:700])}</code>")
                bot.send_message(chat_id, "✅ تم تأكيد الدفع، لكن المورد لم يؤكد إتمام الطلب. تم إشعار الإدارة، لا ترسل دفعة ثانية.")
                USER_SELECTED_PRODUCT.pop(chat_id, None)
                return
            delivery = extract_delivery_data(result["data"])
            if not delivery:
                notify_admin(f"⚠ <b>الدفع وطلب المورد تم قبولهما، لكن لم أستطع استخراج بيانات التسليم.</b>\nالزبون: <code>{chat_id}</code>\nالمنتج: {safe_html(info['name'])}\nمرجع الدفع: <code>{safe_html(reference)}</code>\nOrder ID المورد: <code>{result.get('order_id')}</code>\nراجع سجل Render وابحث عن SUPPLIER CREATE RAW PREVIEW.")
                bot.send_message(chat_id, "✅ تم تأكيد الدفع وإرسال الطلب للمورد، لكن بيانات المنتج لم تصلنا بصيغة مفهومة. تم إشعار الإدارة لمتابعة التسليم. لا تدفع مرة أخرى.")
                orders = load_orders()
                orders.setdefault(str(chat_id), []).append({"product": info["name"], "item": "قيد المتابعة مع المورد - لم تصل بيانات التسليم بعد", "reference": reference, "status": "pending_delivery", "time": time.strftime("%Y-%m-%d %H:%M:%S")})
                save_orders(orders)
                USER_SELECTED_PRODUCT.pop(chat_id, None)
                return
            orders = load_orders()
            orders.setdefault(str(chat_id), []).append({"product": info["name"], "item": delivery, "reference": reference, "status": "delivered", "time": time.strftime("%Y-%m-%d %H:%M:%S")})
            save_orders(orders)
            delivery_message = (f"🎉 <b>تم تأكيد الدفع والتسليم بنجاح!</b>\n\n📦 <b>{safe_html(info['name'])}</b>\n🔑 <b>بيانات المنتج:</b>\n<pre>{safe_html(delivery[:3500])}</pre>\n\nاحتفظ بهذه الرسالة للرجوع إليها.")
            bot.send_message(chat_id, delivery_message, parse_mode="HTML", reply_markup=get_main_menu_markup(chat_id, chat_id == ADMIN_ID))
            USER_SELECTED_PRODUCT.pop(chat_id, None)
        except Exception as exc:
            print("PAYMENT/DELIVERY HANDLER ERROR:", repr(exc))
            notify_admin(f"🚨 خطأ غير متوقع أثناء معالجة طلب:\nالزبون: <code>{chat_id}</code>\n<code>{safe_html(str(exc)[:700])}</code>")
            bot.send_message(chat_id, "حدث خطأ أثناء معالجة الطلب. تم إشعار الإدارة. لا تعاود الدفع قبل التواصل مع الدعم.")
        finally:
            USER_PROCESSING.discard(chat_id)

app = Flask(__name__)

@app.route("/")
def health_check():
    return "Pixora Store Active!", 200

@app.route("/health")
def health():
    return {"status": "ok"}, 200

def keep_alive():
    while True:
        time.sleep(300)
        url = os.environ.get("RENDER_EXTERNAL_URL", "").strip()
        if url:
            try:
                requests.get(url, timeout=10)
            except Exception:
                pass

if __name__ == "__main__":
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN غير موجود في Environment Variables على Render.")
    if bot:
        try:
            bot.remove_webhook()
        except Exception as exc:
            print("REMOVE WEBHOOK ERROR:", repr(exc))
    threading.Thread(target=keep_alive, daemon=True).start()
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "10000")), use_reloader=False), daemon=True).start()
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
        except Exception as exc:
            print("BOT POLLING ERROR:", repr(exc))
            time.sleep(5)
