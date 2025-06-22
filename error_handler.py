from telegram import Bot
from telegram.error import TimedOut, Forbidden, ChatMigrated
from retrying import retry
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from database import Database
import asyncio

# قائمة القنوات المطلوبة للاشتراك
CHANNELS = ["@infotouchcommunity", "@hqlaptop"]

#MESSAGE TO NOTIFY USERS
MESSAGE = (
    "<b>اللهم انصر أهل غزة</b> \n\n"
    "<b>﴿ إِن يَنصُرْكُمُ اللَّهُ فَلَا غَالِبَ لَكُمْ ﴾ [آل عمران: 160]<b>\n\n"
    "اللهم كن لإخواننا في غزة، اللهم احفظهم بحفظك، وانصرهم بنصرك، وكن لهم وليًّا ومعينًا.\n"
    "اللهم اجبر كسرهم، وداوِ جرحهم، وارحم شهداءهم، وطمئن قلوبهم، وكن معهم حيث لا معين إلا أنت.\n\n"
    "اللهم أرنا في عدوّهم يومًا أسودًا كيوم عاد وثمود.\n"
    "اللهم اشفِ صدور قومٍ مؤمنين.\n\n"
    "اللهم انصرهم نصرًا عزيزًا مؤزرًا عاجلًا غير آجل يا رب العالمين.\n\n"
    "وصلِّ اللهم وسلِّم وبارك على سيدنا محمد وعلى آله وصحبه أجمعين ﷺ."
)

async def send_message(chat_id: int, text: str, retries: int = 3):
    """إرسال رسالة مع إعادة المحاولة عند حدوث أخطاء"""
    from main import bot, db
    for attempt in range(retries):
        try:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')
            logging.info(f"✅ تم إرسال الرسالة إلى المستخدم {chat_id}")
            return  # تم الإرسال بنجاح، نخرج من الدالة

        except Forbidden:
            logging.warning(f"User {chat_id} blocked the bot. Removing from database.")
            db.remove_user_from_database(chat_id)
            return  # لا داعي لإعادة المحاولة

        except TimedOut:
            logging.warning(f"Timeout error while sending message to {chat_id}. Retrying...")
            await asyncio.sleep(2)  # انتظار ثم إعادة المحاولة

        except ChatMigrated as e:
            new_chat_id = e.new_chat_id
            logging.warning(f"Chat ID {chat_id} has migrated to {new_chat_id}. Updating database.")
            # db.update_chat_id(chat_id, new_chat_id)  # تحديث معرف الدردشة
            await send_message(new_chat_id, text)  # إعادة الإرسال للمعرف الجديد
            return

        except Exception as e:
            logging.error(f"Failed to send message to {chat_id} on attempt {attempt+1}: {e}")
            await asyncio.sleep(2)  # انتظار قبل إعادة المحاولة

    logging.error(f"Giving up on sending message to {chat_id} after {retries} retries.")

async def notify_users():
    """إرسال إشعارات لجميع المستخدمين"""
    from main import bot, db
    user_ids = db.get_all_user_ids()
    batch_size = 50

    for i in range(0, len(user_ids), batch_size):
        batch = user_ids[i:i+batch_size]
        logging.info(f"📤 إرسال دفعة المستخدمين من {i+1} إلى {i+len(batch)}")

        # استخدام asyncio.gather بدلاً من ThreadPoolExecutor
        tasks = [send_message(uid, MESSAGE) for uid in batch]
        await asyncio.gather(*tasks, return_exceptions=True)

        await asyncio.sleep(3)  # تأخير 3 ثواني بين كل دفعة

async def is_subscribed(update, context) -> bool:
    """التحقق من اشتراك المستخدم في القنوات المطلوبة"""
    user_id = update.message.from_user.id
    try:
        for channel in CHANNELS:
            chat_member = await context.bot.get_chat_member(channel, user_id)
            if chat_member.status not in ["member", "administrator", "creator"]:
                return False  # ❌ إذا لم يكن مشتركًا في إحدى القنوات، نعيد False
        return True  # ✅ المستخدم مشترك في جميع القنوات
    except Exception as e:
        logging.error(f"Error checking subscription: {e}")
        return False  # ❌ أي خطأ يتم اعتباره عدم اشتراك 
