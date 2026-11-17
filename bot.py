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

# Supabase: server-side secret key only; never expose it to Telegram clients or GitHub.
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_SECRET_KEY = os.environ.get("SUPABASE_SECRET_KEY", "").strip()

ORDERS_FILE = os.environ.get("ORDERS_FILE", "orders.json")
bot = telebot.TeleBot(BOT_TOKEN, threaded=False) if BOT_TOKEN else None

USER_SELECTED_PRODUCT = {}
USER_WAITING_FOR_SEARCH = {}
USER_LANGUAGES = {}
USER_PROCESSING = set()
PAYMENT_REGISTRY_LOCK = threading.Lock()

LANG_TEXTS = {
    "ar": {
        "welcome": "🔥 أهلاً بك في متجر Pixora Store الرقمي!\n\nاختر القسم أو المنتج المطلوب:",
        "search": "🔍 بحث عن منتج", "orders": "📜 مشترياتي",
        "deposit": "💳 شحن الرصيد / الدفع", "support": "🛠️ الدعم الفني",
        "api": "🔑 خدمات API", "lang": "🌐 اللغة / Language",
        "admin": "🛠️ لوحة تحكم الإدارة", "no_products": "⚠️ لا توجد منتجات متاحة حالياً...",
        "sold_out": "نفد"
    },
    "en": {
        "welcome": "🔥 Welcome to Pixora Store Digital!\n\nChoose a category or product:",
        "search": "🔍 Search Product", "orders": "📜 My Orders",
        "deposit": "💳 Top up / Payment", "support": "🛠️ Support",
        "api": "🔑 API Services", "lang": "🌐 Language",
        "admin": "🛠️ Admin Panel", "no_products": "⚠️ No products available right now...",
        "sold_out": "Sold out"
    },
    "fr": {
        "welcome": "🔥 Bienvenue sur Pixora Store Numérique !\n\nChoisissez une catégorie ou un produit :",
        "search": "🔍 Rechercher", "orders": "📜 Mes Commandes",
        "deposit": "💳 Recharger / Paiement", "support": "🛠️ Support",
        "api": "🔑 Services API", "lang": "🌐 Langue",
        "admin": "🛠️ Panneau Admin", "no_products": "⚠️ Aucun produit disponible...",
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

def fetch_supplier_products():
    if not RESELLER_KEY:
        print("CONFIG ERROR: RESELLER_KEY is empty")
        return {}
    try:
        response = requests.get(
            f"{VENTEBOT_API_URL}/products",
            headers=supplier_headers(), timeout=20
        )
        if response.status_code != 200:
            print("SUPPLIER PRODUCTS ERROR:", response.status_code, response.text[:1000])
            return {}
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
                cost = float(item.get("price_usd") or 0)
                price = round(cost + 0.50, 2)
            except (TypeError, ValueError):
                price = 0.0
            result[product_id] = {
                "id": product_id,
                "name": str(name).strip(),
                "price": price,
                "stock": int(item.get("stock") or 0),
                "description": str(desc or "اشتراك رقمي."),
                "image": item.get("image_url") or "",
                "family": get_product_family(name)
            }
        return result
    except Exception as exc:
        print("FETCH SUPPLIER PRODUCTS EXCEPTION:", repr(exc))
        return {}

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
    """يسجل أسماء الحقول وأنواعها فقط، ولا يسجل كلمات مرور أو مفاتيح تسليم."""
    if depth > 6:
        return "..."
    if isinstance(value, dict):
        return {str(k): log_response_structure(v, depth + 1) for k, v in value.items()}
    if isinstance(value, list):
        return [log_response_structure(value[0], depth + 1)] if value else []
    return type(value).__name__

def _delivery_value_to_text(value):
    """Convert supplier delivery payload to readable text without losing URLs."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, indent=2)
    return str(value).strip()


def extract_delivery_data(response_data):
    """Extract delivery credentials from a completed VenteBot order.

    Supports the documented items[].account_data shape and common alternate
    delivery field names. Does not treat arbitrary order metadata as credentials.
    """
    if not isinstance(response_data, dict):
        return None

    candidates = []
    root_order = response_data.get("order")
    if isinstance(root_order, dict):
        candidates.append(root_order)
    if "items" in response_data or "status" in response_data:
        candidates.append(response_data)

    # Some API responses wrap the order in data/result.
    for wrapper_key in ("data", "result", "response"):
        wrapped = response_data.get(wrapper_key)
        if isinstance(wrapped, dict):
            nested = wrapped.get("order")
            if isinstance(nested, dict):
                candidates.append(nested)
            if "items" in wrapped or "status" in wrapped:
                candidates.append(wrapped)

    seen = set()
    for order in candidates:
        marker = id(order)
        if marker in seen:
            continue
        seen.add(marker)
        if str(order.get("status", "")).upper() not in ("COMPLETED", "COMPLETE", "SUCCESS", "DELIVERED"):
            continue

        items = order.get("items")
        if not isinstance(items, list):
            # A few supplier responses return delivery data directly on order.
            items = [order]

        credentials = []
        for item in items:
            if not isinstance(item, dict):
                continue
            value = None
            for field in (
                "account_data", "delivery_data", "delivery", "credentials",
                "activation_data", "activation_link", "account", "serial",
                "license_key", "code"
            ):
                candidate = item.get(field)
                if candidate not in (None, "", [], {}):
                    value = candidate
                    break
            text_value = _delivery_value_to_text(value)
            if text_value and text_value not in credentials:
                credentials.append(text_value)

        if credentials:
            if len(credentials) == 1:
                return credentials[0]
            return "\n\n".join(
                f"بيانات المنتج {i}:\n{value}"
                for i, value in enumerate(credentials, start=1)
            )
    return None


def supplier_order_status(order_id):
    """Read an existing order; this endpoint does not create or charge a new order."""
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
    """Recover the existing request using its exact idempotency key."""
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
    """
    VenteBot documented create payload: product_id, quantity, idempotency_key.
    If the response is lost/uncertain, lookup the same key. Never POST twice.
    Only order.status == COMPLETED is treated as delivery-ready.
    """
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
        print(
            "SUPPLIER CREATE STRUCTURE:",
            json.dumps(log_response_structure(data), ensure_ascii=False)
        )
        if isinstance(data, dict):
            order = data.get("order")
            if isinstance(order, dict):
                order_id = order.get("id")
    except requests.RequestException as exc:
        # The supplier may have accepted the request before a timeout.
        # Do not repeat POST; recover the same idempotency key below.
        print("SUPPLIER CREATE REQUEST EXCEPTION:", repr(exc))

    # If create response is absent/incomplete, recover by idempotency key.
    if not isinstance(order, dict) or not order_id:
        try:
            lookup_status, lookup_data = lookup_supplier_order(idempotency_key)
            print("SUPPLIER LOOKUP STATUS:", lookup_status)
            print(
                "SUPPLIER LOOKUP STRUCTURE:",
                json.dumps(log_response_structure(lookup_data), ensure_ascii=False)
            )
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
                    return {
                        "success": False,
                        "error": "المورد أكد أن الطلب فشل دون خصم رصيد (failed_no_charge).",
                        "idempotency_key": idempotency_key
                    }
                break
        except requests.RequestException as exc:
            print("SUPPLIER LOOKUP EXCEPTION:", repr(exc))

    status = str(order.get("status", "")).upper() if isinstance(order, dict) else ""

    # Poll only the read endpoint while the order is pending.
    if status != "COMPLETED" and order_id:
        for attempt in range(8):
            time.sleep(7)
            try:
                poll_http_status, poll_data = supplier_order_status(order_id)
                print("SUPPLIER ORDER POLL HTTP:", poll_http_status)
                candidate = poll_data.get("order") if isinstance(poll_data, dict) else None
                if isinstance(candidate, dict):
                    order = candidate
                    status = str(order.get("status", "")).upper()
                print("SUPPLIER ORDER STATE:", status or "UNKNOWN")
                if status == "COMPLETED":
                    break
            except requests.RequestException as exc:
                print("SUPPLIER ORDER POLL EXCEPTION:", repr(exc))

    if status == "COMPLETED" and isinstance(order, dict):
        # IMPORTANT: POST /orders may return only a summary. Always read the
        # completed order once more to retrieve its actual delivery payload.
        # This is GET-only: it cannot create another purchase or charge wallet.
        final_order_data = {"success": True, "order": order}
        resolved_order_id = order_id or order.get("id")
        if resolved_order_id:
            try:
                detail_http, detail_data = supplier_order_status(resolved_order_id)
                print("SUPPLIER ORDER DETAILS HTTP:", detail_http)
                print(
                    "SUPPLIER ORDER DETAILS STRUCTURE:",
                    json.dumps(log_response_structure(detail_data), ensure_ascii=False)
                )
                if detail_http == 200 and isinstance(detail_data, dict):
                    detail_order = detail_data.get("order")
                    if isinstance(detail_order, dict):
                        final_order_data = {"success": True, "order": detail_order}
                    elif isinstance(detail_data.get("data"), dict):
                        nested = detail_data["data"]
                        nested_order = nested.get("order") if isinstance(nested, dict) else None
                        final_order_data = {"success": True, "order": nested_order} if isinstance(nested_order, dict) else detail_data
                    elif isinstance(detail_data, dict):
                        final_order_data = detail_data
            except requests.RequestException as exc:
                print("SUPPLIER ORDER DETAILS EXCEPTION:", repr(exc))

        # Report only shape/field types; never print account_data or activation URLs.
        print(
            "SUPPLIER DELIVERY STRUCTURE:",
            json.dumps(log_response_structure(final_order_data), ensure_ascii=False)
        )
        return {
            "success": True,
            "data": final_order_data,
            "idempotency_key": idempotency_key,
            "order_id": resolved_order_id
        }

    return {
        "success": False,
        "error": (
            "المورد لم يؤكد حالة COMPLETED. لم تتم إعادة الشراء لتجنب الخصم المكرر. "
            f"الحالة الحالية: {status or 'غير معروفة'}."
        ),
        "idempotency_key": idempotency_key,
        "order_id": order_id
    }


def verify_binance_transaction(transaction_id, expected_amount):
    """
    Verify an incoming Binance Pay transaction.
    Requires exact transactionId, positive amount, USDT, and receiver Binance ID.
    Binance Pay history supports a maximum 90-day interval and limit 100.
    """
    if not BINANCE_API_KEY or not BINANCE_SECRET_KEY:
        return {"success": False, "error": "مفاتيح Binance API غير مضبوطة على Render."}
    if not BINANCE_ID:
        return {"success": False, "error": "BINANCE_ID غير مضبوط."}

    try:
        from decimal import Decimal, InvalidOperation

        now_ms = int(time.time() * 1000)
        params = {
            "startTime": now_ms - (90 * 24 * 60 * 60 * 1000),
            "endTime": now_ms,
            "limit": 100,
            "recvWindow": 5000,
            "timestamp": now_ms,
        }
        query_string = urlencode(params)
        signature = hmac.new(
            BINANCE_SECRET_KEY.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        response = requests.get(
            "https://api.binance.com/sapi/v1/pay/transactions",
            params=f"{query_string}&signature={signature}",
            headers={"X-MBX-APIKEY": BINANCE_API_KEY},
            timeout=20
        )

        if response.status_code != 200:
            detail = response.text[:400]
            if response.status_code == 451:
                return {
                    "success": False,
                    "error": "Binance HTTP 451: الوصول محجوب من Binance لهذا الخادم/الحساب. لا يمكن تجاوز ذلك بتعديل الكود."
                }
            return {
                "success": False,
                "error": f"Binance HTTP {response.status_code}: {detail}"
            }

        payload = response.json()
        if not isinstance(payload, dict) or payload.get("success") is False:
            return {
                "success": False,
                "error": f"رد Binance غير ناجح أو غير متوقع: {str(payload)[:300]}"
            }

        transactions = payload.get("data", [])
        if not isinstance(transactions, list):
            return {"success": False, "error": "صيغة سجل معاملات Binance غير متوقعة."}

        expected_id = str(transaction_id).strip()
        for tx in transactions:
            if not isinstance(tx, dict):
                continue
            if str(tx.get("transactionId", "")).strip() != expected_id:
                continue

            try:
                actual = Decimal(str(tx.get("amount", "0")))
                expected = Decimal(str(expected_amount))
            except (InvalidOperation, TypeError, ValueError):
                return {"success": False, "error": "تعذر قراءة مبلغ المعاملة أو مبلغ الطلب."}

            currency = str(tx.get("currency", "")).upper()
            receiver = tx.get("receiverInfo") or {}
            receiver_id = str(receiver.get("binanceId", "")).strip()

            if actual <= 0:
                return {"success": False, "error": "المعاملة ليست مبلغاً وارداً موجباً."}
            if currency != "USDT":
                return {
                    "success": False,
                    "error": f"عملة المعاملة هي {currency or 'غير معروفة'} وليست USDT."
                }
            if receiver_id != str(BINANCE_ID).strip():
                return {
                    "success": False,
                    "error": "المعاملة موجودة، لكن Binance ID المستلم لا يطابق حساب المتجر."
                }
            if actual < expected:
                return {
                    "success": False,
                    "error": f"المبلغ المستلم {actual} USDT أقل من السعر المطلوب {expected} USDT."
                }

            return {
                "success": True,
                "transaction_id": expected_id,
                "amount": str(actual),
                "currency": currency,
                "receiver_binance_id": receiver_id
            }

        return {
            "success": False,
            "error": "رقم المعاملة غير موجود ضمن سجل Binance Pay المتاح (آخر 90 يوماً)."
        }

    except requests.RequestException as exc:
        return {"success": False, "error": f"تعذر الاتصال بـ Binance: {str(exc)[:300]}"}
    except Exception as exc:
        return {"success": False, "error": f"خطأ أثناء التحقق: {str(exc)[:300]}"}


def payment_reference_already_used(reference):
    """Return True if this Binance transaction ID was ever reserved or used."""
    reference = str(reference).strip()
    if not reference:
        return True
    orders = load_orders()
    registry = orders.get("__payment_registry__", {})
    if isinstance(registry, dict) and reference in registry:
        return True
    # Backward compatibility: also inspect historical order records.
    for user_id, user_orders in orders.items():
        if user_id == "__payment_registry__" or not isinstance(user_orders, list):
            continue
        for order in user_orders:
            if isinstance(order, dict) and str(order.get("reference", "")).strip() == reference:
                return True
    return False


def supabase_is_configured():
    return bool(SUPABASE_URL and SUPABASE_SECRET_KEY)


def supabase_headers(prefer=None):
    # Supabase's new sb_secret_* keys are opaque API keys, not JWTs.
    # Send them in apikey only (not Authorization: Bearer).
    headers = {
        "apikey": SUPABASE_SECRET_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def supabase_transaction_exists(reference):
    """Check Supabase for an already-used Binance transaction ID.

    On connection/configuration errors, fail closed: never approve a payment
    when the permanent duplicate-check store cannot be reached.
    """
    if not supabase_is_configured():
        print("SUPABASE CONFIG ERROR: SUPABASE_URL / SUPABASE_SECRET_KEY missing")
        return True
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/payment_transactions",
            headers=supabase_headers(),
            params={"select": "transaction_id", "transaction_id": f"eq.{reference}", "limit": "1"},
            timeout=15
        )
        if response.status_code != 200:
            print("SUPABASE CHECK ERROR:", response.status_code, response.text[:300])
            return True
        rows = response.json()
        return isinstance(rows, list) and len(rows) > 0
    except Exception as exc:
        print("SUPABASE CHECK EXCEPTION:", repr(exc))
        return True


def supabase_reserve_transaction(reference, chat_id, product_name, amount, currency="USDT"):
    """Atomically reserve transaction_id using the database UNIQUE constraint."""
    if not supabase_is_configured():
        print("SUPABASE CONFIG ERROR: cannot reserve transaction without Supabase")
        return False
    payload = {
        "transaction_id": str(reference),
        "telegram_user_id": int(chat_id),
        "product_name": str(product_name),
        "amount": str(amount),
        "currency": str(currency),
        "status": "PENDING"
    }
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/payment_transactions",
            headers=supabase_headers("return=representation"),
            json=payload,
            timeout=15
        )
        if response.status_code in (200, 201):
            return True
        if response.status_code == 409:
            print("SUPABASE DUPLICATE TRANSACTION:", reference)
            return False
        # PostgREST can report unique violations with a 4xx response.
        try:
            error_data = response.json()
        except Exception:
            error_data = {}
        error_text = str(error_data).lower()
        if "duplicate key" in error_text or "unique" in error_text or "23505" in error_text:
            return False
        print("SUPABASE RESERVE ERROR:", response.status_code, response.text[:500])
        return False
    except Exception as exc:
        print("SUPABASE RESERVE EXCEPTION:", repr(exc))
        return False


def supabase_update_transaction_status(reference, status):
    """Update transaction lifecycle without ever deleting or releasing its ID."""
    if not supabase_is_configured():
        return False
    try:
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/payment_transactions",
            headers=supabase_headers("return=minimal"),
            params={"transaction_id": f"eq.{reference}"},
            json={"status": str(status), "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
            timeout=15
        )
        if response.status_code not in (200, 204):
            print("SUPABASE STATUS UPDATE ERROR:", response.status_code, response.text[:300])
            return False
        return True
    except Exception as exc:
        print("SUPABASE STATUS UPDATE EXCEPTION:", repr(exc))
        return False


def payment_reference_already_used(reference):
    """Return True if the transaction exists in permanent or legacy local history."""
    reference = str(reference).strip()
    if not reference:
        return True
    orders = load_orders()
    registry = orders.get("__payment_registry__", {})
    if isinstance(registry, dict) and reference in registry:
        return True
    for user_id, user_orders in orders.items():
        if user_id == "__payment_registry__" or not isinstance(user_orders, list):
            continue
        for order in user_orders:
            if isinstance(order, dict) and str(order.get("reference", "")).strip() == reference:
                return True
    return supabase_transaction_exists(reference)


def reserve_payment_reference(reference, chat_id, product_name, amount, currency="USDT"):
    """Permanently reserve a verified payment in Supabase before supplier purchase.

    Supabase's UNIQUE(transaction_id) constraint is the authoritative atomic lock.
    The ID is never released, even if supplier purchase or delivery later fails.
    """
    reference = str(reference).strip()
    if not reference:
        return False
    with PAYMENT_REGISTRY_LOCK:
        orders = load_orders()
        registry = orders.setdefault("__payment_registry__", {})
        if not isinstance(registry, dict):
            registry = {}
            orders["__payment_registry__"] = registry
        if reference in registry:
            return False
        for user_id, user_orders in orders.items():
            if user_id == "__payment_registry__" or not isinstance(user_orders, list):
                continue
            for old_order in user_orders:
                if isinstance(old_order, dict) and str(old_order.get("reference", "")).strip() == reference:
                    return False

        # Insert first: the database UNIQUE constraint prevents races across bot restarts/instances.
        if not supabase_reserve_transaction(reference, chat_id, product_name, amount, currency):
            return False

        registry[reference] = {
            "chat_id": str(chat_id),
            "product": str(product_name),
            "amount": str(amount),
            "currency": str(currency),
            "status": "PENDING",
            "reserved_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        save_orders(orders)
        return True


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
        markup.add(InlineKeyboardButton(
            FAMILY_NAMES.get(fam, f"📁 قسم {fam.upper()}"),
            callback_data="fam_" + fam
        ))
    for key, info in sorted(singles, key=lambda x: x[1]["name"].lower()):
        label = (f"✅ {info['name']} · ${info['price']}"
                 if info["stock"] > 0 else f"❌ {info['name']} ({t['sold_out']})")
        markup.add(InlineKeyboardButton(
            label,
            callback_data=("buy_" if info["stock"] > 0 else "sold_out_") + key
        ))
    markup.row(
        InlineKeyboardButton(t["search"], callback_data="search_product"),
        InlineKeyboardButton(t["orders"], callback_data="my_orders")
    )
    markup.row(
        InlineKeyboardButton(t["deposit"], callback_data="payment_methods"),
        InlineKeyboardButton(t["support"], url=SUPPORT_WHATSAPP)
    )
    markup.row(
        InlineKeyboardButton(t["api"], callback_data="show_apis"),
        InlineKeyboardButton(t["lang"], callback_data="menu_lang")
    )
    if is_admin:
        markup.row(InlineKeyboardButton(t["admin"], callback_data="admin_panel"))
    return markup

def get_admin_markup():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("💰 فحص الرصيد", callback_data="adm_balance"),
        InlineKeyboardButton("💳 طرق الإيداع", callback_data="adm_deposits")
    )
    markup.row(
        InlineKeyboardButton("📊 سجل المعاملات", callback_data="adm_transactions"),
        InlineKeyboardButton("🔙 الرئيسية", callback_data="main_menu")
    )
    return markup

def send_home(chat_id):
    bot.send_message(
        chat_id, LANG_TEXTS[user_lang(chat_id)]["welcome"],
        reply_markup=get_main_menu_markup(chat_id, chat_id == ADMIN_ID)
    )

if bot:
    try:
        bot.set_my_commands([
            BotCommand("start", "تشغيل المتجر 🚀"),
            BotCommand("products", "تصفح المنتجات 🛍️"),
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
                rows.append(
                    f"📦 <b>{safe_html(order.get('product', 'منتج'))}</b>\n"
                    f"🔑 <code>{safe_html(order.get('item', ''))}</code>\n"
                    f"🕒 {safe_html(order.get('time', ''))}\n──────────────"
                )
            body = "📜 سجل مشترياتي السابقة:\n\n" + "\n".join(rows)
        bot.send_message(
            chat_id, body,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu")
            ),
            parse_mode="HTML"
        )

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
                bot.edit_message_text(
                    LANG_TEXTS[lang]["welcome"], chat_id, msg_id,
                    reply_markup=get_main_menu_markup(chat_id, is_admin)
                )
            except Exception:
                send_home(chat_id)

        elif data.startswith("fam_"):
            fam = data[4:]
            bot.answer_callback_query(call.id)
            markup = InlineKeyboardMarkup()
            found = [
                (k, v) for k, v in products.items()
                if v["family"] == fam
            ]
            for key, info in sorted(found, key=lambda x: x[1]["name"].lower()):
                if info["stock"] > 0:
                    markup.add(InlineKeyboardButton(
                        f"✅ {info['name']} · ${info['price']}",
                        callback_data="buy_" + key
                    ))
                else:
                    markup.add(InlineKeyboardButton(
                        f"❌ {info['name']} (نفد)",
                        callback_data="sold_out_" + key
                    ))
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
                    markup.add(InlineKeyboardButton(
                        f"✅ {info['name']} · ${info['price']}",
                        callback_data="buy_" + key
                    ))
            markup.add(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
            bot.edit_message_text("🔑 <b>خدمات API المتاحة:</b>", chat_id, msg_id,
                                  reply_markup=markup, parse_mode="HTML")

        elif data == "admin_panel" and is_admin:
            bot.answer_callback_query(call.id)
            bot.edit_message_text("🛠️ <b>لوحة تحكم الإدارة:</b>", chat_id, msg_id,
                                  reply_markup=get_admin_markup(), parse_mode="HTML")

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
            bot.send_message(chat_id, f"{title}\n<pre>{body}</pre>",
                             reply_markup=InlineKeyboardMarkup().add(
                                 InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")
                             ), parse_mode="HTML")

        elif data == "search_product":
            bot.answer_callback_query(call.id)
            USER_WAITING_FOR_SEARCH[chat_id] = True
            bot.edit_message_text(
                "🔍 أرسل اسم المنتج للبحث:", chat_id, msg_id,
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🏠 إلغاء", callback_data="main_menu")
                )
            )

        elif data == "payment_methods":
            bot.answer_callback_query(call.id)
            pay_info = f"💳 <b>شحن الرصيد / الدفع:</b>\n\n- Binance ID: <code>{safe_html(BINANCE_ID)}</code>"
            bot.edit_message_text(
                pay_info, chat_id, msg_id,
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu")
                ), parse_mode="HTML"
            )

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
            # لا نرسل بيانات وهمية لمنتجات الاختبار المجانية.
            if info["price"] <= 0:
                bot.send_message(chat_id, "⚠️ هذا المنتج مجاني/تجريبي ولم يتم تفعيل تسليمه. تواصل مع الإدارة.")
                notify_admin(f"⚠️ محاولة شراء منتج سعره صفر: {safe_html(info['name'])} (ID: {safe_html(key)})")
                return
            USER_SELECTED_PRODUCT[chat_id] = key
            markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton("🪙 إتمام الدفع الفوري", callback_data="pay_" + key)
            )
            markup.row(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
            msg = (
                f"🏷️ <b>{safe_html(info['name'])}</b>\n"
                f"💰 السعر: <b>${info['price']}</b> | التوفر: <b>{info['stock']}</b>\n\n"
                f"📝 <b>تفاصيل المنتج:</b>\n{safe_html(info['description'])}"
            )
            try:
                bot.delete_message(chat_id, msg_id)
            except Exception:
                pass
            bot.send_message(chat_id, msg, reply_markup=markup, parse_mode="HTML")

        elif data.startswith("pay_"):
            key = data[4:]
            info = products.get(key)
            bot.answer_callback_query(call.id)
            if not info or info["price"] <= 0:
                bot.send_message(chat_id, "تعذر تحديد المنتج. ارجع للقائمة وحاول مجدداً.")
                return
            USER_SELECTED_PRODUCT[chat_id] = key
            pay_msg = (
                f"🪙 قم بتحويل (${info['price']} USDT) إلى Binance ID: "
                f"<code>{safe_html(BINANCE_ID)}</code>\n\n"
                "ثم أرسل رقم المعاملة (Transaction ID) كما يظهر في سجل Binance Pay هنا في المحادثة."
            )
            bot.edit_message_text(
                pay_msg, chat_id, msg_id,
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu")
                ), parse_mode="HTML"
            )

        elif data == "my_orders":
            bot.answer_callback_query(call.id)
            orders = load_orders().get(str(chat_id), [])
            if not orders:
                body = "📜 لا توجد طلبات."
            else:
                body = "📜 سجل مشترياتي:\n" + "\n".join(
                    f"📦 {safe_html(o.get('product', 'منتج'))}\n"
                    f"🔑 <code>{safe_html(o.get('item', ''))}</code>"
                    for o in orders[-30:]
                )
            bot.edit_message_text(
                body, chat_id, msg_id,
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu")
                ), parse_mode="HTML"
            )

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
                        markup.add(InlineKeyboardButton(
                            f"✅ {info['name']} · ${info['price']}",
                            callback_data="buy_" + key
                        ))
            markup.row(InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu"))
            bot.send_message(
                chat_id,
                f"🔍 نتائج البحث: <b>{safe_html(message.text)}</b>" if found
                else f"❌ لا توجد نتائج لـ: <b>{safe_html(message.text)}</b>",
                reply_markup=markup, parse_mode="HTML"
            )
            return

        if chat_id not in USER_SELECTED_PRODUCT:
            bot.send_message(
                chat_id, "⚠️ يرجى اختيار المنتج أولاً من القائمة.",
                reply_markup=get_main_menu_markup(chat_id, chat_id == ADMIN_ID)
            )
            return

        if chat_id in USER_PROCESSING:
            bot.send_message(chat_id, "⏳ طلبك قيد المعالجة، انتظر قليلاً.")
            return

        reference = (message.text or "").strip()
        if not re.fullmatch(r"[A-Za-z0-9_-]{8,128}", reference):
            bot.send_message(
                chat_id,
                "❌ رقم العملية غير صالح. أرسل Transaction ID كما يظهر في Binance (من 8 إلى 128 حرفاً/رقماً)."
            )
            return

        # رقم الاختبار المقترح لا يطابق معاملة حقيقية، لكنه يمر عبر مسار الفحص.
        if payment_reference_already_used(reference):
            bot.send_message(chat_id, "❌ رقم هذه المعاملة استُخدم سابقاً ولا يمكن استخدامه مرة أخرى.")
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
                bot.send_message(
                    chat_id,
                    f"❌ <b>فشل التحقق:</b>\n{safe_html(payment['error'])}",
                    parse_mode="HTML"
                )
                return

            # Reserve the transaction immediately after successful Binance verification
            # and BEFORE contacting the supplier. A transaction can pay only once.
            if not reserve_payment_reference(
                reference, chat_id, info["name"],
                payment.get("amount", info["price"]),
                payment.get("currency", "USDT")
            ):
                bot.send_message(
                    chat_id,
                    "❌ رقم هذه المعاملة محجوز أو استُخدم بالفعل، ولا يمكن استخدامه مرة أخرى."
                )
                return

            bot.send_message(chat_id, "✅ تم تأكيد الدفع وحجز رقم المعاملة. جارٍ إرسال الطلب إلى المورد...")
            result = purchase_order_from_supplier(product_key, reference)
            if not result["success"]:
                supabase_update_transaction_status(reference, "SUPPLIER_REVIEW")
                notify_admin(
                    "🚨 <b>دفع مؤكد لكن طلب المورد فشل</b>\n"
                    f"الزبون: <code>{chat_id}</code>\n"
                    f"المنتج: {safe_html(info['name'])}\n"
                    f"مرجع الدفع: <code>{safe_html(reference)}</code>\n"
                    f"الخطأ: <code>{safe_html(result.get('error', 'غير معروف')[:700])}</code>"
                )
                bot.send_message(
                    chat_id,
                    "✅ تم تأكيد الدفع، لكن المورد لم يؤكد إتمام الطلب. "
                    "تم إشعار الإدارة، لا ترسل دفعة ثانية."
                )
                USER_SELECTED_PRODUCT.pop(chat_id, None)
                return

            delivery = extract_delivery_data(result["data"])
            if not delivery:
                supabase_update_transaction_status(reference, "PENDING_DELIVERY")
                # لا ندعي نجاح التسليم إذا لم تظهر بيانات الاعتماد في الرد.
                notify_admin(
                    "⚠️ <b>الدفع وطلب المورد تم قبولهما، لكن لم أستطع استخراج بيانات التسليم.</b>\n"
                    f"الزبون: <code>{chat_id}</code>\n"
                    f"المنتج: {safe_html(info['name'])}\n"
                    f"مرجع الدفع: <code>{safe_html(reference)}</code>\n"
                    "راجع Render Logs وابحث عن SUPPLIER ORDER DETAILS STRUCTURE و SUPPLIER DELIVERY STRUCTURE. "
                "تم تسجيل أسماء الحقول وأنواعها فقط دون تسجيل بيانات التفعيل السرية."
                )
                bot.send_message(
                    chat_id,
                    "✅ تم تأكيد الدفع وإرسال الطلب للمورد، لكن بيانات المنتج لم تصلنا بصيغة مفهومة. "
                    "تم إشعار الإدارة لمتابعة التسليم. لا تدفع مرة أخرى."
                )
                # نسجل الطلب كقيد المتابعة بدون اختلاق بيانات.
                orders = load_orders()
                orders.setdefault(str(chat_id), []).append({
                    "product": info["name"],
                    "item": "قيد المتابعة مع المورد - لم تصل بيانات التسليم بعد",
                    "reference": reference,
                    "payment_amount": payment.get("amount"),
                    "payment_currency": payment.get("currency"),
                    "status": "pending_delivery",
                    "time": time.strftime("%Y-%m-%d %H:%M:%S")
                })
                save_orders(orders)
                USER_SELECTED_PRODUCT.pop(chat_id, None)
                return

            supabase_update_transaction_status(reference, "DELIVERED")
            orders = load_orders()
            orders.setdefault(str(chat_id), []).append({
                "product": info["name"],
                "item": delivery,
                "reference": reference,
                "payment_amount": payment.get("amount"),
                "payment_currency": payment.get("currency"),
                "status": "delivered",
                "time": time.strftime("%Y-%m-%d %H:%M:%S")
            })
            save_orders(orders)

            delivery_message = (
                "🎉 <b>تم تأكيد الدفع والتسليم بنجاح!</b>\n\n"
                f"📦 <b>{safe_html(info['name'])}</b>\n"
                f"🔑 <b>بيانات المنتج:</b>\n<pre>{safe_html(delivery[:3500])}</pre>\n\n"
                "احتفظ بهذه الرسالة للرجوع إليها."
            )
            bot.send_message(
                chat_id, delivery_message, parse_mode="HTML",
                reply_markup=get_main_menu_markup(chat_id, chat_id == ADMIN_ID)
            )
            USER_SELECTED_PRODUCT.pop(chat_id, None)

        except Exception as exc:
            print("PAYMENT/DELIVERY HANDLER ERROR:", repr(exc))
            notify_admin(
                "🚨 خطأ غير متوقع أثناء معالجة طلب:\n"
                f"الزبون: <code>{chat_id}</code>\n"
                f"<code>{safe_html(str(exc)[:700])}</code>"
            )
            bot.send_message(
                chat_id,
                "حدث خطأ أثناء معالجة الطلب. تم إشعار الإدارة. "
                "لا تعاود الدفع قبل التواصل مع الدعم."
            )
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
    threading.Thread(
        target=lambda: app.run(
            host="0.0.0.0",
            port=int(os.environ.get("PORT", "10000")),
            use_reloader=False
        ),
        daemon=True
    ).start()

    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
        except Exception as exc:
            print("BOT POLLING ERROR:", repr(exc))
            time.sleep(5)
