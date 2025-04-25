# ========== KEEP-BOT-ALIVE SERVER ==========
from flask import Flask
import threading
app = Flask(__name__)

@app.route('/')
def home():
    return "🟢 Minecraft Bot is ONLINE 24/7"

threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

# ========== BOT WITH POSTGRES STORAGE ==========
import os, logging, psycopg2
from psycopg2.extras import RealDictCursor
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

# Load config from Railway env vars
BOT_TOKEN        = os.getenv("BOT_TOKEN")
ADMIN_ID         = int(os.getenv("ADMIN_ID"))
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")
DATABASE_URL     = os.getenv("DATABASE_URL")

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Connect to Postgres
conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
cur  = conn.cursor()
# Create table if not exists
cur.execute("""
CREATE TABLE IF NOT EXISTS apk_links (
  apk_id SERIAL PRIMARY KEY,
  file_id TEXT NOT NULL
)
""")
conn.commit()

def save_link(file_id: str) -> str:
    """Insert file_id into DB and return its apk_id."""
    cur.execute("INSERT INTO apk_links (file_id) VALUES (%s) RETURNING apk_id", (file_id,))
    row = cur.fetchone()
    conn.commit()
    return str(row['apk_id'])

def get_file_id(apk_id: str) -> str:
    """Fetch file_id by apk_id, or None."""
    cur.execute("SELECT file_id FROM apk_links WHERE apk_id = %s", (apk_id,))
    row = cur.fetchone()
    return row['file_id'] if row else None

# /start handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args:
        file_id = get_file_id(args[0])
        if file_id:
            return await send_if_joined(update, context, file_id)
        else:
            await update.message.reply_text("⚠️ Link expired! Ask admin for new one.")
    else:
        link = f"https://t.me/{context.bot.username}?start=1"
        await update.message.reply_text(f"👋 Hi! Click here to get APK:\n{link}")

# Admin upload handler
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Admin only!")
    doc = update.message.document
    if not doc.file_name.endswith('.apk'):
        return await update.message.reply_text("❌ Only .apk files!")
    apk_id = save_link(doc.file_id)
    download_link = f"https://t.me/{context.bot.username}?start={apk_id}"
    await update.message.reply_text(f"✅ Link: {download_link}")

# Membership + send
async def send_if_joined(update, context, file_id):
    user = update.effective_user.id
    member = await context.bot.get_chat_member(CHANNEL_USERNAME, user)
    if member.status in ("member","administrator","creator"):
        await context.bot.send_document(update.effective_chat.id, document=file_id, caption="🎮 Enjoy!")
    else:
        kb = [
            [InlineKeyboardButton("👉 JOIN", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
            [InlineKeyboardButton("✅ VERIFY", callback_data="verify")]
        ]
        await update.message.reply_text("🔒 Join first!", reply_markup=InlineKeyboardMarkup(kb))

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    # assume last used apk_id is in context (could store it per-user)
    # for brevity, reuse start logic:
    await start(update, context)

def main():
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app_bot.add_handler(CallbackQueryHandler(button_click))
    app_bot.run_polling()

if __name__ == "__main__":
    main()
