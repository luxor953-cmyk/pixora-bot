import os
import time
import json
import threading
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_ID = 1004439571098
BINANCE_ID = "957483337"
RENDER_URL = os.environ.get("RENDER_URL", "").strip()
SUPPORT_WHATSAPP = "https://wa.me/213555668244"

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
app = Flask(__name__)

# قائمة الـ 31 صنفاً الأصلية كاملة بالأسعار
RAW_PRODUCTS = [
    # 1. المونتاج والتصميم
    ("capcut_1m", "🎞️ CapCut Pro (شهر)", 1.30),
    ("capcut_1y", "🎞️ CapCut Pro (سنة)", 9.50),
    ("filmora", "🎬 Wondershare Filmora 13", 8.00),
    ("canva_pro", "🎨 Canva Pro (سنة)", 4.00),
    ("picsart", "📸 PicsArt Gold (سنة)", 3.00),

    # 2. أدوات الذكاء الاصطناعي
    ("chatgpt_plus", "🤖 ChatGPT Plus (شهر)", 18.00),
    ("claude_pro", "🧠 Claude Pro (شهر)", 18.00),
    ("gemini_adv", "💠 Google Gemini Advanced", 3.00),
    ("elevenlabs", "🎙️ ElevenLabs Starter", 5.00),
    ("midjourney", "🎨 Midjourney Basic", 10.00),
    ("runway", "📹 Runway Gen-2 (شهر)", 12.00),
    ("perplexity", "🔍 Perplexity Pro (شهر)", 6.00),

    # 3. برامج مايكروسوفت والإنتاجية
    ("office_365", "🟩 Microsoft Office 365", 0.30),
    ("windows_11", "🪟 Windows 11 Pro Key", 3.50),
    ("windows_10", "🪟 Windows 10 Pro Key", 2.50),
    ("autodesk", "🔺 Autodesk All Apps (سنة)", 3.00),

    # 4. الحماية والـ VPN
    ("nordvpn", "🛡️ NordVPN Premium (سنة)", 3.50),
    ("expressvpn", "⚡ ExpressVPN (شهر)", 4.00),
    ("surfshark", "🦈 Surfshark VPN (سنة)", 3.00),
    ("kaspersky", "🦠 Kaspersky Total Security", 5.00),

    # 5. الترفيه ومنصات البث
    ("netflix_1m", "🍿 Netflix UHD (شهر)", 3.50),
    ("netflix_3m", "🍿 Netflix UHD (3 أشهر)", 9.00),
    ("spotify_ind", "🎵 Spotify Premium (شهر)", 2.00),
    ("spotify_1y", "🎵 Spotify Premium (سنة)", 11.00),
    ("youtube_prem", "▶️ YouTube Premium (شهر)", 2.00),
    ("youtube_6m", "▶️ YouTube Premium (6 أشهر)", 8.50),
    ("crunchyroll", "🍥 Crunchyroll Mega Fan", 2.00),
    ("shahid_vip", "⭐ Shahid VIP (شهر)", 3.50),
    ("iptv_1y", "📺 اشتراك IPTV (سنة)", 12.00),

    # 6. التعليم والتطوير
    ("duolingo", "🦉 Duolingo Super (سنة)", 4.50),
    ("github_pack", "🐙 GitHub Student Pack", 7.00)
]

PRODUCTS_INFO = {k: {"name": n, "price": p} for k, n, p in RAW_PRODUCTS}

# قاعدة بيانات المخزون (المتوفر فقط يوضع هنا، وباقي الأصناف رصيدها 0 وتظهر كـ Sold Out)
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
        print("Save error:", e)

WELCOME_TEXT = "🔥 <b>أهلاً بك في متجر Pixora Store الرقمي!</b> 🚀\n\n⚡
