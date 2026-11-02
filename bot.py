import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# === إعداداتك الخاصة ===
BOT_TOKEN = "8884467242:AAGqwLhTOuQdpRdOy5GCuhhAOoxuypM_Y4Y"
ADMIN_ID = 514752764
RIP_CPP = "0079999900229772775"
BINANCE_ID = "957483337"
REDOTPAY_ID = "1198898814"
# ======================

bot = telebot.TeleBot(BOT_TOKEN)

# خادم ويب خفيف لإرضاء منصة Render وتشغيل الموقع بنجاح
app = Flask('')

@app.route('/')
def home():
    return "Pixora Store is Active & Running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# دالة القائمة الرئيسية مع الكميات والأسعار المنظمة
@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    markup = InlineKeyboardMarkup(row_width=2)
    
    # الصفوف الشبكية مع الكميات والأسعار
    btn_capcut = InlineKeyboardButton("🎬 CapCut · (10)", callback_data="prod_capcut")
    btn_chatgpt = InlineKeyboardButton("🤖 ChatGPT · (15)", callback_data="prod_chatgpt")
    
    btn_gemini = InlineKeyboardButton("🔥 Gemini Ai · $3 (4)", callback_data="prod_gemini")
    btn_office = InlineKeyboardButton("🪟 Microsoft 365 · (8)", callback_data="prod_office")
    
    btn_autodesk = InlineKeyboardButton("🅰️ AUTODESK · (3)", callback_data="prod_autodesk")
    btn_canva = InlineKeyboardButton("🎨 Canva Pro · (12)", callback_data="prod_canva")
    
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
        "مرحباً بك في متجر **Pixora Store**، يرجى اختيار الخدمة المطلوبة:", 
        reply_markup=markup, 
        parse_mode="Markdown"
    )

# معالجة ضغطات الأزرار
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    
    if call.data == "prod_gemini":
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("💳 شراء عبر Baridimob", callback_data="pay_ccp"),
            InlineKeyboardButton("🟡 شراء عبر Binance", callback_data="pay_binance"),
            InlineKeyboardButton("💳 شراء عبر RedotPay", callback_data="pay_redotpay"),
            InlineKeyboardButton("🏠 Main Menu / القائمة الرئيسية", callback_data="main_menu")
        )
        bot.send_message(
            chat_id,
            "🌟 **Gemini Pro 18 Months**\n\n"
            "📌 **الوصف:** حساب رسمي مدعوم بالذكاء الاصطناعي الأقوى من جوجل لمدة 18 شهر.\n"
            "📦 **الكمية المتوفرة:** 4 حسابات جاهزة.\n"
            "💰 **السعر:** $3\n\n"
            "اختر وسيلة الدفع لإتمام الطلب:",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif call.data == "prod_chatgpt":
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("📚 ChatGPT تعليمي · (6)", callback_data="gpt_edu"),
            InlineKeyboardButton("👤 ChatGPT خاص · (4)", callback_data="gpt_private"),
            InlineKeyboardButton("👥 ChatGPT مشترك · (5)", callback_data="gpt_shared"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        )
        bot.send_message(
            chat_id,
            "🤖 **مشتريات ChatGPT**\n\n"
            "📌 اختر نوع الحساب المناسب لك والكمية المطلوبة:",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif call.data in ["gpt_edu", "gpt_private", "gpt_shared"]:
        bot.answer_callback_query(call.id)
        type_name = "تعليمي" if call.data == "gpt_edu" else ("خاص" if call.data == "gpt_private" else "مشترك")
        markup = InlineKeyboardMarkup(row_width=3)
        markup.add(
            InlineKeyboardButton("1 شهر", callback_data="pay_prompt"),
            InlineKeyboardButton("3 أشهر", callback_data="pay_prompt"),
            InlineKeyboardButton("12 شهر", callback_data="pay_prompt"),
            InlineKeyboardButton("⬅️ رجوع", callback_data="prod_chatgpt")
        )
        bot.send_message(
            chat_id,
            f"📅 لقد اخترت ChatGPT ({type_name}).\nاختر المدة المطلوبة:",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif call.data == "prod_capcut":
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("💳 الدفع وإتمام الطلب", callback_data="show_payments"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        )
        bot.send_message(
            chat_id,
            "🎬 **CapCut Pro**\n\n"
            "📌 اشتراك رسمي لتفعيل كافة ميزات الذكاء الاصطناعي والتصدير المفتوح.\n"
            "📦 **الكمية المتوفرة:** 10 اشتراكات.",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif call.data == "prod_office":
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("💳 الدفع وإتمام الطلب", callback_data="show_payments"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        )
        bot.send_message(
            chat_id,
            "🪟 **Microsoft Office 365**\n\n"
            "📌 حزمة أوفيس الأصلية كاملة مع مساحة تخزين سحابية.\n"
            "📦 **الكمية المتوفرة:** 8 مفاتيح تفعيل.",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif call.data == "prod_autodesk":
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("💳 الدفع وإتمام الطلب", callback_data="show_payments"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        )
        bot.send_message(
            chat_id,
            "🅰️ **AutoDesk Full Apps**\n\n"
            "📌 تفعيل برامج الهندسة والتصميم الرسمية (AutoCAD, 3ds Max...).",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif call.data == "prod_canva":
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("💳 الدفع وإتمام الطلب", callback_data="show_payments"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        )
        bot.send_message(
            chat_id,
            "🎨 **Canva Pro / Admin Account**\n\n"
            "📌 الاستفادة من قوالب وتصميمات كانفا برو الاحترافية.",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif call.data in ["show_payments", "pay_prompt"]:
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🏦 CCP Baridimob", callback_data="pay_ccp"),
            InlineKeyboardButton("🪙 Binance Pay", callback_data="pay_binance"),
            InlineKeyboardButton("💳 RedotPay ID", callback_data="pay_redotpay"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        )
        bot.send_message(
            chat_id,
            "💳 **اختر وسيلة الدفع المناسبة لك:**\nبعد الدفع، قم بإرسال إيصال الدفع هنا للمشرف لتفعيل طلبك.",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif call.data == "pay_ccp":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, f"🏦 **معلومات الدفع عبر Baridimob (CCP):**\n`{RIP_CPP}`\n\nأرسل وصل الدفع لتأكيد الطلب.", parse_mode="Markdown")
    elif call.data == "pay_binance":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, f"🪙 **معلومات الدفع عبر Binance Pay:**\nID: `{BINANCE_ID}`\n\nأرسل لقطة الشاشة للمشرف.", parse_mode="Markdown")
    elif call.data == "pay_redotpay":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, f"💳 **معلومات الدفع عبر RedotPay:**\nID: `{REDOTPAY_ID}`\n\nأرسل لقطة الشاشة للمشرف.", parse_mode="Markdown")

    elif call.data == "main_menu":
        bot.answer_callback_query(call.id)
        send_welcome(call.message)

# تشغيل خادم الويب والبوت معاً
if __name__ == '__main__':
    t = Thread(target=run_web)
    t.start()
    bot.infinity_polling()
