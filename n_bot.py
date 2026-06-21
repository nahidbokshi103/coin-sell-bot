import os
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ওয়েব সার্ভারটি ব্যাকগ্রাউন্ডে চালু হবে
Thread(target=run_web).start()

# এরপর আপনার বটের বাকি কোড এখানে থাকবে
import sqlite3
import re
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler, 
                          filters, ContextTypes, ConversationHandler, CallbackQueryHandler)

# --- কনফিগারেশন ---
TOKEN = '8471658319:AAEBi2OJNw9PXVzIdtj0Kooo1vLdesRBvPY' 
PRIVATE_GROUP_ID = -1004408318864 
MY_NIVA_USERNAME = "nk2007khalid2" 

# কয়েনের রেটসমূহ
RATES = {
    "💰 NS Coin": {"rate": 0.00730, "info": "১ টা কয়েন: ০.০০৭৩০ টাকা\n১০০০ কয়েন: ৭.৩০ টাকা"},
    "💰 Old Top Coin": {"rate": 0.003, "info": "১ টা কয়েন: ০.০০৩ টাকা\n১০০০ কয়েন: ৩.০ টাকা"},
    "💰 Niva Coin": {"rate": 0.00275, "info": "১ টা কয়েন: ০.০০২৭৫ টাকা\n১০০০ কয়েন: ২.৭৫ টাকা"},
    "💰 New Top Coin": {"rate": 0.00330, "info": "১ টা কয়েন: ০.০০৩৩০ টাকা\n১০০০ কয়েন: ৩.৩০ টাকা"}
}

# --- ডাটাবেস ---
conn = sqlite3.connect('payments.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS history (amount REAL)''')
conn.commit()

# --- বটের ধাপসমূহ ---
COIN_TYPE, COIN_AMOUNT, NIVA_USER_STEP, REDEEM_CODE_STEP, SCREENSHOT, BKASH_STEP = range(6)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # স্টার্ট চাপলে পুরনো ডাটা মুছে ফেলা
    context.user_data.clear()
    user = update.effective_user
    welcome_text = (
        f"🌟 **স্বাগতম, {user.first_name}!** 🌟\n\n"
        "আমাদের প্ল্যাটফর্মে কয়েন সেল করার জন্য ধন্যবাদ। আমরা দিচ্ছি সবচেয়ে নির্ভরযোগ্য ও দ্রুত পেমেন্ট সুবিধা।\n\n"
        "💎 **আমাদের বৈশিষ্ট্যসমূহ:**\n"
        "✅ সর্বোচ্চ রেট গ্যারান্টি\n"
        "⚡ দ্রুততম পেমেন্ট\n"
        "🛡 ১০০% নিরাপদ লেনদেন\n\n"
        "নিচের মেনু থেকে আপনার পছন্দের অপশনটি বেছে নিন:"
    )
    menu_keyboard = [
        [KeyboardButton("💰 NS Coin"), KeyboardButton("💰 Old Top Coin")],
        [KeyboardButton("💰 Niva Coin"), KeyboardButton("💰 New Top Coin")],
        [KeyboardButton("📞 Support & Help")]
    ]
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=ReplyKeyboardMarkup(menu_keyboard, resize_keyboard=True))
    return COIN_TYPE

async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "📞 Support & Help":
        support_msg = (
            "🛠 **সাপোর্ট সেন্টার** 🛠\n\n"
            "যেকোনো প্রয়োজনে আমাদের সাথে যোগাযোগ করতে পারেন:\n\n"
            "👤 **অ্যাডমিন:** @Arafat4466\n"
            "📢 **আপডেট চ্যানেল:** [এখানে ক্লিক করুন](https://t.me/nscoinbuy)\n\n"
            "আমাদের সাথে থাকার জন্য ধন্যবাদ! ❤️"
        )
        await update.message.reply_text(support_msg, parse_mode='Markdown', disable_web_page_preview=True)
        return COIN_TYPE
    
    if text in RATES:
        context.user_data['coin_type'] = text
        await update.message.reply_text(f"আপনি {text} সিলেক্ট করেছেন।\n{RATES[text]['info']}\n\nকত কয়েন বিক্রি করতে চান সংখ্যায় লিখুন:")
        return COIN_AMOUNT
    return COIN_TYPE

async def step_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        coins = float(update.message.text)
    except ValueError:
        await update.message.reply_text("অনুগ্রহ করে একটি সঠিক সংখ্যা লিখুন।")
        return COIN_AMOUNT
    context.user_data['coins'] = coins
    coin_type = context.user_data['coin_type']
    context.user_data['bdt_amount'] = coins * RATES[coin_type]['rate']
    
    msg = (f"✅ কয়েন: {coins}\n💵 মোট টাকা: {context.user_data['bdt_amount']:.2f} BDT\n\n")

    if coin_type == "💰 Niva Coin":
        await update.message.reply_text(f"{msg}আপনার কয়েন আমাদের এই ঠিকানায় পাঠান: `{MY_NIVA_USERNAME}`\n\nএখন আপনার **Niva Coin ইউজারনেমটি** লিখুন:", parse_mode='Markdown')
        return NIVA_USER_STEP
    elif coin_type == "💰 Old Top Coin":
        await update.message.reply_text(f"{msg}এখন আপনার **রিডিম কোডটি** লিখুন (ফরম্যাট: 3xxx-9xxx-bxxx):", parse_mode='Markdown')
        return REDEEM_CODE_STEP
    else:
        info_map = {"💰 NS Coin": "ns_buyer_0", "💰 New Top Coin": "nivafamaly"}
        await update.message.reply_text(f"{msg}🆔 User Name: `{info_map.get(coin_type)}`\n\nএখন কয়েন পাঠানোর পর একটি **স্ক্রিনশট** পাঠান:", parse_mode='Markdown')
        return SCREENSHOT

async def step_niva_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['niva_username'] = update.message.text
    await update.message.reply_text("✅ ইউজারনেম গৃহীত। এখন কয়েন পাঠানোর পর একটি **স্ক্রিনশট** পাঠান:")
    return SCREENSHOT

async def step_redeem_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if not re.match(r"^[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}$", code):
        await update.message.reply_text("❌ ভুল কোড ফরম্যাট! অনুগ্রহ করে সঠিক ফরম্যাটে দিন (যেমন: 3xxx-9xxx-bxxx)।")
        return REDEEM_CODE_STEP
    context.user_data['redeem_code'] = code
    await update.message.reply_text("✅ কোড গৃহীত। এখন কয়েন পাঠানোর পর একটি **স্ক্রিনশট** পাঠান:")
    return SCREENSHOT

async def step_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data['photo'] = update.message.photo[-1].file_id
        await update.message.reply_text("✅ স্ক্রিনশট পাওয়া গেছে। পেমেন্ট পাওয়ার জন্য আপনার **বিকাশ নাম্বার (১১ ডিজিট)**টি লিখুন:")
        return BKASH_STEP
    else:
        await update.message.reply_text("অনুগ্রহ করে কয়েন পাঠানোর স্ক্রিনশটটি পাঠান।")
        return SCREENSHOT

async def step_bkash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bkash = update.message.text.strip()
    if not (bkash.isdigit() and len(bkash) == 11 and bkash.startswith("01")):
        await update.message.reply_text("❌ ভুল বিকাশ নাম্বার! সঠিক ১১ ডিজিটের নাম্বার দিন (যেমন: 017xxxxxxxx)।")
        return BKASH_STEP
    
    user = update.effective_user
    coin_type = context.user_data['coin_type']
    niva_info = f"\n👤 ইউজারের Niva Username: `{context.user_data.get('niva_username', 'N/A')}`" if coin_type == "💰 Niva Coin" else ""
    redeem_info = f"\n🎟 Redeem Code: `{context.user_data.get('redeem_code', 'N/A')}`" if coin_type == "💰 Old Top Coin" else ""
    
    cursor.execute("INSERT INTO history VALUES (?)", (context.user_data['bdt_amount'],))
    conn.commit()
    
    caption = (f"🔔 **নতুন রিকোয়েস্ট ({coin_type})**\n{niva_info}{redeem_info}\n"
               f"👤 ইউজার: @{user.username if user.username else user.first_name}\n💰 কয়েন: {context.user_data['coins']}\n"
               f"💵 পরিমাণ: {context.user_data['bdt_amount']:.2f} BDT\n📱 বিকাশ: `{bkash}`")
    
    keyboard = [[InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}"), InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")]]
    await context.bot.send_photo(chat_id=PRIVATE_GROUP_ID, photo=context.user_data['photo'], caption=caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    await update.message.reply_text("✅ রিকোয়েস্ট সাবমিট হয়েছে। ধন্যবাদ!")
    context.user_data.clear()
    return ConversationHandler.END

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    action, user_id = query.data.split("_")
    status = "✔️ অ্যাপ্রুভড" if action == "approve" else "✖️ রিজেক্টেড"
    await context.bot.send_message(chat_id=int(user_id), text=f"আপনার রিকোয়েস্টটি {status} করা হয়েছে।")
    await query.edit_message_caption(caption=query.message.caption + f"\n\n{status}")
    await query.answer()

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            COIN_TYPE: [MessageHandler(filters.TEXT & (~filters.COMMAND), handle_choice)],
            COIN_AMOUNT: [MessageHandler(filters.TEXT & (~filters.COMMAND), step_coin)],
            NIVA_USER_STEP: [MessageHandler(filters.TEXT, step_niva_user)],
            REDEEM_CODE_STEP: [MessageHandler(filters.TEXT, step_redeem_code)],
            SCREENSHOT: [MessageHandler(filters.PHOTO, step_screenshot)],
            BKASH_STEP: [MessageHandler(filters.TEXT, step_bkash)],
        },
        fallbacks=[CommandHandler('start', start)],
        allow_reentry=True # এটাই আসল সমাধান
    )
    
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(conv)
    app.run_polling()
