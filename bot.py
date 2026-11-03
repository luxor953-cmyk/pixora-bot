import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# === إعداداتك الخاصة ===
BOT_TOKEN = "9118344859:AAGXKPIzdLAByBR1QZhK13oM3XXmW9fDiaY"
ADMIN_ID = 514752764
RIP_CPP = "0079999900229772775"
BINANCE_ID = "957483337"
REDOTPAY_ID = "1198898814"
# ======================

bot = telebot.TeleBot(BOT_TOKEN)

# =========================================================================
# 📦 [قاعدة بيانات المخزون والتسليم التلقائي]
# أضف هنا حساباتك، روابطك، أو مفاتيح التفعيل الجديدة لكل صنف بنفس هذا التنسيق:
# =========================================================================
STOCK_DATABASE = {
    "capcut": [
        "CapCut_Key_1: user1@pixoras.com / pass123",
        "CapCut_Key_2: user2@pixoras.com / pass123",
        "CapCut_Key_3: user3@pixoras.com / pass123"
    ],
    "gemini": [
        "https://g.co/gemini/share/sample_link_1",
        "https://g.co/gemini/share/sample_link_2",
        "https://g.co/gemini/share/sample_link_3",
        "https://g.co/gemini/share/sample_link_4"
    ],
    "office": [
        "Office365_Key_1: acc1@pixora.store / P@ss1",
        "Office365_Key_2: acc2@pixora.store / P@ss2"
    ],
    "autodesk": [
        "Autodesk_Key_ABC123",
        "Autodesk_Key_XYZ789"
    ],
    "canva": [
        "https://www.canva.com/brand/join?inv=sample_team_link_1",
        "https://www.canva.com/brand/join?inv=sample_team_link_2"
    ]
}

# خادم ويب خفيف لإرضاء منصة Render وتشغيل الموقع بنجاح
app = Flask('')

@app.route('/')
def home():
    return "Pixora Store is Active & Running with Auto-Delivery!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# دالة القائمة الرئيسية مع قراءة الكميات الحقيقية من المخزون تلقائياً
@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    markup = InlineKeyboardMarkup(row_width=2)
    
    # حساب الكميات المتوفرة تلقائياً من قاعدة البيانات
    capcut_count = len(STOCK_DATABASE["capcut"])
    gemini_count = len(STOCK_DATABASE["gemini"])
    office_count = len(STOCK_DATABASE["office"])
    autodesk_count = len(STOCK_DATABASE["autodesk"])
    canva_count = len(STOCK_DATABASE["canva"])
    
    # الصفوف الشبكية مع الكميات الحية والأسعار
    btn_capcut = InlineKeyboardButton(f"🎬 CapCut · ({capcut_count})", callback_data="buy_capcut")
    btn_chatgpt = InlineKeyboardButton("🤖 ChatGPT · (15)", callback_data="prod_chatgpt")
    
    btn_gemini = InlineKeyboardButton(f"🔥 Gemini Ai · $3 ({gemini_count})", callback_data="buy_gemini")
    btn_office = InlineKeyboardButton(f"🪟 Microsoft 365 · ({office_count})", callback_data="buy_office")
    
    btn_autodesk = InlineKeyboardButton(f"🅰️ AUTODESK · ({autodesk_count})", callback_data="buy_autodesk")
    btn_canva = InlineKeyboardButton(f"🎨 Canva Pro · ({canva_count})", callback_data="buy_canva")
    
    markup.add(btn_capcut, btn_chatgpt, btn_gemini, btn_office, btn_autodesk, btn_canva)
    
    # منتج مميز مع الكمية
    btn_bestseller = InlineKeyboardButton("🔥 (💚 BEST SELLER) ChatGPT Plus · (5)", callback_data="prod_chatgpt")
    markup.add(btn_bestseller)
    
    # زر طرق الدفع الرئيسية
    btn_pay = InlineKeyboardButton("💳 طرق الدفع (CCP / Binance / RedotPay)", callback_data="show_payments")
    markup.add(btn_pay)
    
    bot.send_message(
        message.chat.id, 
        "🌐 **Choose Your Product / اختر منتجك المفضّل:**\n"
        "مرحباً بك في متجر **Pixora Store** (النظام الآلي الفوري):", 
        reply_markup=markup, 
        parse_mode="Markdown"
    )

# معالجة ضغطات الأزرار وعمليات الشراء والخصم والتسليم التلقائي
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    user_name = call.from_user.first_name

    # 1. منتج CapCut
    if call.data == "buy_capcut":
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("✅ تأكيد الدفع واستلام الحساب فوراً", callback_data="deliver_capcut"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        )
        bot.send_message(
            chat_id,
            "🎬 **CapCut Pro**\n\n"
            "📌 اشتراك رسمي لتفعيل كافة ميزات الذكاء الاصطناعي والتصدير المفتوح.\n"
            f"📦 **الكمية المتوفرة حالياً:** {len(STOCK_DATABASE['capcut'])}\n\n"
            "💳 بعد إتمام الدفع عبر Baridimob أو Binance أو RedotPay، اضغط زر التأكيد أدناه لاستلام حسابك في ثوانٍ:",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif call.data == "deliver_capcut":
        bot.answer_callback_query(call.id)
        if len(STOCK_DATABASE["capcut"]) > 0:
            item = STOCK_DATABASE["capcut"].pop(0) # سحب أول حساب وخصمه تلقائياً
            bot.send_message(
                chat_id,
                "🎉 **تم تأكيد طلبك وتسليم المنتج بنجاح!**\n\n"
                f"📦 **بيانات الحساب:**\n`{item}`\n\n"
                "شكراً لثقتك بمتجر **Pixora Store** 💚",
                parse_mode="Markdown"
            )
            bot.send_message(ADMIN_ID, f"🔔 **عملية بيع جديدة (CapCut):**\n👤 العميل: {user_name}\n🔑 تم تسليم: `{item}`", parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "⚠️ عذراً، نفدت كمية هذا المنتج مؤقتاً! يرجى التواصل مع المشرف.")

    # 2. منتج Gemini Ai
    elif call.data == "buy_gemini":
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("✅ تأكيد الدفع واستلام الرابط فوراً", callback_data="deliver_gemini"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        )
        bot.send_message(
            chat_id,
            "🌟 **Gemini Pro 18 Months**\n\n"
            "📌 حساب رسمي مدعوم بالذكاء الاصطناعي الأقوى من جوجل.\n"
            f"📦 **الكمية المتوفرة:** {len(STOCK_DATABASE['gemini'])}\n"
            "💰 **السعر:** $3\n\n"
            "اضغط زر التأكيد أدناه بعد الدفع لاستلام الرابط فوراً:",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif call.data == "deliver_gemini":
        bot.answer_callback_query(call.id)
        if len(STOCK_DATABASE["gemini"]) > 0:
            item = STOCK_DATABASE["gemini"].pop(0)
            bot.send_message(
                chat_id,
                "🎉 **تم تسليم طلبك بنجاح!**\n\n"
                f"🔗 **رابط الحساب:**\n`{item}`",
                parse_mode="Markdown"
            )
            bot.send_message(ADMIN_ID, f"🔔 **عملية بيع جديدة (Gemini):**\n👤 العميل: {user_name}\n🔑 تم تسليم: `{item}`", parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "⚠️ عذراً، نفدت كمية حسابات Gemini مؤقتاً.")

    # 3. منتج Microsoft 365
    elif call.data == "buy_office":
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("✅ تأكيد الدفع واستلام الحساب فوراً", callback_data="deliver_office"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        )
        bot.send_message(
            chat_id,
            "🪟 **Microsoft Office 365**\n\n"
            f"📦 **الكمية المتوفرة:** {len(STOCK_DATABASE['office'])}\n\n"
            "اضغط زر التأكيد لاستلام مفتاح أو حساب الأوفيس فوراً:",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif call.data == "deliver_office":
        bot.answer_callback_query(call.id)
        if len(STOCK_DATABASE["office"]) > 0:
            item = STOCK_DATABASE["office"].pop(0)
            bot.send_message(chat_id, f"🎉 **تم تسليم طلبك بنجاح!**\n\n`{item}`", parse_mode="Markdown")
            bot.send_message(ADMIN_ID, f"🔔 **بيع Office 365:** العميل {user_name} استلم: `{item}`", parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "⚠️ عذراً، نفدت كمية Microsoft 365 مؤقتاً.")

    # 4. منتج Autodesk
    elif call.data == "buy_autodesk":
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("✅ تأكيد الدفع واستلام التفعيل فوراً", callback_data="deliver_autodesk"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        )
        bot.send_message(
            chat_id,
            "🅰️ **AutoDesk Full Apps**\n\n"
            f"📦 **الكمية المتوفرة:** {len(STOCK_DATABASE['autodesk'])}\n\n"
            "اضغط زر التأكيد لاستلام تفعيل أوتوديسك فوراً:",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif call.data == "deliver_autodesk":
        bot.answer_callback_query(call.id)
        if len(STOCK_DATABASE["autodesk"]) > 0:
            item = STOCK_DATABASE["autodesk"].pop(0)
            bot.send_message(chat_id, f"🎉 **تم تسليم طلبك بنجاح!**\n\n`{item}`", parse_mode="Markdown")
            bot.send_message(ADMIN_ID, f"🔔 **بيع Autodesk:** العميل {user_name} استلم: `{item}`", parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "⚠️ عذراً، نفدت كمية Autodesk مؤقتاً.")

    # 5. منتج Canva Pro
    elif call.data == "buy_canva":
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("✅ تأكيد الدفع واستلام الرابط فوراً", callback_data="deliver_canva"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        )
        bot.send_message(
            chat_id,
            "🎨 **Canva Pro / Admin Account**\n\n"
            f"📦 **الكمية المتوفرة:** {len(STOCK_DATABASE['canva'])}\n\n"
            "اضغط زر التأكيد لاستلام رابط دعوة كانفا برو فوراً:",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif call.data == "deliver_canva":
        bot.answer_callback_query(call.id)
        if len(STOCK_DATABASE["canva"]) > 0:
            item = STOCK_DATABASE["canva"].pop(0)
            bot.send_message(chat_id, f"🎉 **تم تسليم طلبك بنجاح!**\n\n🔗 `{item}`", parse_mode="Markdown")
            bot.send_message(ADMIN_ID, f"🔔 **بيع Canva Pro:** العميل {user_name} استلم: `{item}`", parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "⚠️ عذراً، نفدت كمية Canva Pro مؤقتاً.")

    # الأقسام الأخرى وطرق الدفع
    elif call.data == "prod_chatgpt":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "🤖 قسم ChatGPT قيد التحديث للاستلام التلقائي قريباً، تواصل مع المشرف عبر أزرار الدفع.")

    elif call.data == "show_payments":
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🏦 Baridimob (CCP)", callback_data="pay_ccp"),
            InlineKeyboardButton("🪙 Binance Pay", callback_data="pay_binance"),
            InlineKeyboardButton("💳 RedotPay ID", callback_data="pay_redotpay"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        )
        bot.send_message(
            chat_id,
            f"💳 **معلومات الدفع في متجر Pixora Store:**\n\n"
            f"🏦 **CCP (بريد الجزائر):**\n`{RIP_CPP}`\n\n"
            f"🪙 **Binance Pay ID:**\n`{BINANCE_ID}`\n\n"
            f"💳 **RedotPay ID:**\n`{REDOTPAY_ID}`\n\n"
            "بعد التحويل، توجه للمنتج واضغط على زر تأكيد الدفع لاستلام طلبك فوراً!",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif call.data == "pay_ccp":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, f"🏦 **RIP Baridimob (CCP):**\n`{RIP_CPP}`", parse_mode="Markdown")
    elif call.data == "pay_binance":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, f"🪙 **Binance ID:** `{BINANCE_ID}`", parse_mode="Markdown")
    elif call.data == "pay_redotpay":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, f"💳 **RedotPay ID:** `{REDOTPAY_ID}`", parse_mode="Markdown")

    elif call.data == "main_menu":
        bot.answer_callback_query(call.id)
        send_welcome(call.message)

# تشغيل خادم الويب والبوت معاً
if __name__ == '__main__':
    t = Thread(target=run_web)
    t.start()
    bot.infinity_polling()
