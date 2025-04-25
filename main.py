import sqlite3
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

# Config
BOT_TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 1254114367
CHANNEL_USERNAME = "@minecraft_updates"
DATABASE = "apk_links.db"  # SQLite database file

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# SQLite helper functions
def init_db():
    # Create table to store links if it doesn't exist
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS apk_links (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_id TEXT NOT NULL,
                        download_link TEXT NOT NULL)''')
    conn.commit()
    conn.close()

def save_apk_link(file_id, download_link):
    # Save new APK link into the database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO apk_links (file_id, download_link) VALUES (?, ?)", (file_id, download_link))
    conn.commit()
    conn.close()

def get_apk_link(apk_id):
    # Retrieve APK link from the database by APK ID
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT download_link FROM apk_links WHERE id=?", (apk_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# Your existing bot code
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args:
        apk_id = int(args[0])  # Get APK ID
        download_link = get_apk_link(apk_id)
        if download_link:
            await update.message.reply_text(f"✅ Here is your APK link: {download_link}")
        else:
            await update.message.reply_text("⚠️ Link expired! Ask admin for a new one.")
    else:
        await update.message.reply_text(
            "👋 Hi! I help download Minecraft APKs\nAsk admin for download links!"
        )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only!")
        return

    document = update.message.document
    if document.file_name.endswith('.apk'):
        file_id = document.file_id
        apk_id = int(get_next_apk_id())  # Get the next available APK ID
        download_link = f"https://t.me/{context.bot.username}?start={apk_id}"
        save_apk_link(file_id, download_link)
        await update.message.reply_text(f"✅ Link: {download_link}")
    else:
        await update.message.reply_text("❌ Only .apk files!")

def get_next_apk_id():
    # Get the next APK ID to assign
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(id) FROM apk_links")
    result = cursor.fetchone()
    conn.close()
    return result[0] + 1 if result[0] else 1

# Bot command to handle verification
async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE, apk_id: int):
    try:
        user_id = update.effective_user.id
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)

        if member.status in ["member", "administrator", "creator"]:
            # Send the APK file link
            download_link = get_apk_link(apk_id)
            if download_link:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"🎮 Your APK is ready! Download here: {download_link}"
                )
            else:
                await update.message.reply_text("❌ Link expired.")
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
    apk_id = int(query.data.split('_')[1])
    await check_membership(update, context, apk_id)

def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(CallbackQueryHandler(button_click))
    application.run_polling()

if __name__ == '__main__':
    init_db()  # Initialize the database on startup
    run_bot()
