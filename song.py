import logging
import os
import threading
import asyncio
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)

# --- 1. THE WEB HEARTBEAT (Fixes Render Port Errors) ---
server = Flask(__name__)

@server.route('/')
def home():
    return "UMC Blessed Bot is Online 24/7"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    server.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# --- 2. CONFIGURATION ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = "8651749292:AAE669h-KhqRLqVuHaoWiRo2zRRmza0W95c" 
ADMIN_ID = 998942116 
ADMIN_USERNAME = "@Haffa_advert"
DEVELOPER_USERNAME = "@pselms" 

NAME, PHONE, EMAIL, PHOTO, CHOIR_PART, PAY_TYPE, SCREENSHOT = range(7)

# --- 3. BOT LOGIC ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🙏 **Grace and Peace to you!**\n\nWelcome to UMC Choir Registration.\nWhat is your **Full Name**?",
        parse_mode="Markdown"
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text(f"Thank you. Now, your **Phone Number**?")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("Enter your **Email Address**:")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['email'] = update.message.text
    await update.message.reply_text("📸 Send a **Profile Photo** or /skip:")
    return PHOTO

async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['profile_pic'] = update.message.photo[-1].file_id if update.message.photo else None
    reply_keyboard = [['Member', 'Participant', 'other']]
    await update.message.reply_text(
        "Which type are you?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOIR_PART

async def get_choir_part(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['type'] = update.message.text
    pay_keyboard = [['Student (25)', 'Uni Student (50)'], ['Worker (100)', 'Yearly (300)']]
    await update.message.reply_text(
        "💳 **Select Payment Type:**",
        reply_markup=ReplyKeyboardMarkup(pay_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return PAY_TYPE

async def get_pay_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['pay_choice'] = update.message.text
    await update.message.reply_text(
        "🏦 **CBE:** `1000021359778`\nSend the **Screenshot** of the receipt now.",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return SCREENSHOT

async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ Please send a photo of the receipt.")
        return SCREENSHOT

    receipt_photo = update.message.photo[-1].file_id
    user_info = context.user_data
    report = f"🚨 **NEW REGISTRATION**\n👤 {user_info.get('name')}\n📞 {user_info.get('phone')}\n💰 {user_info.get('pay_choice')}"

    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=report)
        if user_info.get('profile_pic'):
            await context.bot.send_photo(chat_id=ADMIN_ID, photo=user_info['profile_pic'], caption="Profile")
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=receipt_photo, caption="Receipt")
        
        await update.message.reply_text(
            "✅ **Registration Successful!**\n\n"
            f"🆘 Support: {ADMIN_USERNAME}\n💻 :Support Developer {DEVELOPER_USERNAME}",
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Error: {e}")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# --- 4. THE CLEAN LAUNCHER ---
def main():
    # 1. Start Web Server
    threading.Thread(target=run_flask, daemon=True).start()

    # 2. Setup Application
    application = Application.builder().token(TOKEN).build()

    # 3. Add Handlers
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            PHOTO: [MessageHandler(filters.PHOTO | filters.TEXT, get_photo), CommandHandler('skip', get_photo)],
            CHOIR_PART: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_choir_part)],
            PAY_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pay_type)],
            SCREENSHOT: [MessageHandler(filters.PHOTO, get_screenshot)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    application.add_handler(conv_handler)

    # 4. START POLLING WITH AUTO-CLEAN
    print("Launching Bot... (Cleaning old connections)")
    # drop_pending_updates=True is the key to preventing "Conflict" errors
    application.run_polling(drop_pending_updates=True, close_loop=False)

if __name__ == '__main__':
    main()
