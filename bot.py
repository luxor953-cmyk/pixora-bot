import os
import time
import hmac
import hashlib
import urllib.parse
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request

# === إعداداتك الخاصة ===
BOT_TOKEN = "9118344859:AAFqrcRY71z4f3fC87fs91c4z_wDQVHzyfo"
ADMIN_ID = 1004439571098
BINANCE_ID = "957483337"
RENDER_URL = "https://pixora-bot-egyp.onrender.com"

# === مفاتيح باينانس الخاصة بك ===
BINANCE_API_KEY = "d6KILQscYZEbSg4SaOf0YAQ02G8tx6a2IkweYQZZjU8F00hw9YvvivEMuOdppw"
BINANCE_SECRET_KEY = "qSiNFjXEOqAEAo9yG5w62yas7utcmJ3zlnXC5JRL97AfUTHSOqjdFsqQ3DmhjRiw"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

try:
    bot.remove_webhook()
    bot.set_webhook(url=RENDER_URL + "/" + BOT_TOKEN)
except Exception as e:
    print("Webhook error:", e)

# الأسعار والمنتجات بالصيغة النصية النظيفة
PRODUCTS_INFO = {
    "capcut": {"name": "CapCut Pro", "price": 1.5},
    "gemini": {"name": "Gemini Pro", "price": 2.0},
    "office": {"name": "Microsoft 365", "price": 2.0},
    "autodesk": {"name": "AUTODESK", "price": 3.0},
    "canva": {"name": "Canva Pro", "price": 2.0}
}

# المخزون بالكميات والأسعار المطلوبة
STOCK_DATABASE = {
    "capcut": [
        "CapCut_Key_1: user1@pixoras.com / pass123"
    ],
