import os
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import sqlite3

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
PORT = int(os.getenv("PORT", 8080))

app = Flask(__name__)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect("apklinks.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS links
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, file_id TEXT, file_name TEXT)''')
    conn.commit()
    conn.close()

init_db()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Send me an APK file to get a shareable link.")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document.mime_type.endswith("vnd.android.package-archive"):
        await update.message.reply_text("Please upload a valid APK file.")
        return

    file = await context.bot.get_file(document.file_id)
    file_id = document.file_id
    file_name = document.file_name

    # Save to DB
    conn = sqlite3.connect("apklinks.db")
    c = conn.cursor()
    c.execute("INSERT INTO links (file_id, file_name) VALUES (?, ?)", (file_id, file_name))
    conn.commit()
    conn.close()

    link = f"https://t.me/{context.bot.username}?start=apk_{file_id}"
    await update.message.reply_text(f"✅ File saved!\nHere is your shareable link:\n{link}")

async def handle_start_param(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args and context.args[0].startswith("apk_"):
        file_id = context.args[0].replace("apk_", "")

        conn = sqlite3.connect("apklinks.db")
        c = conn.cursor()
        c.execute("SELECT file_name FROM links WHERE file_id = ?", (file_id,))
        result = c.fetchone()
        conn.close()

        if result:
            await update.message.reply_document(file_id, filename=result[0])
        else:
            await update.message.reply_text("❌ This APK link is invalid or expired.")

def run_bot():
    app_bot = ApplicationBuilder().token(TOKEN).build()

    app_bot.add_handler(CommandHandler("start", handle_start_param))
    app_bot.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app_bot.add_handler(CommandHandler("help", start))

    app_bot.run_polling()

@app.route("/", methods=["GET", "POST"])
def index():
    return "Bot is Running!"

if __name__ == "__main__":
    run_bot()
