import os
import time
import json
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.environ.get("ADMIN_ID", "1004439571")) 
BINANCE_ID = "957483337"
RENDER_URL = os.environ.get("RENDER_URL", "https://pixora-bot.onrender.com").strip()
SUPPORT_WHATSAPP = "https://wa.me/213555668244"

# التحقق الصارم من التوكن
if not BOT_TOKEN or ":" not in BOT_TOKEN:
    raise ValueError("⚠️ خطأ حرج: متغير البيئة BOT_TOKEN غير موجود أو غير مدخل في لوحة تحكم Render!")

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# قائمة المنتجات الكاملة مع الأوصاف الأصلية المفصلة
RAW_PRODUCTS = [
    (
        "capcut",
        "🎞️ CapCut Pro 1 Month FW",
        1.47,
        "📰 Description:\n"
        "- Full 30 days private Pro Team account.\n"
        "- Maximum 2 devices , with full warranty.\n"
        "- Stable Account full 30 days (no 7days renew ).\n"
        "- Login to mobile App first next to laptop (desktop App no web) via QR code ."
    ),
    (
        "gemini",
        "💠 Gemini Ai · Gemini Pro 18 Months Link",
        3.0,
        "Description\n"
        "⚡ 18 Months Plan\n"
        "⚡ 5TB cloud storage included\n"
        "⚡ You can add 5 users\n"
        "⚡ No Shared\n"
        "⚡ 100% Private \n"
        "⚡ NO NEED ANY CARD\n"
        "⚡ The link is delivered via a verified custom domain and redirects to the official Google Gemini website for activation.\n"
        "🔥 Works in any country, no verification required\n"
        "🚫 Non Warranty After 1H of Delivery\n\n"
        "⚡ 100% Genuine Gemini AI Pro Subscription Activated on Your Own Gmail."
    ),
    (
        "office",
        "📱 Microsoft 365 · Microsoft Office 365 1Tb 5 Devices Lifetime",
        1.0,
        "Description\n"
        "✔️ Microsoft 365 Plus – 100GB/1000GB | 5 Devices\n\n"
        "📱 Full access to Microsoft Office apps.\n\n"
        "✔️ Format : Email | Password\n\n"
        "✔️ Word, Excel, PowerPoint, Outlook & more\n"
        "✔️ Activate on up to 5 devices\n"
        "✔️ Compatible with Windows, Mac, Android & iOS\n"
        "✔️ 100GB/1000GB OneDrive cloud storage\n"
        "✔️ Automatic updates & premium features\n"
        "✔️ Instant & automatic delivery\n\n"
        "🛡 2-Year Warranty & Activation Support\n\n"
        "⚠️ Important Notes :\n"
        "- Keep your login credentials safe, forgotten password in not covered by Warranty.\n"
        "- OneDrive Storage is not covered by Warranty always keep backup for your files."
    ),
    (
        "autodesk",
        "🔺 Autodesk all Apps 1 Year",
        0.60,
        "📰 Description:\n"
        "🎓 1 year subscription to Autodesk Student.\n"
        "📧 Invitation in customer's email to Autodesk.\n"
        "💻 Almost all apps are included (3ds Max, AutoCAD, Fusion 360, Maya, Revit...)\n"
        "💬 If you want to add a specific app (message us)"
    ),
    (
        "canva",
        "🎨 Canva Education Panel — Quick Setup Guide",
        4.0,
        "🚀 Canva Education Panel — Quick Setup Guide 🎓\n"
        "1
