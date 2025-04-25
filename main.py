from flask import Flask
import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)

# ========== KEEP-BOT-ALIVE SERVER ==========
app = Flask(__name__)

@app.route('/')
def home():
    return "🟢 Minecraft Bot is ONLINE 24/7"

# Start web server in background
import threading
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

# ========== APK DATA STORAGE ==========
apk_file_path = "apk_data.json"

# Load existing data from file
if os.path.exists(apk_file_path):
    with open(apk_file_path, "r") as f:
        apk_files = json.load(f)
else:
    apk_files = {}

def save_apk_data():
    """Save apk files data to a JSON file."""
    with open(apk_file_path, "w") as f:
        json.dump(apk_files, f)

# ========== BOT CODE ==========
BOT_TOKEN = "7526718494:AAGlcmEOyLsPnB8AclKcsujJdnk5oDM5CZA"
ADMIN_ID = 1254114367
CHANNEL_USERNAME = "@minecraft_updates"

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only!")
        return

    document = update.message.document
    if document.file_name.endswith('.apk'):
        file_id = document.file_id
        apk_id = str(len(apk_files) + 1)
        apk_files[apk_id] = file_id
        download_link = f"https://t.me/{context.bot.username}?start={apk_id}"

        # Save data to the JSON file
        save_apk_data()

        await update.message.reply_text(f"✅ Link: {download_link}")
    else:
        await update.message.reply_text("❌ Only .apk files!")

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

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    apk_id = query.data.split('_')[1]
    await check_membership(update, context, apk_id)

def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(CallbackQueryHandler(button_click))
    application.run_polling()

if __name__ == '__main__':
    run_bot()
