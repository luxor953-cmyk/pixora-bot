import os
import time
import hmac
import hashlib
import urllib.parse
import requests
import telebot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto
)
from flask import Flask, request

BOT_TOKEN = os.environ["BOT_TOKEN"]
BINANCE_API_KEY = os.environ["BINANCE_API_KEY"]
BINANCE_SECRET_KEY = os.environ["BINANCE_SECRET_KEY"]

ADMIN_ID = 1004439571098
BINANCE_ID = "957483337"
RENDER_URL = "https://pixora-bot-egyp.onrender.com"
SUPPORT_WHATSAPP = "https://wa.me/213555668244"

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

try:
    bot.remove_webhook()
    bot.set_webhook(url=RENDER_URL + "/" + BOT_TOKEN)
except Exception as e:
    print("Webhook error:", e)

PRODUCTS_INFO = {
    "capcut": {
        "name": "🎞️ CapCut",
        "price": 2.0,
        "description": (
            "- Full 30 days private Pro Team account .\n"
            "- Maximum 2 devices , with full warranty .\n"
            "- Stable Account full 30 days (no 7days renew ).\n"
            "- Login to mobile App first next to laptop "
            "(desktop App no web) via QR code ."
        )
    },
    "gemini": {
        "name": "💠 Gemini",
        "price": 2.0,
        "description": (
            "- Full access to Gemini Advanced & Pro features.\n"
            "- Direct official invite or shared private account.\n"
            "- Fast response and full warranty for the duration."
        )
    },
    "office": {
        "name": "🟩 Microsoft 365",
        "price": 2.0,
        "description": (
            "- Official Microsoft 365 account "
            "(5 PCs/Macs + 5 Tablets + 5 Phones).\n"
            "- 1TB OneDrive Cloud storage included.\n"
            "- Full warranty and multi-device support."
        )
    },
    "autodesk": {
        "name": "🔺 Autodesk",
        "price": 3.0,
        "description": (
            "- Official Autodesk Educational/Pro access.\n"
            "- Access to AutoCAD, Revit, Maya, and more.\n"
            "- Full warranty and stable subscription."
        )
    },
    "canva": {
        "name": "🎨 Canva",
        "price": 2.0,
        "description": (
            "- Canva Pro Team Invitation.\n"
            "- Unlock all premium templates, fonts, "
            "and background remover.\n"
            "- Private account safety with full warranty."
        )
    },
    "adobe": {
        "name": "🔴 Adobe",
        "price": 2.5,
        "description": (
            "- Full Adobe Creative Cloud access.\n"
            "- Full warranty and stability."
        )
    },
    "avira": {
        "name": "🔴 Avira",
        "price": 2.0,
        "description": (
            "- Premium Antivirus & Security subscription.\n"
            "- Full warranty."
        )
    },
    "chatgpt": {
        "name": "🔴 ChatGPT",
        "price": 3.0,
        "description": (
            "- ChatGPT Plus account access.\n"
            "- Fast GPT-4o and DALL-E generation."
        )
    },
    "coursera": {
        "name": "🔴 Coursera",
        "price": 2.0,
        "description": (
            "- Coursera subscription for "
            "professional certificates."
        )
    },
    "duolingo": {
        "name": "🔴 Duolingo",
        "price": 0.75,
        "description": (
            "- Duolingo Super 12 Months subscription."
        )
    },
    "elevenlabs": {
        "name": "🔴 ElevenLabs",
        "price": 3.5,
        "description": (
            "- AI Voice Generator premium plan."
        )
    },
    "expressvpn": {
        "name": "🔴 ExpressVPN",
        "price": 2.5,
        "description": (
            "- High-speed secure VPN subscription."
        )
    },
    "figma": {
        "name": "🔴 Figma",
        "price": 2.0,
        "description": (
            "- Figma Pro team access for designers."
        )
    },
    "framer": {
        "name": "🔴 Framer",
        "price": 2.0,
        "description": (
            "- Framer Pro web building subscription."
        )
    },
    "gamma": {
        "name": "🔴 Gamma",
        "price": 2.0,
        "description": (
            "- AI presentations and docs generator."
        )
    },
    "grok": {
        "name": "🔴 Grok",
        "price": 2.5,
        "description": (
            "- xAI Grok premium access."
        )
    },
    "hmavpn": {
        "name": "🔴 HMA VPN",
        "price": 0.55,
        "description": (
            "- HideMyAss VPN secure access."
        )
    },
    "jetbrain": {
        "name": "🔴 JetBrain",
        "price": 3.0,
        "description": (
            "- All Products Pack license access."
        )
    },
    "kaspersky": {
        "name": "🔴 Kaspersky",
        "price": 2.0,
        "description": (
            "- Kaspersky Total Security license."
        )
    },
    "linkedin": {
        "name": "🔴 LinkedIn",
        "price": 3.0,
        "description": (
            "- LinkedIn Premium Career/Business access."
        )
    },
    "lovable": {
        "name": "🔴 Lovable",
        "price": 2.5,
        "description": (
            "- Full stack AI web app builder."
        )
    },
    "muse": {
        "name": "🔴 Muse",
        "price": 2.0,
        "description": (
            "- Muse AI premium tools access."
        )
    },
    "notion": {
        "name": "🔴 Notion",
        "price": 2.0,
        "description": (
            "- Notion Pro workspace subscription."
        )
    },
    "youtube": {
        "name": "🔴 YouTube",
        "price": 2.0,
        "description": (
            "- YouTube Premium ad-free subscription."
        )
    },
    "ilovepdf": {
        "name": "🔴 iLovePdf",
        "price": 1.5,
        "description": (
            "- iLovePDF Premium tools access."
        )
    },
    "api": {
        "name": "🔴 API",
        "price": 5.0,
        "description": (
            "- High limit developer API keys
