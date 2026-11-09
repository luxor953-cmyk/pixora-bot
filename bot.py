import os
import time
import json
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.environ.get("ADMIN_ID", "1004439571")) 
BINANCE_ID = "957483337"
SUPPORT_WHATSAPP = "https://wa.me/213555668244"

if not BOT_TOKEN or ":" not in BOT_TOKEN:
    raise ValueError("⚠️ خطأ: متغير البيئة BOT_TOKEN غير موجود أو صيغته خاطئة في لوحة تحكم Render!")

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# قائمة المنتجات الـ 31 الكاملة مع الأوصاف الأصلية المفصلة
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
        "1️⃣ Secure the Email ✉️\n"
        "Log in to the provided Outlook account and add your personal email or phone number as a recovery method 🔒 (do not change the original account details).\n"
        "2️⃣ First Login 🕵️‍♂️\n"
        "Open an Incognito / Private window and sign in using the main Canva account 🔑.\n"
        "3️⃣ Add Your Personal Account 👨‍🏫\n"
        "Go to Team Settings ⚙️ → Members 👥 → Invite Members, and invite your personal Canva email as a Teacher / Co-Teacher 📩.\n"
        "4️⃣ Log Out & Manage 🎛\n"
        "Accept the invite from your personal email ✅, log out of the main account completely 🚪, and use your personal account to manage the panel (add/remove members) from now on 💻.\n"
        "⚠️ Important Reminders 🛑\n"
        "❌ Do not delete the main account or change the team/panel name.\n"
        "📈 Add members gradually to keep the account safe.\n"
        "🌍 Keep your login location/IP consistent (avoid switching VPNs frequently)."
    ),
    ("adobe", "🔴 Adobe", 2.5, "Full Adobe Creative Cloud access."),
    ("avira", "🔴 Avira", 2.0, "Premium Antivirus & Security subscription."),
    ("chatgpt", "🔴 ChatGPT", 3.0, "ChatGPT Plus account access."),
    ("coursera", "🔴 Coursera", 2.0, "Coursera subscription for certificates."),
    ("duolingo", "🔴 Duolingo", 0.75, "Duolingo Super 12 Months."),
    ("elevenlabs", "🔴 ElevenLabs", 3.5, "AI Voice Generator premium plan."),
    ("expressvpn", "🔴 ExpressVPN", 2.5, "High-speed secure VPN subscription."),
    ("figma", "🔴 Figma", 2.0, "Figma Pro team access for designers."),
    ("framer", "🔴 Framer", 2.0, "Framer Pro web building subscription."),
    ("gamma", "🔴 Gamma", 2.0, "AI presentations and docs generator."),
    ("grok", "🔴 Grok", 2.5, "xAI Grok premium access."),
    ("hmavpn", "🔴 HMA VPN", 0.55, "HideMyAss VPN secure access."),
    ("jetbrain", "🔴 JetBrain", 3.0, "All Products Pack license access."),
    ("kaspersky", "🔴 Kaspersky", 2.0, "Kaspersky Total Security license."),
    ("linkedin", "🔴 LinkedIn", 3.0, "LinkedIn Premium Career/Business access."),
    ("lovable", "🔴 Lovable", 2.5, "Full stack AI web app builder."),
    ("muse", "🔴 Muse", 2.0, "Muse AI premium tools access."),
    ("notion", "🔴 Notion", 2.0, "Notion Pro workspace subscription."),
    ("youtube", "🔴 YouTube", 2.0, "YouTube Premium ad-free subscription."),
    ("ilovepdf", "🔴 iLovePdf", 1.5, "iLovePDF Premium tools access."),
    ("api", "🔴 API", 5.0, "High limit developer API keys."),
    ("grammarly", "🔴 Grammarly", 2.0, "Grammarly Premium writing assistant."),
    ("nordvpn", "🔴 Nord Vpn", 2.0, "NordVPN secure high-speed servers."),
    ("scribd", "🔴 Scribd", 2.0, "Scribd ebooks and audiobooks access."),
    ("wispr", "🔴 Wispr", 2.0, "Wispr Flow voice dictation tool."),
    ("udemy", "🔴 Udemy", 2.0, "Premium courses access plan.")
]

PRODUCTS_INFO = {k: {"name": n, "price": p, "description": d} for k, n, p, d in RAW_PRODUCTS}

STOCK_DATABASE = {k: [] for k in PRODUCTS_INFO}
STOCK_DATABASE["capcut"] = ["CapCut_Key_1: user1@pixoras.com / pass123"]
STOCK_DATABASE["gemini"] = ["https://g.co/gemini/share/sample_link_1"]
STOCK_DATABASE["office"] = ["Office365_Key_1: kc5921@o365pp.com / &$^2^jGq"]
STOCK_DATABASE["autodesk"] = ["Autodesk_Key_ABC123"]
STOCK_DATABASE["canva"] = ["https://www.canva.com/brand/join?inv=sample_1"]

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
        print("Error saving orders:", e)

WELCOME
