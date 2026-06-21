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
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler, 
                          filters, ContextTypes, ConversationHandler, CallbackQueryHandler)

# --- কনফিগারেশন ---
TOKEN = '8471658319:AAEBi2OJNw9PXVzIdtj0Kooo1vLdesRBvPY' 
PRIVATE_GROUP_ID = -1004408318864 

# কয়েনের রেটসমূহ
RATES = {
    "💰 NS Coin": {"rate": 0.00730, "info": "১ টা কয়েন: ০.০০৭৩০ টাকা\n১০০০ কয়েন: ৭.৩০ টাকা"},
    "💰 Old Top Coin": {"rate": 0.00312, "info": "১ টা কয়েন: ০.০০৩১২ টাকা\n১০০০ কয়েন: ৩.১২ টাকা"},
    "💰 Niva Coin": {"rate": 0.00275, "info": "১ টা কয়েন: ০.০০২৭৫ টাকা\n১০০০ কয়েন: ২.৭৫ টাকা"},
    "💰 New Top Coin": {"rate": 0.00330, "info": "১ টা কয়েন: ০.০০৩৩০ টাকা\n১০০০ কয়েন: ৩.৩০ টাকা"}
}

# --- ডাটাবেস ---
conn = sqlite3.connect('payments.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS history (amount REAL)''')
conn.commit()

def update_total_db(amount_bdt):
    cursor.execute("INSERT INTO history VALUES (?)", (amount_bdt,))
    conn.commit()

def get_total_db():
    cursor.execute("SELECT SUM(amount) FROM history")
    total = cursor.fetchone()[0]
    return total if total else 0.0

# --- বটের ধাপসমূহ ---
COIN_TYPE, COIN_AMOUNT, REDEEM_CODE_STEP, SCREENSHOT, BKASH_STEP = range(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"👋 স্বাগতম, {user.first_name}!\n\n"
        "💰 আমাদের প্ল্যাটফর্মে আপনাকে স্বাগতম। এখান থেকে আপনি খুব সহজেই আপনার কয়েন সেল করতে পারবেন।\n\n"
        "✅ **আমাদের বৈশিষ্ট্যসমূহ:**\n"
        "⭐ Market Highest Rate Guaranteed\n"
        "🔒 Fast Payment\n"
        "🛡 100% Secure Transaction\n\n"
        "নিচের মেনু থেকে আপনার পছন্দের অপশনটি বেছে নিন:"
    )
    menu_keyboard = [
        [KeyboardButton("💰 NS Coin"), KeyboardButton("💰 Old Top Coin")],
        [KeyboardButton("💰 Niva Coin"), KeyboardButton("💰 New Top Coin")],
        [KeyboardButton("📞 Support")]
    ]
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=ReplyKeyboardMarkup(menu_keyboard, resize_keyboard=True))
    return COIN_TYPE

async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "📞 Support":
        support_msg = (
            "👋 Welcome to NS Coin Buy\n"
            "💡 Earn smarter, not harder!\n\n"
            "💰 কয়েন Sell এর সবচেয়ে বিশ্বস্ত প্ল্যাটফর্ম।\n"
            "⭐ Market Highest Rate Guaranteed\n"
            "🔒 Fast Payment\n"
            "🛡 100% Secure Transaction\n\n"
            "📩 যোগাযোগ : @Arafat4466\n"
            "🔴 Update Channel : https://t.me/nscoinbuy"
        )
        await update.message.reply_text(support_msg, parse_mode='Markdown')
        return COIN_TYPE
    
    if text in RATES:
        context.user_data['coin_type'] = text
        await update.message.reply_text(f"আপনি {text} সিলেক্ট করেছেন।\nবর্তমান রেট:\n{RATES[text]['info']}\n\nকত কয়েন বিক্রি করতে চান সংখ্যায় লিখুন:")
        return COIN_AMOUNT
    return COIN_TYPE

async def step_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        coins = float(update.message.text)
    except ValueError:
        await update.message.reply_text("ভুল ইনপুট! অনুগ্রহ করে শুধুমাত্র সংখ্যা লিখুন।")
        return COIN_AMOUNT
        
    context.user_data['coins'] = coins
    coin_type = context.user_data['coin_type']
    context.user_data['bdt_amount'] = coins * RATES[coin_type]['rate']
    
    if coin_type == "💰 Niva Coin":
        context.user_data['niva_username'] = "Nk2007khalid2"
        await update.message.reply_text(f"✅ পরিমাণ গৃহীত হয়েছে। মোট টাকা: {context.user_data['bdt_amount']:.2f} BDT\n🆔 আমাদের Niva Username: `Nk2007khalid2`\n\nএখন কয়েন পাঠানোর পর একটি **স্ক্রিনশট** পাঠান:", parse_mode='Markdown')
        return SCREENSHOT
    
    elif coin_type == "💰 Old Top Coin":
        await update.message.reply_text("✅ পরিমাণ গৃহীত হয়েছে। এখন আপনার **রিডিম কোডটি** লিখুন:")
        return REDEEM_CODE_STEP
    
    info_map = {"💰 NS Coin": "ns_buyer_0", "💰 New Top Coin": "nivafamaly"}
    await update.message.reply_text(f"✅ পরিমাণ গৃহীত হয়েছে। মোট টাকা: {context.user_data['bdt_amount']:.2f} BDT\n🆔 User Name: `{info_map.get(coin_type)}`\n\nএখন কয়েন পাঠানোর পর একটি **স্ক্রিনশট** পাঠান:", parse_mode='Markdown')
    return SCREENSHOT

async def step_redeem_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['redeem_code'] = update.message.text
    await update.message.reply_text("✅ কোড গৃহীত। এখন কয়েন পাঠানোর পর একটি **স্ক্রিনশট** পাঠান:")
    return SCREENSHOT

async def step_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data['photo'] = update.message.photo[-1].file_id
        await update.message.reply_text("✅ স্ক্রিনশট পাওয়া গেছে। পেমেন্ট পাওয়ার জন্য আপনার **বিকাশ নাম্বার**টি লিখুন:")
        return BKASH_STEP
    else:
        await update.message.reply_text("অনুগ্রহ করে একটি ছবি (স্ক্রিনশট) পাঠান।")
        return SCREENSHOT

async def step_bkash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bkash = update.message.text
    user = update.effective_user
    
    # ইউজারনেম বা কোডের তথ্য সংগ্রহ
    niva_info = f"\n👤 Niva Username: `{context.user_data.get('niva_username', 'N/A')}`" if context.user_data.get('coin_type') == "💰 Niva Coin" else ""
    redeem_info = f"\n🎟 Redeem Code: `{context.user_data.get('redeem_code', 'N/A')}`" if context.user_data.get('coin_type') == "💰 Old Top Coin" else ""
    
    update_total_db(context.user_data['bdt_amount'])
    caption = (f"🔔 **নতুন রিকোয়েস্ট ({context.user_data['coin_type']})**\n{niva_info}{redeem_info}\n"
               f"👤 ইউজার: @{user.username}\n💰 কয়েন: {context.user_data['coins']}\n"
               f"💵 টাকার পরিমাণ: {context.user_data['bdt_amount']:.2f} BDT\n📱 বিকাশ নাম্বার: `{bkash}`\n\n"
               f"📈 **সর্বমোট:** {get_total_db():.2f} BDT")
    
    keyboard = [[InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}"), InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")]]
    await context.bot.send_photo(chat_id=PRIVATE_GROUP_ID, photo=context.user_data['photo'], caption=caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    await update.message.reply_text("✅ রিকোয়েস্ট সাবমিট হয়েছে। ধন্যবাদ!")
    context.user_data.clear()
    return ConversationHandler.END

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    action, user_id = query.data.split("_")
    status = "✔️ স্ট্যাটাস: অ্যাপ্রুভড" if action == "approve" else "✖️ স্ট্যাটাস: রিজেক্টেড"
    await context.bot.send_message(chat_id=int(user_id), text=f"আপনার রিকোয়েস্টটি {action} করা হয়েছে।")
    await query.edit_message_caption(caption=query.message.caption + f"\n\n{status}")
    await query.answer()

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            COIN_TYPE: [MessageHandler(filters.TEXT & (~filters.COMMAND), handle_choice)],
            COIN_AMOUNT: [MessageHandler(filters.TEXT & (~filters.COMMAND), step_coin)],
            REDEEM_CODE_STEP: [MessageHandler(filters.TEXT, step_redeem_code)],
            SCREENSHOT: [MessageHandler(filters.PHOTO | filters.TEXT, step_screenshot)],
            BKASH_STEP: [MessageHandler(filters.TEXT, step_bkash)],
        },
        fallbacks=[CommandHandler('start', start)]
    )
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(conv)
    app.run_polling()
