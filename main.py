import logging
import os
import threading
import time
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from database import Database
from error_handler import send_message, notify_users, is_subscribed
from grade_calculator import (
    start, choose_specialization, choose_level, choose_sub_level, ask_for_grades,
    receive_first_grade, receive_second_grade, receive_tp_grade, receive_td_grade,
    calculate_subject_average, receive_subject_average, cancel, validate_grade, get_menu_keyboard
)
from specializations import *

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

SPECIALIZATION, LEVEL, SUB_LEVEL, FIRST, SECOND, TP, TD, NEXT_SUBJECT = range(8)

# إعداد قاعدة البيانات
DB_PATH = "bot_newdata.db"
db = Database(DB_PATH)

# رسائل what's new
MESSAGE_whatsnew = (
    "🎉 <b>New Patch Released!</b> 🎉\n\n"
    "Hello everyone! We're excited to announce a new update to the Grade Calculator Bot. Here's what's new:\n\n"
    "1. <b>We have added new levels</b>:Physics3 (+4), Science3 (+4) , science3 (+5), Math - Fourth Year (+5) and Sciences - Second Year.\n"
    "2. <b>Visitor Count</b>: You can now see how many unique users have visited the bot with the command /visitor_count.\n"
    "3. <b>Usage Count</b>: You can now see how many times the Bot has been used with the command /usage_count.\n\n"
    "4. <b>Bug Fixes</b>: We've fixed several bugs to improve the overall user experience.\n"
    "5. <b>Improved Help</b>: Need assistance? Just type /help for detailed instructions.\n"
    "6. <b>Enhanced Validations</b>: Better input validation to ensure accurate grade calculations.\n\n"
    "Update Date: <b>19 June 2024</b>\n\n"
    "Thank you for using our bot! If you have any questions or need further assistance, feel free to reach out.\n\n"
    "Happy calculating! 📊"
)

MESSAGE_AR_whatsnew = (
    "🎉 <b>تحديث جديد تم إصداره!</b> 🎉\n\n"
    "مرحبًا بالجميع! نحن متحمسون للإعلان عن تحديث جديد لبوت حساب المعدل بالنسبة لجميع التخصصات بالمدرسة العليا للأساتذة _ القبة. إليكم ما هو جديد:\n\n"
    "1. <b>مستويات جديدة</b>: لقد أضفنا المستويات: فيزياء - السنة الثالثة (+4)، علوم - السنة الثالثة (+4)، علوم - السنة الثالثة (+5)، الرياضيات - السنة الرابعة (+5) وعلوم - السنة الثانية.\n"
    "2. <b>عدد الزوار</b>: يمكنك الآن رؤية عدد المستخدمين الذين زاروا الروبوت باستخدام الأمر /visitor_count.\n"
    "3. <b>عدد مرات الاستخدام</b>: يمكنك الآن معرفة عدد المرات التي تم فيها استعمال البوت باستخدام الأمر /usage_count.\n\n"
    "4. <b>تصحيح بعض الأخطاء</b>: لقد قمنا بتصحيح العديد من الأخطاء لتحسين تجربة المستخدم العامة.\n"
    "5. <b>تحسين المساعدة</b>: تحتاج إلى مساعدة؟ فقط اكتب /help للحصول على تعليمات مفصلة.\n"
    "6. <b>تحسين التحقق من المدخلات</b>: تحقق أفضل من العلامات لضمان حساب دقيق للمعدلات.\n\n"
    "تاريخ التحديث: <b>19 يونيو 2024</b>\n\n"
    "شكرًا لاستخدامك البوت الخاص بنا! إذا كانت لديك أي أسئلة أو إستفسارات، يرجى التواصل معنا، نحن في الخدمة دائما.\n\n"
    "تجربة ممتعة! 😊"
)

# دوال مساعدة بسيطة

def help_command(update, context):
    update.message.reply_text(
        "📚 <b>Here are the instructions: 21032025</b>\n\n"
        "1. Click <b>/start</b> to begin using the bot.\n"
        "2. Follow the prompts to enter your grades.\n"
        "3. Make sure to enter valid grades between 0 and 20.\n"
        "4. Click <b>/cancel</b> if you want to stop the bot.\n"
        "5. To restart, first click <b>/cancel</b> then <b>/start</b>.\n"
        "If you need further assistance, just text @yassineboukerma\n\n\n"
        "📚 <b>إليك التعليمات:</b>\n\n"
        "1. اضغط على <b>/start</b> للبدء في استعمال البوت.\n"
        "2. اتبع التعليمات لإدخال درجاتك.\n"
        "3. تأكد من إدخال درجات صالحة بين 0 و 20.\n"
        "4. اضغط على <b>/cancel</b> في حالة كنت تريد إيقاف البوت.\n"
        "5. للقيام بإعادة البدء، اضغط أولاً على <b>/cancel</b> ثم <b>/start</b>.\n"
        "إذا كنت بحاجة إلى مساعدة إضافية، تواصل مع @yassineboukerma",
        parse_mode='HTML'
    )

def visitor_count(update, context):
    count = db.get_visitor_count()
    update.message.reply_text(f"The bot has been visited by {count + 600} unique users.")

def overall_average_count(update, context):
    count = db.get_overall_average_count()
    update.message.reply_text(f"The Bot has been used {count + 1530} times.")

def show_user_ids(update, context):
    user_ids = db.get_all_user_ids()
    update.message.reply_text(f"Collected user IDs: {', '.join(map(str, user_ids))}")

def whatsnew(update, context):
    update.message.reply_text(MESSAGE_whatsnew, parse_mode='HTML')
    update.message.reply_text(MESSAGE_AR_whatsnew, parse_mode='HTML')

# إعدادات البوت و webhook
BOT_TOKEN = "7163691593:AAFmVnHxBgH4ORZ9ohTC9QQpiDmKjWTaMEI"
WEBHOOK_HOST = "ens-average-bot-599688285140.europe-west1.run.app"
WEBHOOK_URL_PATH = BOT_TOKEN
WEBHOOK_URL = f"https://{WEBHOOK_HOST}/{WEBHOOK_URL_PATH}"

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)

ADMIN_ID = 5909420341
try:
    bot.send_message(chat_id=ADMIN_ID, text="✅ Bot has started successfully on Cloud Run!")
except Exception as e:
    print(f"Failed to send startup message: {e}")

def main():
    global db
    db = Database(DB_PATH)

    # إنشاء Updater بدلاً من Dispatcher
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', lambda update, context: start(update, context, db))],
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
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("visitor_count", visitor_count))
    dispatcher.add_handler(CommandHandler("usage_count", overall_average_count))
    dispatcher.add_handler(CommandHandler("showUserIDs", show_user_ids))
    dispatcher.add_handler(CommandHandler("whats_new", whatsnew))

    # تعيين webhook
    bot.set_webhook(url=WEBHOOK_URL)
    print(f"Webhook set to: {WEBHOOK_URL}")

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    # استخدام updater بدلاً من dispatcher مباشرة
    updater = Updater(token=BOT_TOKEN, use_context=True)
    updater.dispatcher.process_update(update)
    return 'ok'

@app.route('/')
def index():
    return 'Bot is running!'

if __name__ == '__main__':
    main()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

