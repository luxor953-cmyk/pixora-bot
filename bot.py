import os
import time
import hmac
import hashlib
import urllib.parse
import json
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY", "").strip()
BINANCE_SECRET_KEY = os.environ.get("BINANCE_SECRET_KEY", "").strip()
ADMIN_ID = 1004439571098
BINANCE_ID = "957483337"
RENDER_URL = os.environ.get("RENDER_URL", "https://pixora-bot-1.onrender.com").strip()
SUPPORT_WHATSAPP = "https://wa.me/213555668244"

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

RAW_PRODUCTS = [
    ("capcut", "🎞️ CapCut", 1.3, 
     "📱 CAPCUT PRO Individual – 30 DAYS\n\n"
     "📌 INFORMATIONS\n"
     "✔️ CapCut Pro account, valid for 29-30 days.\n"
     "✔️ Format : Email | Password\n\n"
     "Delivery is automatic after payment confirmation."),
     
    ("gemini", "💠 Gemini", 3.0, 
     "⚡ 18 Months Plan\n"
     "⚡ 5TB cloud storage included\n"
     "⚡ 100% Genuine Gemini AI Pro Subscription Activated on Your Own Gmail."),
     
    ("office", "🟩 Microsoft Office 365", 0.30, 
     "✔️ Microsoft 365 Plus – 100GB/1000GB | 5 Devices\n\n"
     "✔️ Activate on up to 5 devices\n"
     "✔️ Instant & automatic delivery"),
     
    ("autodesk", "🔺 Autodesk", 3.0, 
     "✔️ Autodesk Admin Dashboard Access\n"
     "✔️ 1 Year Subscription\n"
     "Delivery is automatic after payment confirmation."),
     
    ("canva", "🎨 Canva", 4.0, 
     "Canva Edu pro invite 499 user\n\n"
     "After placing your order, please send your Canva registered email address to receive your invitation."),
     
    ("adobe", "🔴 Adobe", 2.5, "- Full Adobe Creative Cloud access.\n- Full warranty and stability."),
    ("avira", "🔴 Avira", 2.0, "- Premium Antivirus & Security subscription."),
    ("chatgpt", "🔴 ChatGPT", 3.0, "- ChatGPT Plus account access."),
    ("coursera", "🔴 Coursera", 2.0, "- Coursera subscription for professional certificates."),
    ("duolingo", "🔴 Duolingo", 0.75, "- Duolingo Super 12 Months subscription."),
    ("elevenlabs", "🔴 ElevenLabs", 3.5, "- AI Voice Generator premium plan."),
    ("expressvpn", "🔴 ExpressVPN", 2.5, "- High-speed secure VPN subscription."),
    ("figma", "🔴 Figma", 2.0, "- Figma Pro team access for designers."),
    ("framer", "🔴 Framer", 2.0, "- Framer Pro web building subscription."),
    ("gamma", "🔴 Gamma", 2.0, "- AI presentations and docs generator."),
    ("grok", "🔴 Grok", 2.5, "- xAI Grok premium access."),
    ("hmavpn", "🔴 HMA VPN", 0.55, "- HideMyAss VPN secure access."),
    ("jetbrain", "🔴 JetBrain", 3.0, "- All Products Pack license access."),
    ("kaspersky", "🔴 Kaspersky", 2.0, "- Kaspersky Total Security license."),
    ("linkedin", "🔴 LinkedIn", 3.0, "- LinkedIn Premium Career/Business access."),
    ("lovable", "🔴 Lovable", 2.5, "- Full stack AI web app builder."),
    ("muse", "🔴 Muse", 2.0, "- Muse AI premium tools access."),
    ("notion",
