import logging
import os
import json
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)
from flask import Flask
import threading

# ========== KEEP-BOT-ALIVE SERVER ==========
app = Flask(__name__)

@app.route('/')
def home():
    return "🟢 Minecraft Bot is ONLINE 24/7"

# Start web server in background
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

# ========== YOUR BOT CODE ==========

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Config
BOT_TOKEN = "7526718494:AAElsuWjGQIGnuiYOaOA34_fYuVPh92ucwU"
ADMIN_ID = 1254114367
CHANNEL_USERNAME = "@minecraft_updates"

# GitHub repository details
repo_owner = 'Vicky-816'
repo_name = 'telegram-apk-bot'
file_path = 'data.json'

# Initialize apk_files from data.json or an empty dictionary
try:
    with open("data.json", "r") as file:
        apk_files = json.load(file)
except (FileNotFoundError, json.JSONDecodeError):
    apk_files = {}

# Function to push the updated data to GitHub
def push_to_github():
    subprocess.run(['python', 'push_to_github.py'])

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args:
        apk_id = args[0]
        if apk_id in apk_files:
            await check_membership(update, context, apk_id)
        else:
            await update.message.reply_text("⚠️ Link expired! Ask admin for new one.")
    else:
        await update.message.reply_text(
            "👋 Hi! I help download Minecraft APKs\n"
            "Ask admin for download links!"
        )

# Upload .apk by admin
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only!")
        return

    document = update.message.document
    if document.file_name.endswith('.apk'):
        file_id = document.file_id
        apk_id = str(len(apk_files) + 1)
        apk_files[apk_id] = file_id

        # Save updated apk_files to data.json
        with open("data.json", "w") as file:
            json.dump(apk_files, file, indent=2)

        # Push changes to GitHub
        push_to_github()

        download_link = f"https://t.me/{context.bot.username}?start={apk_id}"
        await update.message.reply_text(f"✅ Link: {download_link}")
    else:
        await update.message.reply_text("❌ Only .apk files!")

# Membership check
async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE, apk_id: str):
    try:
        user_id = update.effective_user.id
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)

        if member.status in ["member", "administrator", "creator"]:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=apk_files[apk_id],
                caption="🎮 Your APK is ready! Enjoy!"
            )
        else:
            keyboard = [
                [InlineKeyboardButton("👉 JOIN CHANNEL", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
                [InlineKeyboardButton("✅ VERIFY JOIN", callback_data=f"verify_{apk_id}")]
            ]
            await update.message.reply_text(
                "📢 Join channel first!\n1. Join\n2. Verify",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ Verification failed")

# Button handling
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    apk_id = query.data.split('_')[1]
    await check_membership(update, context, apk_id)

# Run bot
def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(CallbackQueryHandler(button_click))
    application.run_polling()

# Run everything
if __name__ == '__main__':
    run_bot()
