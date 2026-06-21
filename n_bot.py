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
COIN_TYPE, COIN_AMOUNT, REDEEM_CODE_STEP, USER_ACCOUNT_STEP, SCREENSHOT, BKASH_STEP = range(6)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"👋 স্বাগতম, {user.first_name}!\n\n"
        "💰 আমাদের প্ল্যাটফর্মে আপনাকে স্বাগতম। এখান থেকে আপনি খুব সহজেই আপনার কয়েন সেল করতে পারবেন।"
    )
    menu_keyboard = [
        [KeyboardButton("💰 NS Coin"), KeyboardButton("💰 Old Top Coin")],
        [KeyboardButton("💰 Niva Coin"), KeyboardButton("💰 New Top Coin")],
        [KeyboardButton("📞 Support")]
    ]
    await update.message.reply_text(welcome_text, reply_markup=ReplyKeyboardMarkup(menu_keyboard, resize_keyboard=True))
    return COIN_TYPE

async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "📞 Support":
        await update.message.reply_text("📩 যোগাযোগ : @Arafat4466")
        return COIN_TYPE
    
    if text in RATES:
        context.user_data['coin_type'] = text
        await update.message.reply_text(f"আপনি {text} সিলেক্ট করেছেন। কত কয়েন বিক্রি করতে চান সংখ্যায় লিখুন:")
        return COIN_AMOUNT
    return COIN_TYPE

async def step_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        coins = float(update.message.text)
        context.user_data['coins'] = coins
        context.user_data['bdt_amount'] = coins * RATES[context.user_data['coin_type']]['rate']
    except ValueError:
        await update.message.reply_text("অনুগ্রহ করে সঠিক সংখ্যা লিখুন।")
        return COIN_AMOUNT
        
    # সব কয়েনের জন্যই এখন ইউজারের একাউন্ট নেম চাওয়া হবে
    await update.message.reply_text("✅ পরিমাণ গৃহীত হয়েছে। আপনার কয়েন পাঠানোর একাউন্টের **ইউজারনেম (User Name)** টি লিখুন:")
    return USER_ACCOUNT_STEP

async def step_user_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['sender_username'] = update.message.text
    coin_type = context.user_data['coin_type']
    
    if coin_type == "💰 Niva Coin":
        await update.message.reply_text(f"✅ গৃহীত। আমাদের Niva Username: `Nk2007khalid2`\n\nএখন কয়েন পাঠানোর পর একটি **স্ক্রিনশট** পাঠান:", parse_mode='Markdown')
    elif coin_type == "💰 Old Top Coin":
        await update.message.reply_text("✅ গৃহীত। আপনার **রিডিম কোডটি** লিখুন:")
        return REDEEM_CODE_STEP
    else:
        info_map = {"💰 NS Coin": "ns_buyer_0", "💰 New Top Coin": "nivafamaly"}
        await update.message.reply_text(f"✅ গৃহীত। আমাদের ইউজারনেম: `{info_map.get(coin_type)}`\n\nএখন কয়েন পাঠানোর পর একটি **স্ক্রিনশট** পাঠান:", parse_mode='Markdown')
    
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
    await update.message.reply_text("অনুগ্রহ করে একটি ছবি পাঠান।")
    return SCREENSHOT

async def step_bkash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bkash = update.message.text
    user = update.effective_user
    
    # সংগৃহীত সব তথ্য দিয়ে ক্যাপশন তৈরি
    caption = (f"🔔 **নতুন রিকোয়েস্ট ({context.user_data['coin_type']})**\n"
               f"👤 ইউজারের কয়েন পাঠানোর একাউন্ট: `{context.user_data['sender_username']}`\n"
               f"👤 টেলিগ্রাম ইউজার: @{user.username}\n"
               f"💰 কয়েন: {context.user_data['coins']}\n"
               f"💵 টাকার পরিমাণ: {context.user_data['bdt_amount']:.2f} BDT\n"
               f"📱 বিকাশ নাম্বার: `{bkash}`")
    
    keyboard = [[InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}"), InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")]]
    await context.bot.send_photo(chat_id=PRIVATE_GROUP_ID, photo=context.user_data['photo'], caption=caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    await update.message.reply_text("✅ রিকোয়েস্ট সাবমিট হয়েছে। ধন্যবাদ!")
    context.user_data.clear()
    return ConversationHandler.END

# ... বাকি হ্যান্ডলার এবং মেইন ফাংশন একই থাকবে ...
