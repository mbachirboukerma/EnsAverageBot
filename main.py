# Standard library imports
import logging
import math
import threading
import time
from datetime import time as datetime_time
from concurrent.futures import ThreadPoolExecutor
import os

# Third-party imports
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Dispatcher, Updater, CommandHandler, MessageHandler, Filters, 
    CallbackContext, ConversationHandler, CallbackQueryHandler
)
from telegram.error import TimedOut, Unauthorized, ChatMigrated
from retrying import retry

# Local imports
from specializations import SpecializationFactory
from database import Database

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants
DB_PATH = "bot_database.db"
CHANNELS = ["@infotouchcommunity", "@hqlaptop"]
BOT_TOKEN = "7202093679:AAFZFyXONDtl4y74ozJlkMupTDDIPxyA9So"

# Conversation states
SPECIALIZATION, LEVEL, SUB_LEVEL, FIRST, SECOND, TP, TD, NEXT_SUBJECT = range(8)

# Message templates
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

# Initialize database
db = Database(DB_PATH)

# Subject Categories
# These lists define which subjects have specific types of evaluations
EXAM1_SUBJECTS = [
    # Computer Science subjects
    "Bdd", "Réseau2", "GL", "Web2", "Poo", "systemExpert", "algo", "algo2", "sm1", "sm2", "se 1", "se 2", "si 1", "si 2", "ai", "compilation", "web", "ro",
    # Mathematics subjects
    "analyse", "algebre", "analyse 2", "calculs différentiels", "géométrie", "algèbre linéaire", "algèbre générale", "analyse numérique", "analyse complexe", "algèbre3",
    "théorie de mesure و de l'intégration1", "statistiques و probabilités", "logique", "topologie",
    # Physics subjects
    "thermo", "stm", "mecanique", "elect", "solid_state_physics", "modern_physics", "Mécanique quantique", "méthodes math",
    # Chemistry subjects
    "organic_chemistry", "analytical_chemistry", "technological_measurements", "thermochimie", "9iyassat",
    # Education subjects
    "psycho", "psycho4", "didactique", "tachri3", "psychologie 'enfant'", "psycho éducative", "psychologie éducative",
    # General subjects
    "tarikh l3olom", "tarbiya", "français", "anglais", "informatique", "informatiquee",
    # Arabic subjects
    "AdabJahili", "NaqdQadim", "Lissaneyat", "Nahw", "Aroud", "Balagha", "Sarf", "Fiqh", "FanT3bir", "HadharaIslam", "Informatique", "OuloumIslamia", "Anglais", "OuloumTarbawiya"
]

EXAM2_SUBJECTS = [
    # Computer Science subjects
    "Bdd", "Réseau2", "Web2", "Poo", "systemExpert", "GL",
    # Mathematics subjects
    "analyse", "algebre", "analyse 2", "calculs différentiels", "géométrie", "algèbre linéaire", "algèbre générale", "analyse numérique", "analyse complexe", "algèbre3",
    "théorie de mesure و de l'intégration1", "statistiques و probabilités", "logique", "topologie",
    # Physics subjects
    "thermo", "stm", "mecanique", "elect", "solid_state_physics", "modern_physics", "Mécanique quantique", "méthodes math",
    # Chemistry subjects
    "organic_chemistry", "analytical_chemistry", "technological_measurements", "thermochimie", "9iyassat",
    # Education subjects
    "psycho4", "didactique", "tachri3", "psychologie 'enfant'", "psycho éducative", "psychologie éducative",
    # General subjects
    "tarikh l3olom", "tarbiya", "français", "anglais", "informatique", "informatiquee",
    # Arabic subjects
    "AdabJahili", "NaqdQadim", "Lissaneyat", "Nahw", "Aroud", "Balagha", "Sarf", "Fiqh", "FanT3bir", "HadharaIslam", "Informatique", "OuloumIslamia", "Anglais", "OuloumTarbawiya"
]

TD_SUBJECTS = [
    # Computer Science subjects
    "GL", "algo", "algo2", "sm1", "sm2", "se 1", "se 2", "si 1", "si 2", "ai", "compilation", "web", "ro",
    # Mathematics subjects
    "analyse", "algebre", "analyse 2", "calculs différentiels", "géométrie", "algèbre linéaire", "algèbre générale", "analyse numérique", "analyse complexe", "algèbre3",
    "théorie de mesure و de l'intégration1", "statistiques و probabilités", "logique", "topologie",
    # Physics subjects
    "thermo", "stm", "mecanique", "elect", "solid_state_physics", "modern_physics", "Mécanique quantique", "méthodes math",
    # Chemistry subjects
    "organic_chemistry", "analytical_chemistry", "technological_measurements", "thermochimie", "9iyassat",
    # Education subjects
    "psycho", "psycho4", "didactique", "psychologie 'enfant'", "psycho éducative", "psychologie éducative",
    # General subjects
    "informatique", "informatiquee",
    # Arabic subjects
    "AdabJahili", "NaqdQadim", "Lissaneyat", "Nahw"
]

TP_SUBJECTS = [
    # Computer Science subjects
    "Réseau2", "Poo", "Web2", "Bdd", "compilation", "web", "algo2",
    # Physics subjects
    "thermo", "stm", "mecanique", "elect",
    # Biology subjects
    "cyto", "histo", "bv", "embryo", "géologie", "Biochimie", "Botanique", "Zoologie", "Microbiologie", "Paléontologie",
    "physiologie_végétale", "physiologie_animal", "pétrologie"
]

# Subjects that require CC (Continuous Control) evaluation
SUBJECTS_WITH_CC = [
    "chimie organique", "chimie analytique", "thermochimie", "9iyassat",
    "solid_state_physics", "organic_chemistry", "physics_education",
    "analytical_chemistry", "chemistry_education", "technological_measurements",
    "solid", "analytique", "nucl", "atomique"
]

# Subjects that require direct average input
SPECIAL_SUBJECTS = ["vibrations", "Optique"]

# Levels that have sub-levels (+4 or +5)
LEVELS_WITH_SUBLEVELS = ["physics4", "math4", "sciences4", "info4", "sciences3", "physics3"]

# Unsupported levels
UNSUPPORTED_LEVELS = [
    "musique1", "musique2", "musique3", "musique4 (+4)", 
    "musique4 (+5)", "musique5"
]

# Define grades and coefficients for each specialization and level
specializations = {
    'math': {
        'math1': {
            "analyse": 4,
            "algebre": 2,
            "thermo": 3,
            "stm": 3,
            "mecanique": 3,
            "elect": 3,
            "tarikh l3olom": 1,
            "tarbiya": 1,
        },
        'math2': {
            "topologie": 4,
            "analyse 2": 2,
            "calculs différentiels": 2,
            "informatiquee": 2,
            "psychologie 'enfant'": 2,
            "géométrie": 2,
            "algèbre linéaire": 2,
            "algèbre générale": 2,
        },
        'math3': {
            "analyse numérique": 4,
            "analyse complexe": 2,
            "algèbre3": 2,
            "théorie de mesure و de l'intégration1": 2,
            "psychologie éducative": 2,
            "géométrie": 2,
            "statistiques و probabilités": 2,
            "logic math": 1,
        },
        'math4 (+4)': {},
        'math4 (+5)': {
            "didactiques mathématiques": 2,
            "Analyse complexe": 2,
            "Algèbre4": 2,
            "Théorie de  mesure et de l'intégration2": 2,
            "Programmes d'études": 1,
            "Géométrie": 2,
            "Statistiques et probabilités2": 2,
            "Équations différentielles": 2,
        },
        'math5': {}
    },
    'physics': {
        'physics1': {
            "analyse": 4,
            "algebre": 2,
            "thermo": 3,
            "stm": 3,
            "mecanique": 3,
            "elect": 3,
            "tarikh l3olom": 1,
            "tarbiya": 1,
        },
        'physics2': {
            "math": 4,
            "vibrations": 3,  # اهتزازات
            "Optique": 3,  # الضوء
            "Cinetique && électrochimie": 3,  # الكيمياء الحركية و الكهربائية
            "équilibre": 4,  # توازنات
            "électronique": 4,  # إلكترونيات
            "informatique": 2,  # معلوماتية
            "psycho": 2,  # علم النفس
        },
        'physics3 (+4)': {
            "solid_state_physics": 4,
            "modern_physics": 4,
            "organic_chemistry": 4,
            "physics_education": 4,
            "analytical_chemistry": 3,
            "chemistry_education": 2,
            "technological_measurements": 2,
            "psycho3": 2,
        },
        'physics3 (+5)': {
            "mécanique classique": 3,
            "nisbiya": 3,
            "psycho3": 2,
            "chimie organique": 3,
            "chimie analytique": 3,
            "Mécanique quantique": 3,
            "méthodes math": 3,
            "thermochimie": 3,
            "9iyassat": 2,
        },
        'physics4 (+4)': {},
        'physics4 (+5)': {
            "solid": 3,
            "analytique": 3,
            "Fluides": 2,
            "info": 2,
            "nucl": 2,
            "atomique": 2,
            "didactique chimie": 3,
            "didactique physique": 3,
            "Manahidj": 1,
        },
        'physics5': {}
    },
    'info': {
        'info1': {
            "algo": 5,
            'sm1': 4,
            "logique": 3,
            "algebre": 3,
            "analyse": 3,
            "électro": 3,
            "stat": 2,
            "tarikh l3olom": 1,
            "education sciences 'fares'": 1,
            "français": 1
        },
        'info2': {
            "algo2": 5,
            "sm2": 4,
            "se 1": 4,
            "si 1": 3,
            "thl": 3,
            "ts": 3,
            "analyse numérique": 3,
            "psychologie 'fares'": 2,
            "anglais": 1
        },
        'info3': {
            "réseau": 4,
            "se 2": 4,
            "compilation": 4,
            "web": 3,
            "ro": 3,
            "psycho": 2,
            "si 2": 2,
            "ai": 2,
            "anglais": 1,
        },
        'info4 (+4)': {
            "Réseau2 ": 4,
            "GL ": 3,
            "Poo ": 3,
            "Web2 ": 3,
            "systemExpert ": 2,
            "psycho4 ": 1,
            "didactique ": 1,
            "tachri3 ": 1,
            "Stage": 3,
        },
        'info4 (+5)': {
            "Bdd": 4,
            "Réseau2": 4,
            "GL": 3,
            "Poo": 3,
            "Web2": 3,
            "systemExpert": 2,
            "psycho4": 1,
            "didactique": 1,
        },
        'info5': {}
    },
    'sciences': {
        'sciences1': {
            "chimie": 3,
            "biophysique": 3,
            "math": 3,
            "info": 1,
            "tarbya": 1,
            "cyto": 1.5,
            "histo": 1.5,
            "bv": 1.5,
            "embryo": 1.5,
            "géologie": 3,
        },
        'sciences2': {
            "Biochimie": 4,
            "Botanique": 4,
            "Zoologie": 4,
            "Microbiologie": 3,
            "Génétique": 3,
            "Paléontologie": 2,
            "Psycho2": 2,
        },
        'sciences3 (+4)': {
            "physiologie_animal": 3,
            "physiologie_végétale": 3,
            "biomol": 2,
            "pétrologie": 3,
            "psycho3": 2,
            "immunologie": 1,
            "parasitologie": 1,
            "anglais ": 1,
            "nutrition": 1,
        },
        'sciences3 (+5)': {
            "physiologie_animal": 3,
            "physiologie_végétale": 3,
            "biomol": 3,
            "pétrologie": 3,
            "psycho3": 2,
            "immunologie": 1,
            "parasitologie": 1,
            "anglais ": 1,
        },
        'sciences4 (+4)': {},
        'sciences4 (+5)':{},
        'sciences5': {}
    },
    'musique': {
        'musique1': {},
        'musique2': {},
        'musique3': {},
        'musique4 (+4)': {},
        'musique4 (+5)': {},
        'musique5': {}
    },
    'arabic': {
        'arabic1': {
            "AdabJahili": 3,
            "NaqdQadim": 3,
            "Lissaneyat": 3,
            "Nahw": 3,
            "Aroud": 2,
            "Balagha": 2,
            "Sarf": 2,
            "Fiqh": 2,
            "FanT3bir": 1,
            "HadharaIslam": 1,
            "Informatique": 1,
            "OuloumIslamia": 1,
            "Anglais": 1,
            "OuloumTarbawiya": 1
        }
    }
}

# --- Webhook Settings (fill these when ready) ---
WEBHOOK_HOST = "mbachirboukerma.pythonanywhere.com"
WEBHOOK_PORT = 443  # البورت الافتراضي للـ HTTPS
WEBHOOK_URL_PATH = BOT_TOKEN  # يفضل أن يكون هو نفسه التوكن
WEBHOOK_URL = f"https://{WEBHOOK_HOST}/{WEBHOOK_URL_PATH}"

# Helper Functions
def validate_grade(grade: str) -> bool:
    """Validate if the input grade is a valid number between 0 and 20."""
    try:
        value = float(grade)
        return 0 <= value <= 20
    except ValueError:
        return False

def get_menu_keyboard():
    """Create the menu keyboard with social media links."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Follow us on facebook", url='https://m.facebook.com/hqlaptop')],
        [InlineKeyboardButton("Follow us on Instagram", url='https://www.instagram.com/Hq.laptop')]
    ])

def get_specialization_keyboard():
    """Create keyboard for specialization selection."""
    keyboard = [
        [InlineKeyboardButton("Math", callback_data="math")],
        [InlineKeyboardButton("Physics", callback_data="physics")],
        [InlineKeyboardButton("Info", callback_data="info")],
        [InlineKeyboardButton("Sciences", callback_data="sciences")],
        [InlineKeyboardButton("Arabic", callback_data="arabic")],
        [InlineKeyboardButton("Musique", callback_data="musique")]
    ]
    return InlineKeyboardMarkup(keyboard)

@retry(wait_fixed=2000, stop_max_attempt_number=5, retry_on_exception=lambda x: isinstance(x, TimedOut))
def send_message(bot, chat_id, text, retries=3):
    """Send a message with retry logic for handling errors."""
    for attempt in range(retries):
        try:
            bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')
            logger.info(f"✅ تم إرسال الرسالة إلى المستخدم {chat_id}")
            return True

        except Unauthorized:
            logger.warning(f"User {chat_id} blocked the bot. Removing from database.")
            db.remove_user_from_database(chat_id)
            return False

        except TimedOut:
            logger.warning(f"Timeout error while sending message to {chat_id}. Retrying...")
            time.sleep(2)

        except ChatMigrated as e:
            new_chat_id = e.new_chat_id
            logger.warning(f"Chat ID {chat_id} has migrated to {new_chat_id}. Updating database.")
            db.update_chat_id(chat_id, new_chat_id)
            send_message(bot, new_chat_id, text)
            return True

        except Exception as e:
            logger.error(f"Failed to send message to {chat_id} on attempt {attempt+1}: {e}")
            time.sleep(2)

    logger.error(f"Giving up on sending message to {chat_id} after {retries} retries.")
    return False

def notify_users(bot):
    """Send notification message to all users in batches."""
    user_ids = db.get_all_user_ids()
    batch_size = 50

    for i in range(0, len(user_ids), batch_size):
        batch = user_ids[i:i+batch_size]
        logger.info(f"📤 إرسال دفعة المستخدمين من {i+1} إلى {i+len(batch)}")

        with ThreadPoolExecutor(max_workers=3) as executor:
            executor.map(lambda uid: send_message(bot, uid, MESSAGE), batch)

        time.sleep(3)  # تأخير 3 ثواني بين كل دفعة

def is_subscribed(update: Update, context: CallbackContext) -> bool:
    """Check if user is subscribed to required channels."""
    user_id = update.message.from_user.id
    try:
        for channel in CHANNELS:
            chat_member = context.bot.get_chat_member(channel, user_id)
            if chat_member.status not in ["member", "administrator", "creator"]:
                return False
        return True
    except Exception as e:
        logger.error(f"Error checking subscription: {e}")
        return False

# Command Handlers
def help_command(update: Update, context: CallbackContext) -> None:
    """Handle /help command."""
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

def visitor_count(update: Update, context: CallbackContext) -> None:
    """Handle /visitor_count command."""
    try:
        count = db.get_visitor_count()
        update.message.reply_text(
            f"👥 عدد الزوار: {count:,}",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error in visitor_count: {str(e)}")
        update.message.reply_text("❌ حدث خطأ أثناء جلب عدد الزوار")

def usage_count(update: Update, context: CallbackContext):
    """Handle /usage_count command."""
    try:
        count = db.get_overall_average_count()
        update.message.reply_text(
            f"📊 عدد مرات حساب المعدل: {count:,}",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error in usage_count: {str(e)}")
        update.message.reply_text("❌ حدث خطأ أثناء جلب عدد مرات الاستخدام")

def whats_new(update: Update, context: CallbackContext):
    """Handle /whats_new command."""
    message = """
🆕 <b>التحديثات الجديدة:</b>

1️⃣ <b>تحسينات في حساب المعدل:</b>
   • دعم للتخصصات الجديدة
   • حسابات أكثر دقة
   • واجهة مستخدم محسنة

2️⃣ <b>ميزات جديدة:</b>
   • إحصائيات استخدام البوت
   • تتبع عدد الزوار
   • تحسينات في الأداء

3️⃣ <b>تحسينات تقنية:</b>
   • قاعدة بيانات محسنة
   • معالجة أفضل للأخطاء
   • أداء أسرع

📢 <b>قريباً:</b>
   • دعم لتخصصات إضافية
   • ميزات إحصائية متقدمة
   • تحسينات في الواجهة
"""
    update.message.reply_text(message, parse_mode='HTML')

def whatsnew(update: Update, context: CallbackContext) -> None:
    """Handle /whatsnew command."""
    update.message.reply_text(MESSAGE_whatsnew, parse_mode='HTML')
    update.message.reply_text(MESSAGE_AR_whatsnew, parse_mode='HTML')

def show_user_ids(update: Update, context: CallbackContext) -> None:
    """Handle /users command."""
    user_ids = db.get_all_user_ids()
    update.message.reply_text(f"Collected user IDs: {', '.join(map(str, user_ids))}")

def cancel(update: Update, context: CallbackContext) -> int:
    """Handle /cancel command."""
    update.message.reply_text('Operation cancelled.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Conversation Handlers
@retry(wait_fixed=2000, stop_max_attempt_number=5, retry_on_exception=lambda x: isinstance(x, TimedOut))
def start(update: Update, context: CallbackContext) -> int:
    """Start the conversation and update visitor count."""
    user = update.effective_user
    
    # Update visitor count for new user
    try:
        db.update_visitors(user.id)
    except Exception as e:
        logger.error(f"Error updating visitor count: {str(e)}")

    # Check subscription
    if not is_subscribed(update, context):
        keyboard = [[InlineKeyboardButton(f"📢 اشترك في {channel[1:]}", url=f"https://t.me/{channel[1:]}")] for channel in CHANNELS]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            "🔹 يجب الاشتراك في القنوات التالية أولاً:",
            reply_markup=reply_markup
        )
        return ConversationHandler.END

    # Show specializations as ReplyKeyboard (not Inline)
    keyboard = [
        ["Math"],
        ["Physics"],
        ["Info"],
        ["Sciences"],
        ["Musique"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text(
        "Hello! Welcome to the Grade Calculator Bot. 🎓\n\n"
        "This bot will help you calculate your overall average grade. Please choose your specialization to get started:\n"
        "- Math\n"
        "- Physics\n"
        "- Info\n"
        "- Sciences\n"
        "- Musique\n\n"
        "If you need any help, type /help. To cancel the process at any time, type /cancel.",
        reply_markup=reply_markup,
    )
    return SPECIALIZATION

def choose_specialization(update: Update, context: CallbackContext) -> int:
    """Handle specialization selection."""
    user_data = context.user_data
    specialization = update.message.text.lower()

    if specialization not in specializations:
        update.message.reply_text("Please choose a valid specialization.")
        return SPECIALIZATION

    user_data['specialization'] = specialization
    keyboard = [
        [f"{specialization.capitalize()}1"],
        [f"{specialization.capitalize()}2"],
        [f"{specialization.capitalize()}3"],
        [f"{specialization.capitalize()}4"],
        [f"{specialization.capitalize()}5"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text("Please choose your level:", reply_markup=reply_markup)
    return LEVEL

def choose_level(update: Update, context: CallbackContext) -> int:
    """Handle level selection and sub-level if needed."""
    user_data = context.user_data
    level = update.message.text.lower()

    if level in UNSUPPORTED_LEVELS:
        update.message.reply_text("<b>هذا التخصص لن يتم دعمه.</b>", parse_mode='HTML')
        update.message.reply_text(
            "الحمد لله، والصلاة والسلام على رسول الله، وعلى آله، وصحبه، أما بعد:\n\n"
            "فالموسيقى لا تجوز دراستها، ولا تدريسها للكبار، ولا للصغار، وراجع في ذلك الفتاوى ذوات الأرقام التالية: "
            "<a href=\"https://www.islamweb.net/ar/fatwa/7932/%D9%87%D9%84-%D9%8A%D8%AC%D9%88%D8%B2-%D8%AD%D8%B6%D9%88%D8%B1-%D8%AF%D8%B1%D9%88%D8%B3-%D8%A7%D9%84%D9%85%D9%88%D8%B3%D9%8A%D9%82%D9%89-%D8%A5%D8%B0%D8%A7-%D9%8A%D9%88%D9%82%D9%81-%D8%B9%D9%84%D9%8A%D9%87%D8%A7-%D8%A7%D9%84%D8%AA%D8%AE%D8%B1%D8%AC\">7932</a>، "
            "<a href=\"https://www.islamweb.net/ar/fatwa/73834/%D8%AD%D9%83%D9%85-%D8%A7%D9%84%D8%AF%D8%B1%D8%A7%D8%B3%D8%A9-%D9%81%D9%8A-%D9%83%D9%84%D9%8A%D8%A9-%D9%85%D9%86-%D8%B6%D9%85%D9%86-%D9%85%D9%88%D8%A7%D8%AF%D9%87%D8%A7-%D8%A7%D9%84%D9%85%D9%88%D8%B3%D9%8A%D9%82%D9%89\">73834</a>، "
            "<a href=\"https://www.islamweb.net/ar/fatwa/191797/%D8%AD%D8%B1%D9%85%D8%A9-%D8%A7%D9%84%D9%85%D9%88%D8%B3%D9%8A%D9%82%D9%89-%D8%AA%D8%B4%D9%85%D9%84-%D8%AF%D8%B1%D8%A7%D8%B3%D8%AA%D9%87%D8%A7%D8%8C%20%D9%88%D9%84%D8%A7,%D8%AA%D8%AE%D9%84%D9%88%20%D9%85%D9%86%20%D9%85%D8%AB%D9%84%20%D9%87%D8%B0%D9%87%20%D8%A7%D9%84%D9%85%D8%A7%D8%AF%D8%A9.\">المصدر</a>",
            parse_mode='HTML'
        )
        return ConversationHandler.END

    specialization = user_data['specialization']
    
    # Get specialization instance
    spec = SpecializationFactory.get_specialization(specialization)
    if not spec:
        update.message.reply_text("Error: Invalid specialization")
        return ConversationHandler.END

    # Check if the year is supported
    if not spec.is_year_supported(level):
        update.message.reply_text("لم يتم اضافة هذا التخصص بعد، يرجى الانتظار.")
        update.message.reply_text("This level is not supported yet. Please wait for upcoming updates.")
        return ConversationHandler.END

    if level in LEVELS_WITH_SUBLEVELS:
        user_data['level_base'] = level
        keyboard = [["+4"], ["+5"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        update.message.reply_text("Please choose your sub-level:", reply_markup=reply_markup)
        return SUB_LEVEL

    if level not in specializations[specialization]:
        update.message.reply_text("Please choose a valid level.")
        return LEVEL

    user_data['level'] = level
    return initialize_grade_calculation(update, context, user_data)

def choose_sub_level(update: Update, context: CallbackContext) -> int:
    """Handle sub-level selection."""
    user_data = context.user_data
    sub_level = update.message.text.lower()
    
    if sub_level not in ["+4", "+5"]:
        update.message.reply_text("Please choose a valid sub-level.")
        return SUB_LEVEL

    level_base = user_data['level_base']
    level = f"{level_base} ({sub_level})"
    
    # Get specialization instance
    spec = SpecializationFactory.get_specialization(user_data['specialization'])
    if not spec:
        update.message.reply_text("Error: Invalid specialization")
        return ConversationHandler.END

    # Check if the year is supported
    if not spec.is_year_supported(level):
        update.message.reply_text("لم يتم اضافة هذا التخصص بعد، يرجى الانتظار.")
        update.message.reply_text("This level is not supported yet. Please wait for upcoming updates.")
        return ConversationHandler.END

    user_data['level'] = level
    return initialize_grade_calculation(update, context, user_data)

def initialize_grade_calculation(update, context, user_data: dict) -> int:
    """Initialize grade calculation variables."""
    user_data['current_subject_index'] = 0
    user_data['subject_grades'] = {}
    user_data['total_grades'] = 0
    user_data['total_coefficients'] = 0
    return ask_for_grades(update, context)

def ask_for_grades(update: Update, context: CallbackContext) -> int:
    """Ask for grades for the current subject."""
    user_data = context.user_data
    specialization = user_data['specialization']
    level = user_data['level']
    subjects = list(specializations[specialization][level].keys())
    current_index = user_data['current_subject_index']

    if current_index >= len(subjects):
        return show_final_average(update, context)

    subject = subjects[current_index]
    user_data['current_subject'] = subject
    user_data['current_subject_grades'] = []

    if subject in SPECIAL_SUBJECTS:
        update.message.reply_text(f"Enter the average grade for {subject} directly:", parse_mode='HTML')
        return NEXT_SUBJECT

    update.message.reply_text(f"Enter the grade for {subject} - Exam 1 :", parse_mode='HTML')
    return FIRST

def show_final_average(update: Update, context: CallbackContext) -> int:
    """Show the final average and end the conversation."""
    user_data = context.user_data

    if user_data['total_coefficients'] == 0:
        update.message.reply_text("No subjects found for this level.")
        return ConversationHandler.END

    average = user_data['total_grades'] / user_data['total_coefficients']
    db.increment_overall_average_count()

    update.message.reply_text("<b>---------------------------------------------</b>", parse_mode='HTML')
    average = math.ceil(average * 100) / 100
    update.message.reply_text(f"<b>Your overall average grade is: <span class=\"tg-spoiler\">{average:.2f}</span></b>", parse_mode='HTML')

    if average >= 10.00:
        update.message.reply_text("<b><span class=\"tg-spoiler\">Congratulations!! YA LKHABACH</span></b>", parse_mode='HTML')
    else:
        update.message.reply_text("<b><span class=\"tg-spoiler\">Don't worry, Rana ga3 f rattrapage.</span></b>", parse_mode='HTML')

    update.message.reply_text(
        "<b>Thank you for using our bot</b>\n\n"
        "<b>Don't forget to follow us on Instagram & Facebook !!</b>\n\n"
        "<b>If you want to use the bot again, click /start.</b>\n\n\n"
        "<b>Developed by <a href=\"https://www.instagram.com/yassine_boukerma\">Yassine Boukerma</a> with ❤️</b>",
        reply_markup=get_menu_keyboard(),
        parse_mode='HTML'
    )

    return ConversationHandler.END

def receive_first_grade(update: Update, context: CallbackContext) -> int:
    """Handle the first exam grade input."""
    user_data = context.user_data
    grade = update.message.text

    if not validate_grade(grade):
        update.message.reply_text("Please enter a valid grade between 0 and 20.")
        return FIRST

    user_data['current_subject_grades'].append(float(grade))

    if user_data['current_subject'] in EXAM1_SUBJECTS:
        update.message.reply_text(f"Enter the grade for {user_data['current_subject']} - Exam 2 :", parse_mode='HTML')
        return SECOND
    else:
        return receive_second_grade(update, context)

def receive_second_grade(update: Update, context: CallbackContext) -> int:
    """Handle the second exam grade input."""
    user_data = context.user_data
    grade = update.message.text

    if not validate_grade(grade):
        update.message.reply_text("Please enter a valid grade between 0 and 20.")
        return SECOND

    if user_data['current_subject'] in EXAM2_SUBJECTS:
        user_data['current_subject_grades'].append(float(grade))
    else:
        user_data['current_subject_grades'].append(user_data['current_subject_grades'][0])

    if user_data['current_subject'] in TP_SUBJECTS:
        update.message.reply_text(f"Enter the grade for {user_data['current_subject']} - TP :", parse_mode='HTML')
        return TP
    else:
        return receive_tp_grade(update, context)

def receive_tp_grade(update: Update, context: CallbackContext) -> int:
    """Handle the TP grade input."""
    user_data = context.user_data
    grade = update.message.text

    if user_data['current_subject'] in TP_SUBJECTS:
        if not validate_grade(grade):
            update.message.reply_text("Please enter a valid grade between 0 and 20.")
            return TP
        user_data['current_subject_grades'].append(float(grade))
    else:
        user_data['current_subject_grades'].append(None)

    if user_data['current_subject'] in SUBJECTS_WITH_CC:
        update.message.reply_text(f"Enter the grade for {user_data['current_subject']} - CC :", parse_mode='HTML')
        return TD
    elif user_data['current_subject'] in TD_SUBJECTS:
        update.message.reply_text(f"Enter the grade for {user_data['current_subject']} - TD :", parse_mode='HTML')
        return TD
    else:
        return receive_td_grade(update, context)

def receive_td_grade(update: Update, context: CallbackContext) -> int:
    """Handle the TD/CC grade input."""
    user_data = context.user_data
    grade = update.message.text

    if user_data['current_subject'] in TD_SUBJECTS:
        if not validate_grade(grade):
            update.message.reply_text("Please enter a valid grade between 0 and 20.")
            return TD
        user_data['current_subject_grades'].append(float(grade))
    else:
        user_data['current_subject_grades'].append(None)

    return calculate_subject_average(update, context)

def calculate_subject_average(update: Update, context: CallbackContext) -> int:
    """Calculate and store the average for the current subject."""
    user_data = context.user_data
    specialization = user_data['specialization']
    level = user_data['level']
    subject = user_data['current_subject']
    grades = user_data['current_subject_grades']

    # Get specialization instance
    spec = SpecializationFactory.get_specialization(specialization)
    if not spec:
        update.message.reply_text("Error: Invalid specialization")
        return ConversationHandler.END

    try:
        # Calculate average using the specialization class
        average = spec.calculate_average(level, subject, grades)
        coefficient = spec.get_subjects(level)[subject].coefficient

        update.message.reply_text(
            f"<b>The average grade for {subject} is: {average:.2f}</b>",
            parse_mode='HTML'
        )

        user_data['total_grades'] += average * coefficient
        user_data['total_coefficients'] += coefficient

        # Update user stats in database
        db.update_user_stats(update.effective_user.id, average)

    except ValueError as e:
        update.message.reply_text(f"Error: {str(e)}")
        return ConversationHandler.END

    user_data['current_subject_index'] += 1
    return ask_for_grades(update, context)

def receive_subject_average(update: Update, context: CallbackContext) -> int:
    """Handle direct average input for special subjects."""
    user_data = context.user_data
    subject = user_data['current_subject']
    average = update.message.text

    if not validate_grade(average):
        update.message.reply_text("Please enter a valid average between 0 and 20.")
        return NEXT_SUBJECT

    average = float(average)
    coefficient = specializations[user_data['specialization']][user_data['level']][subject]

    user_data['total_grades'] += average * coefficient
    user_data['total_coefficients'] += coefficient

    user_data['current_subject_index'] += 1
    return ask_for_grades(update, context)

# إعداد Flask
app = Flask(__name__)

# إعداد البوت و Dispatcher
bot = Bot(token=BOT_TOKEN)
bot.setWebhook(WEBHOOK_URL)
dispatcher = Dispatcher(bot, None, workers=1)

# نقطة استقبال التحديثات من تيليجرام
@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

# نقطة اختبار (اختياري)
@app.route('/')
def index():
    return 'Bot is running!'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

