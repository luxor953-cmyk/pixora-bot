import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request

# === الاعدادات ===
BOT_TOKEN = "9118344859:AAFqrcRY71z4f3fC87fs91c4z_wDQVHzyfo"
ADMIN_ID = 1004439571098
BINANCE_ID = "957483337"
REDOTPAY_ID = "1198898814"
RENDER_URL = "https://pixora-bot-egyp.onrender.com"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

try:
    bot.remove_webhook()
    bot.set_webhook(url=RENDER_URL + "/" + BOT_TOKEN)
except Exception as e:
    print("Webhook error:", e)

STOCK_DATABASE = {
    "capcut": ["CapCut_Key_1: user1@pixoras.com / pass123", "CapCut_Key_2: user2@pixoras.com / pass123"],
    "gemini": ["https://g.co/gemini/share/sample_link_1", "https://g.co/gemini/share/sample_link_2"],
    "office": ["Office365_Key_1: acc1@pixora.store / P@ss1", "Office365_Key_2: acc2@pixora.store / P@ss2"],
    "autodesk": ["Autodesk_Key_ABC123", "Autodesk_Key_XYZ789"],
    "canva": ["https://www.canva.com/brand/join?inv=sample_1", "https://www.canva.com/brand/join?inv=sample_2"]
}

app = Flask('')

@app.route('/')
def home():
    return "Pixora Store Bot is Live!"

@app.route('/' + BOT_TOKEN, methods=['POST'])
def receive_update():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    markup = InlineKeyboardMarkup(row_width=2)
    btn_capcut = InlineKeyboardButton("CapCut (" + str(len(STOCK_DATABASE["capcut"])) + ")", callback_data="buy_capcut")
    btn_chatgpt = InlineKeyboardButton("ChatGPT (15)", callback_data="prod_chatgpt")
    btn_gemini = InlineKeyboardButton("Gemini Ai (" + str(len(STOCK_DATABASE["gemini"])) + ")", callback_data="buy_gemini")
    btn_office = InlineKeyboardButton("Microsoft 365 (" + str(len(STOCK_DATABASE["office"])) + ")", callback_data="buy_office")
    btn_autodesk = InlineKeyboardButton("AUTODESK (" + str(len(STOCK_DATABASE["autodesk"])) + ")", callback_data="buy_autodesk")
    btn_canva = InlineKeyboardButton("Canva Pro (" + str(len(STOCK_DATABASE["canva"])) + ")", callback_data="buy_canva")
    markup.add(btn_capcut, btn_chatgpt, btn_gemini, btn_office, btn_autodesk, btn_canva)
    markup.add(InlineKeyboardButton("طرق الدفع (Binance / RedotPay)", callback_data="show_payments"))
    
    welcome_text = "مرحباً بك في متجر *Pixora Store* (الدفع الرقمي السريع).\nاختر منتجك المفضل من القائمة أدناه:"
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: not call.data.startswith(("Approve_", "Reject_")))
def handle_query(call):
    chat_id = call.message.chat.id
    products_map = {
        "buy_capcut": ("CapCut Pro", "capcut"),
        "buy_gemini": ("Gemini Pro", "gemini"),
        "buy_office": ("Microsoft 365", "office"),
        "buy_autodesk": ("AUTODESK", "autodesk"),
        "buy_canva": ("Canva Pro", "canva")
    }

    if call.data in products_map:
        prod_name, prod_key = products_map[call.data]
        bot.answer_callback_query(call.id)
        stock_len = len(STOCK_DATABASE[prod_key])
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("إظهار معلومات الدفع (Binance & RedotPay)", callback_data="show_payments"),
            InlineKeyboardButton("القائمة الرئيسية", callback_data="main_menu")
        )
        msg_text = "المنتج: *" + prod_name + "*\nالكمية المتوفرة: " + str(stock_len) + "\n\n1. اضغط على زر إظهار معلومات الدفع وحول المبلغ.\n2. أرسل صورة إيصال التحويل (Screenshot) هنا في المحادثة ليتم تسليمك المنتج فوراً."
        bot.send_message(chat_id, msg_text, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "prod_chatgpt":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "قسم ChatGPT قيد التحديث حالياً، تواصل مع المشرف لتفعيل طلبك.")

    elif call.data == "show_payments":
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("Binance Pay", callback_data="pay_binance"),
            InlineKeyboardButton("RedotPay ID", callback_data="pay_redotpay"),
            InlineKeyboardButton("القائمة الرئيسية", callback_data="main_menu")
        )
        pay_text = "طرق الدفع المتاحة في *Pixora Store*:\n\n*Binance Pay ID:*\n`" + BINANCE_ID + "`\n\n*RedotPay ID:*\n`" + REDOTPAY_ID + "`\n\nبعد التحويل، أرسل لقطة الشاشة هنا في المحادثة ليتم تسليمك المنتج فوراً!"
        bot.send_message(chat_id, pay_text, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "pay_binance":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "*Binance Pay ID:*\n`" + BINANCE_ID + "`\n\nأرسل لقطة الشاشة هنا بعد إتمام التحويل.", parse_mode="Markdown")

    elif call.data == "pay_redotpay":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "*RedotPay ID:*\n`" + REDOTPAY_ID + "`\n\nأرسل لقطة الشاشة هنا بعد إتمام التحويل.", parse_mode="Markdown")

    elif call.data == "main_menu":
        bot.answer_callback_query(call.id)
        send_welcome(call.message)

@bot.message_handler(content_types=['photo', 'document', 'text'])
def handle_incoming_messages(message):
    chat_id = message.chat.id
    user_name = message.from_user.first_name or "عميل"
    user_username = "@" + message.from_user.username if message.from_user.username else "بدون معرف"

    if message.content_type == 'text':
        if message.text.startswith('/'):
            return
        if str(chat_id) != str(ADMIN_ID):
            bot.send_message(chat_id, "فضلاً، أرسل *صورة إيصال الدفع* كصورة أو ملف ليتم مراجعتها وتسليمك الطلب.", parse_mode="Markdown")
        return

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("موافقة CapCut", callback_data="Approve_capcut_" + str(chat_id)),
        InlineKeyboardButton("موافقة Gemini", callback_data="Approve_gemini_" + str(chat_id)),
        InlineKeyboardButton("موافقة Office", callback_data="Approve_office_" + str(chat_id)),
        InlineKeyboardButton("موافقة Autodesk", callback_data="Approve_autodesk_" + str(chat_id)),
        InlineKeyboardButton("موافقة Canva", callback_data="Approve_canva_" + str(chat_id)),
        InlineKeyboardButton("رفض الإيصال", callback_data="Reject_" + str(chat_id))
    )

    try:
        # ملاحظة: إذا كان الـ ADMIN_ID لقناة أو مجموعة في تليجرام فغالباً يبدأ بـ -100
        bot.forward_message(ADMIN_ID, chat_id, message.message_id)
        admin_text = "إيصال دفع جديد قيد المراجعة!\nالعميل: " + user_name + " (" + user_username + ")\nID: `" + str(chat_id) + "`\n\nاختر المنتج للموافقة وإرسال الحساب للعميل تلقائياً:"
        bot.send_message(ADMIN_ID, admin_text, reply_markup=markup, parse_mode="Markdown")
        bot.send_message(chat_id, "تم استلام إيصال الدفع بنجاح! جاري المراجعة وسيتم إرسال تفاصيل طلبك فور التأكيد.")
    except Exception as e:
        print("Error forwarding to admin:", e)
        bot.send_message(chat_id, "تم استلام الصورة، ولكن تعذر إشعار المشرف تلقائياً. خطأ تقني: " + str(e))

@bot.callback_query_handler(func=lambda call: call.data.startswith(("Approve_", "Reject_")))
def admin_action(call):
    bot.answer_callback_query(call.id)
    data_parts = call.data.split("_")
    action = data_parts[0]

    if action == "Reject":
        target_chat_id = data_parts[1]
        bot.send_message(target_chat_id, "عذراً، تم رفض إيصال الدفع من قبل الإدارة. يرجى التأكد من التحويل والتواصل معنا.")
        bot.edit_message_text("تم رفض الإيصال وإبلاغ العميل.", call.message.chat.id, call.message.message_id)

    elif action == "Approve":
        prod_key = data_parts[1]
        target_chat_id = data_parts[2]

        if len(STOCK_DATABASE[prod_key]) > 0:
            item = STOCK_DATABASE[prod_key].pop(0)
            delivery_text = "تم تأكيد الدفع بنجاح وتسليم طلبك!\n\nبيانات الحساب:\n`" + item + "`\n\nشكراً لثقتك بمتجر *Pixora Store*"
            bot.send_message(target_chat_id, delivery_text, parse_mode="Markdown")
            bot.edit_message_text("تمت الموافقة وتسليم المنتج:\n" + item, call.message.chat.id, call.message.message_id)
        else:
            bot.send_message(call.message.chat.id, "تنبيه: نفدت كمية هذا المنتج من المخزون!")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
