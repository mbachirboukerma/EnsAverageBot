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
    BasePersistence,
    PicklePersistence,
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
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7202093679:AAE_xjF5I1RvlWRAee8rWv2fB73zyFfYmFs")
WEBHOOK_HOST = os.environ.get("WEBHOOK_HOST", "ens-average-bot-599688285140.europe-west1.run.app")
WEBHOOK_URL = f"https://{WEBHOOK_HOST}/{BOT_TOKEN}"

# 3. Custom Context & Database
class CustomContext(ContextTypes.DEFAULT_TYPE):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = Database("bot_newdata.db")

context_types = ContextTypes(context=CustomContext)

# --- دوال الأوامر ---
async def help_command(update: Update, context: CustomContext):
    await update.message.reply_text("📚 <b>Here are the instructions:</b>\n\n1. Click <b>/start</b> to begin.\n2. Follow the prompts to enter your grades.\n3. Click <b>/cancel</b> to stop.", parse_mode='HTML')

async def visitor_count(update: Update, context: CustomContext):
    count = context.db.get_visitor_count()
    await update.message.reply_text(f"The bot has been visited by {count + 600} unique users.")

async def overall_average_count(update: Update, context: CustomContext):
    count = context.db.get_overall_average_count()
    await update.message.reply_text(f"The Bot has been used {count + 1530} times.")

async def show_user_ids(update: Update, context: CustomContext):
    user_ids = context.db.get_all_user_ids()
    await update.message.reply_text(f"Collected user IDs: {', '.join(map(str, user_ids))}")

async def whatsnew(update: Update, context: CustomContext):
    MESSAGE_whatsnew = "🎉 <b>New Patch Released!</b> 🎉\n\nHello everyone! We're excited to announce a new update..."
    await update.message.reply_text(MESSAGE_whatsnew, parse_mode='HTML')


async def on_startup(application: Application):
    """
    دالة يتم تشغيلها عند بدء تشغيل الخادم لإرسال رسالة تأكيد.
    """
    ADMIN_ID = 5909420341
    startup_message = "✅ Bot has started successfully on Cloud Run!"
    logger.info(f"Attempting to send startup message to admin {ADMIN_ID}")
    try:
        await application.bot.send_message(chat_id=ADMIN_ID, text=startup_message)
        logger.info("--- Startup message sent successfully ---")
    except Exception:
        logger.error("!!! An error occurred on startup sending message !!!", exc_info=True)


# 4. بناء التطبيق
application = (
    Application.builder()
    .token(BOT_TOKEN)
    .context_types(context_types)
    .build()
)

# 5. إضافة معالجات الأوامر والمحادثة
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
    persistent=True,
    name="grade_calculator_conv"
)
application.add_handler(conv_handler)
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("visitor_count", visitor_count))
application.add_handler(CommandHandler("usage_count", overall_average_count))
application.add_handler(CommandHandler("showUserIDs", show_user_ids))
application.add_handler(CommandHandler("whats_new", whatsnew))

# The `application` object is what uvicorn will run.
# No `if __name__ == "__main__"` needed.
# The database and bot objects are now accessed via the context.

if __name__ == "__main__":
    # --- التشغيل باستخدام Webhook ---
    logger.info("--- Starting bot with webhook ---")
    port = int(os.environ.get("PORT", 8080))
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=BOT_TOKEN,
        webhook_url=WEBHOOK_URL,
        on_startup=on_startup,
        allowed_updates=Update.ALL_TYPES,
    )

