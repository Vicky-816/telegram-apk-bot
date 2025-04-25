import os
from flask import Flask, request
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

# ——— Config from ENV ———
BOT_TOKEN        = os.getenv("BOT_TOKEN")
ADMIN_ID         = int(os.getenv("ADMIN_ID"))
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")
PORT             = int(os.getenv("PORT", 8080))
# Render exposes your service URL here:
RENDER_URL       = os.getenv("RENDER_EXTERNAL_URL")

# ——— Flask App for Webhooks ———
app = Flask(__name__)

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    """Receive updates from Telegram and push them into the app’s queue."""
    update = Update.de_json(request.get_json(force=True), bot)
    application.update_queue.put(update)
    return "OK"

@app.route("/")
def health_check():
    return "✅ Bot is running!"

# ——— Bot Logic ———
apk_files = {}

# /start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args and args[0] in apk_files:
        await check_membership(update, context, args[0])
    else:
        await update.message.reply_text(
            "👋 Hi! I help download Minecraft APKs.\n"
            "Ask admin for download links!"
        )

# Handle .apk Uploads from Admin
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Admin only!")
    doc = update.message.document
    if doc.file_name.endswith(".apk"):
        apk_id = str(len(apk_files) + 1)
        apk_files[apk_id] = doc.file_id
        link = f"https://{RENDER_URL}/{BOT_TOKEN}?start={apk_id}"
        await update.message.reply_text(f"✅ Download Link: {link}")
    else:
        await update.message.reply_text("❌ Only .apk files allowed.")

# Membership Check
async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE, apk_id: str):
    user = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user)
        if member.status in ("member","administrator","creator"):
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=apk_files[apk_id],
                caption="🎮 Here’s your APK!"
            )
        else:
            keyboard = [
                [InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
                [InlineKeyboardButton("Verify", callback_data=f"verify_{apk_id}")]
            ]
            await update.message.reply_text(
                "📢 Please join the channel first.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    except Exception:
        await update.message.reply_text("❌ Could not verify membership.")

# Button Callback
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    apk_id = update.callback_query.data.split("_",1)[1]
    await check_membership(update, context, apk_id)

# ——— Build Application ———
logging.basicConfig(level=logging.INFO)
application = Application.builder().token(BOT_TOKEN).build()
bot = application.bot  # for webhook handler

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
application.add_handler(CallbackQueryHandler(button_click))

if __name__ == "__main__":
    # Set Telegram Webhook to your Render URL
    webhook_url = f"https://{RENDER_URL}/{BOT_TOKEN}"
    bot.set_webhook(webhook_url)

    # Start Flask server to receive updates
    app.run(host="0.0.0.0", port=PORT)