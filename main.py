import logging
import os
import asyncio
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

# 1. إعداد اللوجر
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# 2. تعريف الثوابت
SPECIALIZATION, LEVEL, SUB_LEVEL, FIRST, SECOND, TP, TD, NEXT_SUBJECT = range(8)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7163691593:AAFmVnHxBgH4ORZ9ohTC9QQpiDmKjWTaMEI")
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_HOST = os.environ.get("WEBHOOK_HOST", "ens-average-bot-599688285140.europe-west1.run.app")
WEBHOOK_URL = f"https://{WEBHOOK_HOST}/{BOT_TOKEN}"

# 3. تهيئة قاعدة البيانات والتطبيق
db = Database("bot_newdata.db")
application = (
    Application.builder()
    .token(BOT_TOKEN)
    .read_timeout(30)
    .write_timeout(30)
    .webhook_url(WEBHOOK_URL)
    .build()
)
bot = application.bot

# --- دوال الأوامر ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📚 <b>Here are the instructions: 21032025</b>\n\n1. Click <b>/start</b> to begin using the bot.\n2. Follow the prompts to enter your grades.\n3. Make sure to enter valid grades between 0 and 20.\n4. Click <b>/cancel</b> if you want to stop the bot.\n5. To restart, first click <b>/cancel</b> then <b>/start</b>.", parse_mode='HTML')

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
    MESSAGE_whatsnew = "🎉 <b>New Patch Released!</b> 🎉\n\nHello everyone! We're excited to announce a new update..."
    await update.message.reply_text(MESSAGE_whatsnew, parse_mode='HTML')

# 4. إعداد معالجات الأوامر والمحادثة
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


# 5. دالة بدء التشغيل الرئيسية
async def main():
    logger.info("Setting webhook...")
    await bot.set_webhook(url=WEBHOOK_URL, allowed_updates=Update.ALL_TYPES)
    logger.info("Webhook is set.")
    
    # Send startup message
    ADMIN_ID = 5909420341
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=f"✅ Bot started successfully on port {PORT}")
    except Exception as e:
        logger.warning(f"Failed to send startup message: {e}")
    
    logger.info("Starting Uvicorn server...")
    # The uvicorn command will run this application object
    # No need to run flask or anything else here.

if __name__ == "__main__":
    asyncio.run(main())
    # Uvicorn will be started from the Dockerfile's CMD
    # e.g., uvicorn main:application --host 0.0.0.0 --port 8080

