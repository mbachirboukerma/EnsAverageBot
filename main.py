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
WEBHOOK_HOST = os.environ.get("WEBHOOK_HOST", "ens-average-bot-599688285140.europe-west1.run.app")
WEBHOOK_URL = f"https://{WEBHOOK_HOST}/{BOT_TOKEN}"

# 3. تهيئة قاعدة البيانات
db = Database("bot_newdata.db")


# --- دوال الأوامر ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📚 <b>Here are the instructions:</b>\n\n1. Click <b>/start</b> to begin.\n2. Follow the prompts to enter your grades.\n3. Click <b>/cancel</b> to stop.", parse_mode='HTML')

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


async def post_init(application: Application) -> None:
    """
    دالة يتم تشغيلها بعد تهيئة التطبيق وقبل بدء تشغيل الخادم.
    تستخدم لضبط الـ webhook وإرسال رسالة بدء التشغيل.
    """
    logger.info("Setting webhook...")
    await application.bot.set_webhook(url=WEBHOOK_URL, allowed_updates=Update.ALL_TYPES)
    logger.info("Webhook is set.")
    
    # Send startup message
    ADMIN_ID = 5909420341
    try:
        await application.bot.send_message(chat_id=ADMIN_ID, text=f"✅ Bot started successfully (post_init model).")
    except Exception as e:
        logger.warning(f"Failed to send startup message: {e}")

# 4. بناء التطبيق وتمرير دالة الإعداد
application = (
    Application.builder()
    .token(BOT_TOKEN)
    .post_init(post_init)
    .build()
)

# 5. هذا المتغير مطلوب للملفات الأخرى التي تقوم باستيراده
bot = application.bot

# 6. إضافة معالجات الأوامر والمحادثة
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

# الكائن `application` هو ما سيقوم `uvicorn` بتشغيله.
# لا حاجة لوجود `if __name__ == "__main__"`.

