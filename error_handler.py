import logging
from telegram.error import TimedOut, Unauthorized, ChatMigrated, NetworkError
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
            except Unauthorized as e:
                logger.warning(f"Unauthorized error: {e}")
                raise BotError("User blocked the bot or token is invalid")
            except TimedOut as e:
                logger.warning(f"Timeout error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise BotError("Request timed out after multiple attempts")
            except ChatMigrated as e:
                logger.warning(f"Chat migrated from {e.old_chat_id} to {e.new_chat_id}")
                # Update chat ID in database and retry
                return func(*args, **kwargs)
            except NetworkError as e:
                logger.error(f"Network error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                raise BotError("Network error occurred")
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                raise BotError(f"An unexpected error occurred: {str(e)}")
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
