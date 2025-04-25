# ========== KEEP-BOT-ALIVE SERVER ==========
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "🟢 Minecraft Bot is ONLINE 24/7"

# Run Flask in its own thread so polling doesn’t block it
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()  # :contentReference[oaicite:0]{index=0}

# ========== YOUR BOT CODE ==========
import logging
import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)

# ——— Bot Configuration ———
BOT_TOKEN        = "7526718494:AAElsuWjGQIGnuiYOaOA34_fYuVPh92ucwU"
ADMIN_ID         = 1254114367
CHANNEL_USERNAME = "@minecraft_updates"
DATA_FILE        = "data.json"

# ——— Load saved APK links ———
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        apk_files = json.load(f)
else:
    apk_files = {}

def save_apks():
    with open(DATA_FILE, "w") as f:
        json.dump(apk_files, f)

# ——— Logging Setup ———
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ——— /start Command ———
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args and args[0] in apk_files:
        await check_membership(update, context, args[0])
    else:
        await update.message.reply_text(
            "👋 Hi! I help download Minecraft APKs.\n"
            "Ask admin for download links!"
        )

# ——— Handle Admin .apk Upload ———
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Admin only!")
    doc = update.message.document
    if doc.file_name.endswith(".apk"):
        apk_id = str(len(apk_files) + 1)
        apk_files[apk_id] = doc.file_id
        save_apks()
        link = f"https://t.me/{context.bot.username}?start={apk_id}"
        await update.message.reply_text(f"✅ Link: {link}")
    else:
        await update.message.reply_text("❌ Only .apk files allowed.")

# ——— Membership Check & Send APK ———
async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE, apk_id: str):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, update.effective_user.id)
        if member.status in ("member","administrator","creator"):
            await update.message.reply_document(
                chat_id=update.effective_chat.id,
                document=apk_files[apk_id],
                caption="🎮 Your APK is ready! Enjoy!"
            )
        else:
            buttons = [
                [InlineKeyboardButton("👉 JOIN CHANNEL", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
                [InlineKeyboardButton("✅ VERIFY", callback_data=f"verify_{apk_id}")]
            ]
            await update.message.reply_text(
                "📢 Join channel first!\n1. Join 2. Verify",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    except Exception as e:
        logger.error(f"Membership check failed: {e}")
        await update.message.reply_text("❌ Could not verify membership.")

# ——— Handle “Verify” Button ———
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    apk_id = update.callback_query.data.split("_",1)[1]
    await check_membership(update, context, apk_id)

# ——— Run Bot with Polling ———
def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()  # :contentReference[oaicite:1]{index=1}
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(CallbackQueryHandler(button_click))
    application.run_polling()  # :contentReference[oaicite:2]{index=2}

if __name__ == "__main__":
    run_bot()