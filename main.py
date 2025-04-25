# ========== KEEP-BOT-ALIVE SERVER ==========
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "🟢 Minecraft Bot is ONLINE 24/7"

# Start web server in background
import threading
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

# ========== YOUR BOT CODE ==========
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
from tinydb import TinyDB, Query
import os

# Config
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_USERNAME = "@minecraft_updates"

# Database
db = TinyDB("apk_files.json")
apk_table = db.table("apks")
APK = Query()

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args:
        apk_id = args[0]
        result = apk_table.get(APK.apk_id == apk_id)
        if result:
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
        apk_id = str(len(apk_table) + 1)
        apk_table.insert({"apk_id": apk_id, "file_id": file_id})
        download_link = f"https://t.me/{context.bot.username}?start={apk_id}"
        await update.message.reply_text(f"✅ Link: {download_link}")
    else:
        await update.message.reply_text("❌ Only .apk files!")

async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE, apk_id: str):
    try:
        user_id = update.effective_user.id
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        result = apk_table.get(APK.apk_id == apk_id)

        if not result:
            await update.message.reply_text("⚠️ Link expired or invalid.")
            return

        if member.status in ["member", "administrator", "creator"]:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=result["file_id"],
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
