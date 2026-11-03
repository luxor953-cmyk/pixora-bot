import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request

# === إعداداتك الخاصة ===
BOT_TOKEN = "9118344859:AAFqrcRY71z4f3fC87fs91c4z_wDQVHzyfo"
ADMIN_ID = 1004439571098
RIP_CPP = "0079999900229772775"
BINANCE_ID = "957483337"
REDOTPAY_ID = "1198898814"

RENDER_URL = "https://pixora-bot-egyp.onrender.com"
# ======================

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

try:
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{BOT_TOKEN}")
except Exception as e:
    print(f"Webhook setup error: {e}")

STOCK_DATABASE = {
    "capcut": [
        "CapCut_Key_1: user1@pixoras.com / pass123",
        "CapCut_Key_2: user2@pixoras.com / pass123",
        "CapCut_Key_3: user3@pixoras.com / pass123"
    ],
    "gemini": [
        "https://g.co/gemini/share/sample_link_1",
        "https://g.co/gemini/share/sample_link_2",
        "https://g.co/gemini/share/sample_link_3"
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

app = Flask('')

@app.route('/')
def home():
    return "Pixora Store Webhook is Active & Secure!"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def receive_update():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    markup = InlineKeyboardMarkup(row_width=2)
    
    capcut_count = len(STOCK_DATABASE["capcut"])
    gemini_count = len(STOCK_DATABASE["gemini"])
    office_count = len(STOCK_DATABASE["office"])
    autodesk_count = len(STOCK_DATABASE["autodesk"])
    canva_count = len(STOCK_DATABASE["canva"])
    
    btn_capcut = InlineKeyboardButton(f"🎬 CapCut · ({capcut_count})", callback_data="buy_capcut")
    btn_chatgpt = InlineKeyboardButton("🤖 ChatGPT · (15)", callback_data="prod_chatgpt")
    btn_gemini = InlineKeyboardButton(f"🔥 Gemini Ai · $3 ({gemini_count})", callback_data="buy_gemini")
    btn_office = InlineKeyboardButton(f"🪟 Microsoft 365 · ({office_count})", callback_data="buy_office")
    btn_autodesk = InlineKeyboardButton(f"🅰️ AUTODESK · ({autodesk_count})", callback_data="buy_autodesk")
    btn_canva = InlineKeyboardButton(f"🎨 Canva Pro · ({canva_count})", callback_data="buy_canva")
    
    markup.add(btn_capcut, btn_chatgpt, btn_gemini, btn_office, btn_autodesk, btn_canva)
    
    btn_bestseller = InlineKeyboardButton("🔥 (💚 BEST SELLER) ChatGPT Plus · (5)", callback_data="prod_chatgpt")
    markup.add(btn_bestseller)
    
    btn_pay = InlineKeyboardButton("💳 طرق الدفع (CCP / Binance / RedotPay)", callback_data="show_payments")
    markup.add(btn_pay)
    
    bot.send_message(
        message.chat.id, 
        "🌐 **Choose Your Product / اختر منتجك المفضّل:**\n"
        "مرحباً بك في متجر **Pixora Store** (النظام الآمن للمراجعة والتسليم):", 
        reply_markup=markup, 
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id

    products_map = {
        "buy_capcut": ("🎬 CapCut Pro", "capcut"),
        "buy_gemini": ("🌟 Gemini Pro", "gemini"),
        "buy_office": ("🪟 Microsoft 365", "office"),
        "buy_autodesk": ("🅰️ AUTODESK", "autodesk"),
        "buy_canva": ("🎨 Canva Pro", "canva")
    }

    if call.data in products_map:
        prod_name, prod_key = products_map[call.data]
        bot.answer_callback_query(call.id)
        stock_len = len(STOCK_DATABASE[prod_key])
        
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("💳 إظهار معلومات الدفع", callback_data="show_payments"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        )
        bot.send_message(
            chat_id,
            f"📦 **{prod_name}**\n\n"
            f"📊 **الكمية المتوفرة حالياً:** {stock_len}\n\n"
            "📌 **خطوات الشراء:**\n"
            "1️⃣ اضغط على زر (إظهار معلومات الدفع) وحول المبلغ.\n"
            "2️⃣ قم بـ **إرسال صورة إيصال الدفع (Screenshot)** هنا في المحادثة.\n"
            "3️⃣ سيقوم المشرف بمراجعة الوصل وإرسال بيانات حسابك فوراً!",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif call.data == "prod_chatgpt":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "🤖 قسم ChatGPT قيد التحديث، تواصل مع المشرف لتفعيل طلبك يدوياً.")

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
            "⚠️ **مهم جداً:** بعد إتمام التحويل، أرسل **صورة الإيصال** هنا في الشات ليتم تأكيدها وتسليمك المنتج!",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif call.data == "pay_ccp":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, f"🏦 **RIP Baridimob (CCP):**\n`{RIP_CPP}`\n\nأرسل صورة الوصل هنا بعد الدفع.", parse_mode="Markdown")
    elif call.data == "pay_binance":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, f"🪙 **Binance ID:** `{BINANCE_ID}`\n\nأرسل لقطة الشاشة هنا بعد الدفع.", parse_mode="Markdown")
    elif call.data == "pay_redotpay":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, f"💳 **RedotPay ID:** `{REDOTPAY_ID}`\n\nأرسل لقطة الشاشة هنا بعد الدفع.", parse_mode="Markdown")

    elif call.data == "main_menu":
        bot.answer_callback_query(call.id)
        send_welcome(call.message)

# معالجة استقبال أي محتوى مرسل (صور، ملفات، أو نصوص)
@bot.message_handler(content_types=['photo', 'document', 'text'])
def handle_incoming_messages(message):
    chat_id = message.chat.id
    user_name = message.from_user.first_name
    user_username = f"@{message.from_user.username}" if message.from_user.username else "لا يوجد معرف"

    # لو رسالة نصية عادية وليست صورة/ملف (وليست أمر start)
    if message.content_type == 'text':
        if message.text.startswith('/'):
            return
        if chat_id != ADMIN_ID:
            bot.send_message(chat_id, "📌 فضلاً، أرسل **صورة إيصال الدفع** كصورة أو ملف ليتم مراجعتها من قبل الإدارة.")
        return

    if chat_id == ADMIN_ID:
        bot.send_message(chat_id, "⚠️ هذه صورة مرسلة من حسابك كمدير، وليست إيصال عميل.")
        return

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✅ موافقة (CapCut)", callback_data=f"Approve_capcut_{chat_id}"),
        InlineKeyboardButton("✅ موافقة (Gemini)", callback_data=f"Approve_gemini_{chat_id}"),
        InlineKeyboardButton("✅ موافقة (Office)", callback_data=f"Approve_office_{chat_id}"),
        InlineKeyboardButton("✅ موافقة (Autodesk)", callback_data=f"Approve_autodesk_{chat_id}"),
        InlineKeyboardButton("✅ موافقة (Canva)", callback_data=f"Approve_canva_{chat_id}"),
        InlineKeyboardButton("❌ رفض الإيصال", callback_data=f"Reject_{chat_id}")
    )

    try:
        bot.forward_message(ADMIN_ID, chat_id, message.message_id)
        bot.send_message(
            ADMIN_ID,
            f"🔔 **إيصال دفع جديد قيد المراجعة!**\n"
            f"👤 العميل: {user_name} ({user_username})\n"
            f"🆔 ID: `{chat_id}`\n\n"
            "اختر المنتج المناسب للموافقة وإرسال الحساب للعميل تلقائياً:",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        bot.send_message(
            chat_id,
            "⏳ **تم استلام إيصال الدفع بنجاح!**\n"
            "جاري مراجعة التحويل من قبل الإدارة، سيتم إرسال تفاصيل طلبك فور التأكيد.",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error forwarding receipt to admin: {e}")
        bot.send_message(chat_id, "⚠️ حدث خطأ أثناء إرسال الإيصال للإدارة. يرجى المحاولة لاحقاً.")

@bot.callback_query_handler(func=lambda call: call.data.startswith(("Approve_", "Reject_")))
def admin_action(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "هذا الزر مخصص للمشرف فقط!")
        return

    bot.answer_callback_query(call.id)
    data_parts = call.data.split("_")
    action = data_parts[0]

    if action == "Reject":
        target_chat_id = data_parts[1]
        bot.send_message(target_chat_id, "❌ عذراً، تم رفض إيصال الدفع من قبل الإدارة أو أن البيانات غير صحيحة. يرجى التواصل معنا للتوضيح.")
        bot.edit_message_text("❌ تم رفض الإيصال وإبلاغ العميل.", call.message.chat.id, call.message.message_id)

    elif action == "Approve":
        prod_key = data_parts[1]
        target_chat_id = data_parts[2]

        if len(STOCK_DATABASE[prod_key]) > 0:
            item = STOCK_DATABASE[prod_key].pop(0)
            bot.send_message(
                target_chat_id,
                "🎉 **تم تأكيد الدفع بنجاح وتسليم طلبك!**\n\n"
                f"📦 **بيانات طلبك:**\n`{item}`\n\n"
                "شكراً لثقتك بمتجر **Pixora Store** 💚",
                parse_mode="Markdown"
            )
            bot.edit_message_text(
                f"✅ **تمت الموافقة بنجاح وتسليم المنتج تلقائياً:**\n`{item}`",
                call.message.chat.id,
                call.message.message_id
            )
        else:
            bot.send_message(ADMIN_ID, "⚠️ تنبيه: عذراً، نفدت كمية هذا المنتج من المخزون! يرجى إضافة مخزون جديد.")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
