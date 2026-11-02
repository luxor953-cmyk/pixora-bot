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

# خادم ويب خفيف لإرضاء منصة Render ومنع خطأ الـ Port timeout
app = Flask('')

@app.route('/')
def home():
    return "Pixora Store Bot is Alive!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# دالة عرض القائمة الرئيسية والمنتجات الأساسية
@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    markup = InlineKeyboardMarkup(row_width=1)
    
    btn_gemini = InlineKeyboardButton("🌟 Google Pro (Gemini 18M)", callback_data="prod_gemini")
    btn_chatgpt = InlineKeyboardButton("🤖 ChatGPT (خيارات متعددة)", callback_data="prod_chatgpt")
    btn_capcut = InlineKeyboardButton("🎬 CapCut Pro", callback_data="prod_capcut")
    btn_office = InlineKeyboardButton("🪟 Microsoft Office 365", callback_data="prod_office")
    btn_autodesk = InlineKeyboardButton("🅰️ AutoDesk Full Apps", callback_data="prod_autodesk")
    btn_canva = InlineKeyboardButton("🎨 Canva Admin Account", callback_data="prod_canva")
    
    markup.add(btn_gemini, btn_chatgpt, btn_capcut, btn_office, btn_autodesk, btn_canva)
    
    btn_pay = InlineKeyboardButton("💳 طرق الدفع المعتمدة (CCP / Binance / RedotPay)", callback_data="show_payments")
    markup.add(btn_pay)
    
    bot.send_message(
        message.chat.id, 
        "مرحباً بك في **Pixora Store** 🌐\nاختر المنتج الذي تفضل شراءه لعرض الوصف والتفاصيل:", 
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
            InlineKeyboardButton("💳 شراء عبر CCP", callback_data="pay_ccp"),
            InlineKeyboardButton("🟡 شراء عبر Binance", callback_data="pay_binance"),
            InlineKeyboardButton("💳 شراء عبر RedotPay", callback_data="pay_redotpay"),
            InlineKeyboardButton("⬅️ العودة للقائمة", callback_data="main_menu")
        )
        bot.send_message(
            chat_id,
            "🌟 **Google Pro (Gemini 18 Months)**\n\n"
            "📌 **الوصف:** حساب رسمي مدعوم بالذكاء الاصطناعي الأقوى من جوجل لمدة 18 شهر كاملة.\n"
            "💰 **السعر:** مميز جداً.\n\n"
            "اختر وسيلة الدفع أدناه لإتمام الطلب وإرسال الإثبات:",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif call.data == "prod_chatgpt":
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("📚 ChatGPT تعليمي", callback_data="gpt_edu"),
            InlineKeyboardButton("👤 ChatGPT خاص", callback_data="gpt_private"),
            InlineKeyboardButton("👥 ChatGPT مشترك", callback_data="gpt_shared"),
            InlineKeyboardButton("⬅️ العودة للقائمة", callback_data="main_menu")
        )
        bot.send_message(
            chat_id,
            "🤖 **مشتريات ChatGPT**\n\n"
            "📌 **الوصف:** اختر نوع الحساب المناسب لك (تعليمي، خاص، أو مشترك) لتبدأ بالتحديد:",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif call.data in ["gpt_edu", "gpt_private", "gpt_shared"]:
        bot.answer_callback_query(call.id)
        type_name = "تعليمي" if call.data == "gpt_edu" else ("خاص" if call.data == "gpt_private" else "مشترك")
        markup = InlineKeyboardMarkup(row_width=3)
        markup.add(
            InlineKeyboardButton("1 شهر", callback_data="pay_prompt"),
            InlineKeyboardButton("2 شهر", callback_data="pay_prompt"),
            InlineKeyboardButton("3 أشهر", callback_data="pay_prompt"),
            InlineKeyboardButton("6 أشهر", callback_data="pay_prompt"),
            InlineKeyboardButton("12 شهر", callback_data="pay_prompt"),
            InlineKeyboardButton("⬅️ رجوع", callback_data="prod_chatgpt")
        )
        bot.send_message(
            chat_id,
            f"📅 لقد اخترت ChatGPT ({type_name}).\nالرجاء اختيار **عدد الشهور** المطلوبة:",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif call.data == "prod_capcut":
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("💳 الدفع وإتمام الطلب", callback_data="show_payments"),
            InlineKeyboardButton("⬅️ العودة للقائمة", callback_data="main_menu")
        )
        bot.send_message(
            chat_id,
            "🎬 **CapCut Pro**\n\n"
            "📌 **الوصف:** اشتراك رسمي لتفعيل كافة ميزات الذكاء الاصطناعي والتصدير المفتوح بدون قوالب مدفوعة.\n\n"
            "اختر طريقة الدفع للمتابعة:",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif call.data == "prod_office":
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("⏳ لمدة عام", callback_data="pay_prompt"),
            InlineKeyboardButton("♾️ مدى الحياة", callback_data="pay_prompt"),
            InlineKeyboardButton("⬅️ العودة للقائمة", callback_data="main_menu")
        )
        bot.send_message(
            chat_id,
            "🪟 **Microsoft Office 365**\n\n"
            "📌 **الوصف:** حزمة أوفيس الأصلية كاملة (Word, Excel, PowerPoint...) مع مساحة تخزين سحابية.\n"
            "اختر المدة المناسبة:",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif call.data == "prod_autodesk":
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("💳 الدفع وإتمام الطلب", callback_data="show_payments"),
            InlineKeyboardButton("⬅️ العودة للقائمة", callback_data="main_menu")
        )
        bot.send_message(
            chat_id,
            "🅰️ **AutoDesk Full Apps**\n\n"
            "📌 **الوصف:** تفعيل برامج الهندسة والتصميم الرسمية (AutoCAD, 3ds Max...) لحسابك الشخصي.\n\n"
            "اختر طريقة الدفع للمتابعة:",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif call.data == "prod_canva":
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("💳 الدفع وإتمام الطلب", callback_data="show_payments"),
            InlineKeyboardButton("⬅️ العودة للقائمة", callback_data="main_menu")
        )
        bot.send_message(
            chat_id,
            "🎨 **Canva Admin Account**\n\n"
            "📌 **الوصف:** صلاحيات إدارة فريق أو ترقية حسابك الشخصي للاستفادة من قوالب وتصميمات كانفا برو الاحترافية.\n\n"
            "اختر طريقة الدفع للمتابعة:",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif call.data in ["show_payments", "pay_prompt"]:
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🏦 CCP بريد الجزائر", callback_data="pay_ccp"),
            InlineKeyboardButton("🪙 Binance Pay", callback_data="pay_binance"),
            InlineKeyboardButton("💳 RedotPay ID", callback_data="pay_redotpay"),
            InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")
        )
        bot.send_message(
            chat_id,
            "💳 **اختر وسيلة الدفع المناسبة لك:**\nبعد الدفع، قم بإرسال إيصال الدفع هنا للمشرف لتفعيل طلبك فوراً.",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif call.data == "pay_ccp":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, f"🏦 **معلومات الدفع عبر بريد الجزائر (CCP):**\n`{RIP_CPP}`\n\nأرسل وصل الدفع للمشرف لتأكيد الطلب.", parse_mode="Markdown")
    elif call.data == "pay_binance":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, f"🪙 **معلومات الدفع عبر Binance Pay:**\nID: `{BINANCE_ID}`\n\nأرسل لقطة الشاشة للمشرف.", parse_mode="Markdown")
    elif call.data == "pay_redotpay":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, f"💳 **معلومات الدفع عبر RedotPay:**\nID: `{REDOTPAY_ID}`\n\nأرسل لقطة الشاشة للمشرف.", parse_mode="Markdown")

    elif call.data == "main_menu":
        bot.answer_callback_query(call.id)
        send_welcome(call.message)

# تشغيل خادم الويب في خلفية مستقلة ليتوافق مع Render
if __name__ == '__main__':
    t = Thread(target=run_web)
    t.start()
    bot.infinity_polling()
