from telegram import Update, Bot
from telegram.ext import ContextTypes
from telegram.error import Forbidden, BadRequest
import logging

# قائمة القنوات
CHANNELS = ["@HQLaptop", "@EnsBot"]
logger = logging.getLogger(__name__)

async def is_subscribed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """التحقق مما إذا كان المستخدم مشتركًا في القنوات المطلوبة."""
    user_id = update.message.from_user.id
    # Get the bot instance from the context
    bot = context.bot
    
    try:
        # التحقق من الاشتراك في القناة الأولى
        member1 = await bot.get_chat_member(chat_id=CHANNELS[0], user_id=user_id)
        if member1.status not in ['member', 'administrator', 'creator']:
            logger.warning(f"User {user_id} not in {CHANNELS[0]}")
            return False

        # التحقق من الاشتراك في القناة الثانية
        member2 = await bot.get_chat_member(chat_id=CHANNELS[1], user_id=user_id)
        if member2.status not in ['member', 'administrator', 'creator']:
            logger.warning(f"User {user_id} not in {CHANNELS[1]}")
            return False
            
    except BadRequest as e:
        if "user not found" in e.message.lower():
            logger.warning(f"User {user_id} not found in one of the channels (BadRequest).")
            return False
        else:
            logger.error(f"A BadRequest occurred for user {user_id}: {e}")
            await update.message.reply_text("An error occurred. Please try again later.")
            return False # أو يمكنك التعامل معها بطريقة أخرى
            
    except Exception as e:
        logger.error(f"An unexpected error occurred in is_subscribed for user {user_id}: {e}")
        await update.message.reply_text("An unexpected error occurred. Please contact support.")
        return False
        
    return True

async def notify_users(context: ContextTypes.DEFAULT_TYPE):
    """إرسال إشعارات للمستخدمين."""
    # Get db and bot from the context
    db = context.db
    bot = context.bot
    
    user_ids = db.get_all_user_ids()
    message = "🎉 **New Patch Release!** 🎉\n\nHello everyone! We're excited to announce a new update..."
    
    for user_id in user_ids:
        try:
            await bot.send_message(chat_id=user_id, text=message, parse_mode='Markdown')
        except Forbidden:
            logger.warning(f"User {user_id} has blocked the bot. Removing from the database.")
            db.remove_user(user_id)
        except Exception as e:
            logger.error(f"Failed to send message to user {user_id}: {e}") 
