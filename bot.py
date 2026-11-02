import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# === إعداداتك الخاصة ===
BOT_TOKEN = "8884467242:AAGqwLhTOuQdpRdOy5GCuhhAOoxuypM_Y4Y"
ADMIN_ID = 514752764
RIP_CPP = "0079999900229772775"
BINANCE_ID = "957483337"
REDOTPAY_INFO = "1198898814"
# ======================

bot = telebot.TeleBot(BOT_TOKEN)

# دالة عرض القائمة الرئيسية والمنتجات
@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    markup = InlineKeyboardMarkup(row_width=2)
    
    # قائمة المنتجات
    btn_capcut = InlineKeyboardButton("🎬 CapCut", callback_data="buy_capcut")
    btn_chatgpt = InlineKeyboardButton("🤖 ChatGPT", callback_data="buy_chatgpt")
    markup.add(btn_capcut, btn_chatgpt)
    
    btn_gemini = InlineKeyboardButton("1️⃣ Gemini Ai", callback_data="buy_gemini")
    btn_m365 = InlineKeyboardButton("🪟 Microsoft 365", callback_data="buy_m365")
    markup.add(btn_gemini, btn_m365)
    
    btn_office_p = InlineKeyboardButton("📦 Office Pro Plus (P...", callback_data="buy_office_p")
    btn_win_phone = InlineKeyboardButton("🪟 Windows (Phone...", callback_data="buy_win_phone")
    markup.add(btn_office_p, btn_win_phone)
    
    btn_office_on = InlineKeyboardButton("🌐 Office PP (Online...", callback_data="buy_office_on")
    btn_win_on = InlineKeyboardButton("🌐 Windows (Online...)", callback_data="buy_win_on")
    markup.add(btn_office_on, btn_win_on)
    
    btn_autodesk = InlineKeyboardButton("🅰️ AUTODESK", callback_data="buy_autodesk")
    btn_muse = InlineKeyboardButton("🎵 Muse AI", callback_data="buy_muse")
    markup.add(btn_autodesk, btn_muse)
    
    btn_best_seller = InlineKeyboardButton("🔥 (💚 BEST SELLER) ChatGPT Plus (G Pay...", callback_data="buy_best_seller")
    markup.add(btn_best_seller)
    
    btn_gemini_pro = InlineKeyboardButton("1️⃣ 🔥 Gemini Pro 18 Months Link • $3 (4)", callback_data="buy_gemini_pro")
    markup.add(btn_gemini_pro)
    
    btn_duolingo = InlineKeyboardButton("🦉 Duolingo Super 12 Months • $0.75 (5)", callback_data="buy_duolingo")
    markup.add(btn_duolingo)
    
    btn_adobe = InlineKeyboardButton("🎨 Adobe Express 12M • $0.35 (10)", callback_data="buy_adobe")
    markup.add(btn_adobe)
    
    btn_hma = InlineKeyboardButton("🦊 HMA VPN Android/PC 30-25 Days • $0.55 (1)", callback_data="buy_hma")
    markup.add(btn_hma)
    
    btn_spotify = InlineKeyboardButton("🎧 Spotify Premium 3M • $1.45 (2)", callback_data="buy_spotify")
    markup.add(btn_spotify)
    
    btn_crunchyroll = InlineKeyboardButton("🍿 Crunchyroll 1 Month Redeem Link • $0.6 (5)", callback_data="buy_crunchyroll")
    markup.add(btn_crunchyroll)
    
    # أزرار طرق الدفع
    btn_ccp = InlineKeyboardButton("🏦 CCP بريد الجزائر", callback_data="pay_ccp")
    btn_binance = InlineKeyboardButton("🪙 Binance Pay", callback_data="pay_binance")
    btn_redotpay = InlineKeyboardButton("💳 RedotPay ID", callback_data="pay_redotpay")
    markup.add(btn_ccp, btn_binance)
    markup.add(btn_redotpay)
    
    # زر القائمة الرئيسية
    btn_main = InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
    markup.add(btn_main)
    
    bot.send_message(message.chat.id, "Choose Your Product:", reply_markup=markup)

# معالجة الضغط على أزرار الدفع
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == "pay_ccp":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"🏦 **معلومات الدفع عبر بريد الجزائر (CCP):**\n`{RIP_CPP}`", parse_mode="Markdown")
    elif call.data == "pay_binance":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"🪙 **معلومات الدفع عبر Binance Pay:**\nID: `{BINANCE_ID}`", parse_mode="Markdown")
    elif call.data == "pay_redotpay":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"💳 **معلومات الدفع عبر RedotPay:**\nID: `{REDOTPAY_INFO}`", parse_mode="Markdown")

# تشغيل البوت
bot.infinity_polling()
