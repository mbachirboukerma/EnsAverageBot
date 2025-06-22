import logging
import os
import asyncio
import threading
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from database import Database
from error_handler import notify_users, is_subscribed
from grade_calculator import (
    start,
    choose_specialization,
    choose_level,
    choose_sub_level,
    receive_first_grade,
    receive_second_grade,
    receive_tp_grade,
    receive_td_grade,
    receive_subject_average,
    cancel,
)
from specializations import *

# 1. إعداد اللوجر
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# 2. تعريف الثوابت
SPECIALIZATION, LEVEL, SUB_LEVEL, FIRST, SECOND, TP, TD, NEXT_SUBJECT = range(8)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7163691593:AAFmVnHxBgH4ORZ9ohTC9QQpiDmKjWTaMEI")
WEBHOOK_HOST = os.environ.get("WEBHOOK_HOST", "ens-average-bot-599688285140.europe-west1.run.app")
WEBHOOK_URL = f"https://{WEBHOOK_HOST}/{BOT_TOKEN}"

# 3. تهيئة قاعدة البيانات والبوت والتطبيق في النطاق العام
db = Database("bot_newdata.db")
application = Application.builder().token(BOT_TOKEN).build()
bot = application.bot  # الحصول على كائن البوت من التطبيق

# --- دوال الأوامر ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use /start to test this bot.")

async def visitor_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = db.get_visitor_count()
    await update.message.reply_text(f"The bot has been visited by {count + 600} unique users.")

async def overall_average_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = db.get_overall_average_count()
    await update.message.reply_text(f"The Bot has been used {count + 1530} times.")

async def show_user_ids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_ids = db.get_all_user_ids()
    await update.message.reply_text(f"Collected user IDs: {', '.join(map(str, user_ids))}")

async def whatsnew(update: Update, context: ContextTypes.DEFAULT_TYPE):
    MESSAGE_whatsnew = "..."  # أضف رسالتك هنا
    await update.message.reply_text(MESSAGE_whatsnew, parse_mode='HTML')


# 4. إعداد معالج المحادثة وجميع المعالجات الأخرى
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        SPECIALIZATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_specialization)],
        LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_level)],
        SUB_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_sub_level)],
        FIRST: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_first_grade)],
        SECOND: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_second_grade)],
        TP: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_tp_grade)],
        TD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_td_grade)],
        NEXT_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_subject_average)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
application.add_handler(conv_handler)
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("visitor_count", visitor_count))
application.add_handler(CommandHandler("usage_count", overall_average_count))
application.add_handler(CommandHandler("showUserIDs", show_user_ids))
application.add_handler(CommandHandler("whats_new", whatsnew))


# 5. تهيئة تطبيق Flask
app = Flask(__name__)

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    try:
        update = Update.de_json(await request.get_json(force=True), bot)
        await application.process_update(update)
        return "ok"
    except Exception as e:
        logger.error(f"Error in webhook: {e}")
        return "error", 500

@app.route("/")
def index():
    return "Bot is running!"

@app.route("/health")
def health():
    return "OK", 200


# 6. دالة الإعداد والتشغيل
async def setup():
    """إعداد وتشغيل البوت"""
    logger.info("Starting setup...")
    await application.initialize()
    if not await bot.set_webhook(url=WEBHOOK_URL):
        logger.error("Failed to set webhook")
    logger.info(f"Webhook set to {WEBHOOK_URL}")
    ADMIN_ID = 5909420341
    try:
        await bot.send_message(chat_id=ADMIN_ID, text="✅ Bot has started successfully on Cloud Run!")
    except Exception as e:
        logger.warning(f"Failed to send startup message: {e}")

    # تشغيل تطبيق Flask في thread منفصل
    flask_thread = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), use_reloader=False)
    )
    flask_thread.start()
    logger.info("Flask app started in a separate thread.")

    # إبقاء الـ application يعمل
    async with application:
        await application.start()


if __name__ == "__main__":
    asyncio.run(setup())

