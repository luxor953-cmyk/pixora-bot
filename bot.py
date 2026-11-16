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
