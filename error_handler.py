import logging
#from telegram.error import TimedOut, Unauthorized, ChatMigrated, NetworkError  # حذف الاستيراد القديم
from functools import wraps
import time

logger = logging.getLogger(__name__)

class BotError(Exception):
    """Custom exception for bot errors"""
    pass

def handle_telegram_errors(func):
    """Decorator to handle Telegram API errors"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise BotError(f"An error occurred: {str(e)}")
        return None
    return wrapper

def safe_send_message(bot, chat_id, text, **kwargs):
    """Safely send message with error handling"""
    @handle_telegram_errors
    def _send():
        return bot.send_message(chat_id=chat_id, text=text, **kwargs)
    
    try:
        return _send()
    except BotError as e:
        logger.error(f"Failed to send message to {chat_id}: {e}")
        return None 
