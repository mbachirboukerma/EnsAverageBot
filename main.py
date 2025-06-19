from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from concurrent.futures import ThreadPoolExecutor
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from retrying import retry
from telegram.error import TimedOut, Unauthorized
import sqlite3
from contextlib import closing
import logging
import math
import threading
import time
import os
from flask import Flask, request
from telegram import Bot
from telegram.ext import Dispatcher


db_lock = threading.Lock()  # ✅ إنشاء قفل لحماية قاعدة البيانات


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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

SPECIALIZATION, LEVEL, SUB_LEVEL, FIRST, SECOND, TP, TD, NEXT_SUBJECT = range(8)  # ✅ تعريف القيم الصحيحة


class Database:
    """ كلاس لإدارة الاتصال بقاعدة البيانات وتحسين الأداء """
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)  # ✅ السماح باستخدام الـ Threads
        self.cursor = self.conn.cursor()
        self.lock = threading.RLock()  # ✅ قفل لحماية العمليات المتزامنة
        self._visitor_count_cache = None
        self._usage_count_cache = None
        self.init_db()

    def execute(self, query, params=()):
        """تنفيذ استعلام دون إرجاع بيانات"""
        with self.lock:  # ✅ منع التداخل بين العمليات
            self.cursor.execute(query, params)
            self.conn.commit()

    def fetchone(self, query, params=()):
        """تنفيذ استعلام وإرجاع صف واحد"""
        with self.lock:
            self.cursor.execute(query, params)
            return self.cursor.fetchone()

    def fetchall(self, query, params=()):
        """تنفيذ استعلام وإرجاع كل النتائج"""
        with self.lock:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()

    def init_db(self):
        """إنشاء الجداول في قاعدة البيانات إن لم تكن موجودة"""
        with self.lock:
            self.execute('''CREATE TABLE IF NOT EXISTS visitors (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id INTEGER UNIQUE)''')
            self.execute('''CREATE TABLE IF NOT EXISTS overall_average_count (count INTEGER)''')
            self.execute('''INSERT OR IGNORE INTO overall_average_count (count) VALUES (0)''')
            self.execute('''CREATE TABLE IF NOT EXISTS visitor_count_table (
                                id INTEGER PRIMARY KEY,
                                count INTEGER NOT NULL)''')
            # تأكد من إدخال قيمة افتراضية إذا لم تكن موجودة
            self.execute('''INSERT OR IGNORE INTO visitor_count_table (id, count) VALUES (1, 2000)''')

    def update_visitors(self, user_id):
        """تحديث عدد الزوار"""
        with self.lock:
            self.execute("INSERT OR IGNORE INTO visitors (user_id) VALUES (?)", (user_id,))
            if self.fetchone("SELECT user_id FROM visitors WHERE user_id = ?", (user_id,)):
                print(f"✅ تم إضافة user_id جديد: {user_id}")

            self._visitor_count_cache = None  # ✅ إعادة ضبط الكاش

    def get_visitor_count(self):
        """إرجاع عدد الزوار، مع استخدام التخزين المؤقت"""
        with self.lock:
            if self._visitor_count_cache is None:
                self._visitor_count_cache = self.fetchone("SELECT COUNT(*) FROM visitors")[0]
            return self._visitor_count_cache

    def get_all_user_ids(self):
        """إرجاع قائمة بجميع معرفات المستخدمين"""
        with self.lock:
            user_ids = self.fetchall("SELECT user_id FROM visitors")
            return [user_id[0] for user_id in user_ids]

    def get_overall_average_count(self):
        """إرجاع عدد الاستخدامات الكلي مع التخزين المؤقت"""
        with self.lock:
            if self._usage_count_cache is None:
                self._usage_count_cache = self.fetchone("SELECT count FROM overall_average_count")[0]
            return self._usage_count_cache

    def increment_overall_average_count(self):
        """زيادة عدد الاستخدامات وإعادة ضبط الكاش"""
        with self.lock:
            self.execute("UPDATE overall_average_count SET count = count + 1")
            self._usage_count_cache = None  # ✅ إعادة ضبط الكاش

    def remove_user_from_database(self, user_id):
        """حذف مستخدم من قاعدة البيانات"""
        with self.lock:
            self.execute("DELETE FROM visitors WHERE user_id = ?", (user_id,))
            logging.info(f"Removed user {user_id} from database")

    def close(self):
        """إغلاق الاتصال بقاعدة البيانات عند إنهاء التشغيل"""
        with self.lock:
            self.conn.close()

# تحديد المسار الصحيح لقاعدة البيانات
DB_PATH = "bot_newdata.db"

# إنشاء كائن قاعدة البيانات لاستخدامه في جميع الوظائف
db = Database(DB_PATH)

def send_message(bot, chat_id, text, retries=3):
    """إرسال رسالة مع إعادة المحاولة عند حدوث أخطاء"""
    for attempt in range(retries):
        try:
            bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')
            logging.info(f"✅ تم إرسال الرسالة إلى المستخدم {chat_id}")
            return  # تم الإرسال بنجاح، نخرج من الدالة

        except Unauthorized:
            logging.warning(f"User {chat_id} blocked the bot. Removing from database.")
            db.remove_user_from_database(chat_id)
            return  # لا داعي لإعادة المحاولة

        except TimedOut:
            logging.warning(f"Timeout error while sending message to {chat_id}. Retrying...")
            time.sleep(2)  # انتظار ثم إعادة المحاولة

        except ChatMigrated as e:
            new_chat_id = e.new_chat_id
            logging.warning(f"Chat ID {chat_id} has migrated to {new_chat_id}. Updating database.")
            db.update_chat_id(chat_id, new_chat_id)  # تحديث معرف الدردشة
            send_message(bot, new_chat_id, text)  # إعادة الإرسال للمعرف الجديد
            return

        except Exception as e:
            logging.error(f"Failed to send message to {chat_id} on attempt {attempt+1}: {e}")
            time.sleep(2)  # انتظار قبل إعادة المحاولة

    logging.error(f"Giving up on sending message to {chat_id} after {retries} retries.")

def notify_users(bot):
    user_ids = db.get_all_user_ids()
    batch_size = 50

    for i in range(0, len(user_ids), batch_size):
        batch = user_ids[i:i+batch_size]
        logging.info(f"📤 إرسال دفعة المستخدمين من {i+1} إلى {i+len(batch)}")


        with ThreadPoolExecutor(max_workers=3) as executor:
            executor.map(lambda uid: send_message(bot, uid, MESSAGE), batch)

        time.sleep(3)  # تأخير 3 ثواني بين كل دفعة


#whats new messages

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


# Define groups for exams, TD, and TP
exam1_subjects = [
    "Bdd", "Réseau2",  "GL", "Web2", "Poo", "systemExpert", "psycho",  "didactique", "tachri3", "analyse", "informatiquee", "algebre", "thermo", "stm", "mecanique", "elect", "tarikh l3olom", "tarbiya","solid_state_physics","organic_chemistry","analytical_chemistry","technological_measurements","modern_physics",
    "topologie", "analyse 2", "calculs différentiels", "informatique", "psychologie 'enfant'", "psycho éducative", "Mécanique quantique", "méthodes math", "thermochimie", "9iyassat",
    "géométrie", "algèbre linéaire", "algèbre générale", "analyse numérique", "analyse complexe", "algèbre3",
    "théorie de mesure و de l'intégration1", "psychologie éducative", "statistiques و probabilités", "logique",
    "math", "Optique", "Cinetique && électrochimie", "équilibre", "électronique", "algo","physics_education",
    "sm1", "logique", "électro", "stat", "education sciences 'fares'", "français", "algo2", "sm2", "se 1", "si 1", "psycho4",
    "thl", "ts", "psychologie 'fares'", "anglais", "réseau", "se 2", "compilation", "web", "ro", "psycho", "si 2", "ai", "chimie", "biophysique", "géologie","didactiques mathématiques", "Analyse complexe","Algèbre4", "Théorie de  mesure et de l'intégration2", "Géométrie", "Statistiques et probabilités2","Équations différentielles","Biochimie","Botanique","Zoologie","Microbiologie","Génétique","Paléontologie","physiologie_végétale","physiologie_animal","pétrologie","biomol","psycho3"
]
exam2_subjects = [
    "Bdd", "Réseau2", "Web2", "Poo", "systemExpert", "psycho4",  "didactique", "tachri3", "GL", "Fluides", "didactique chimie", "math","analyse", "informatiquee", "algebre", "thermo", "stm", "mecanique", "elect", "tarikh l3olom", "tarbiya","solid_state_physics","organic_chemistry","analytical_chemistry","technological_measurements","modern_physics",
    "topologie", "analyse 2", "calculs différentiels", "informatique", "psychologie 'enfant'",  "psycho éducative", "Mécanique quantique", "méthodes math", "thermochimie", "9iyassat",
    "géométrie", "algèbre linéaire", "algèbre générale", "analyse numérique", "analyse complexe", "algèbre3",
    "théorie de mesure و de l'intégration1", "psychologie éducative", "statistiques و probabilités", "logique",
    "math", "Cinetique && électrochimie", "équilibre", "électronique", "algo","education sciences 'fares'","physics_education",
    "sm1", "logique", "électro", "stat", "français", "algo2", "sm2", "se 1", "si 1",
    "thl", "ts", "psychologie 'fares'", "anglais", "réseau", "se 2", "compilation", "web", "ro", "psycho", "si 2", "ai", "chimie", "biophysique", "géologie","didactiques mathématiques", "Analyse complexe","Algèbre4", "Théorie de  mesure et de l'intégration2", "Géométrie", "Statistiques et probabilités2","Équations différentielles","Biochimie","Botanique","Zoologie","Microbiologie","Génétique","Paléontologie","physiologie_végétale","physiologie_animal","pétrologie","biomol","psycho3"
]

td_subjects = [
    "GL ", "GL", "Fluides", "didactique chimie", "math", "vibrations", "psychologie 'fares'", "psychologie 'enfant'", "Optique", "Cinetique && électrochimie", "équilibre", "électronique", "informatique",
    "algo", "algo2", "sm1", "sm2", "stat", "se 1", "thl", "si 1", "ts", "analyse numérique", "psycho", "ro", "se 2", "compilation","mécanique classique", "nisbiya", "psycho éducative", "chimie organique", "chimie analytique", "Mécanique quantique", "méthodes math", "thermochimie", "9iyassat",
    "topologie", "analyse 2", "calculs différentiels", "géométrie", "algèbre linéaire", "algèbre générale", "analyse complexe", "stm", "solid", "analytique", "nucl", "atomique",
    "algèbre3", "théorie de mesure و de l'intégration1", "statistiques و probabilités", "analyse", "algebre", "thermo","solid_state_physics","organic_chemistry","physics_education","analytical_chemistry","chemistry_education","technological_measurements","modern_physics", "mecanique", "elect", "logique", "électro", "psychologie éducative", "chimie", "biophysique","didactiques mathématiques", "Analyse complexe","Algèbre4", "Théorie de  mesure et de l'intégration2", "Géométrie", "Statistiques et probabilités2","Équations différentielles","Biochimie","Zoologie","Génétique","Psycho2","biomol","psycho3"
]

tp_subjects = [
    "Réseau2 ", "Poo ", "Web2 ", "Bdd", "Réseau2", "Poo","Web2", "didactique physique", "info","vibrations", "informatiquee", "Optique", "Cinetique && électrochimie", "équilibre", "électronique", "compilation", "web",
    "réseau", "algo2", "thermo", "stm", "mecanique", "elect", "algo", "cyto", "histo", "bv", "embryo", "géologie","Biochimie","Botanique","Zoologie","Microbiologie","Paléontologie","physiologie_végétale","physiologie_animal","pétrologie",
]

subject_with_cc =["chimie organique", "chimie analytique", "thermochimie", "9iyassat" ,"solid_state_physics", "organic_chemistry", "physics_education", "analytical_chemistry", "chemistry_education", "technological_measurements","solid","analytique","nucl","atomique"]


# Define special subjects that require direct average input
special_subjects = ["vibrations", "Optique"]

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
            "sm1": 4,
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
    }
}

# Menu keyboard to appear after showing overall average
def get_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Follow us on facebook", url='https://m.facebook.com/hqlaptop')],
        [InlineKeyboardButton("Follow us on Instagram", url='https://www.instagram.com/Hq.laptop')]
    ])


def is_subscribed(update: Update, context: CallbackContext) -> bool:
    user_id = update.message.from_user.id
    try:
        for channel in CHANNELS:
            chat_member = context.bot.get_chat_member(channel, user_id)
            if chat_member.status not in ["member", "administrator", "creator"]:
                return False  # ❌ إذا لم يكن مشتركًا في إحدى القنوات، نعيد False
        return True  # ✅ المستخدم مشترك في جميع القنوات
    except Exception as e:
        logging.error(f"Error checking subscription: {e}")
        return False  # ❌ أي خطأ يتم اعتباره عدم اشتراك

@retry(wait_fixed=2000, stop_max_attempt_number=5, retry_on_exception=lambda x: isinstance(x, TimedOut))
def start(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    db.update_visitors(user_id)

    # 🔹 التحقق من الاشتراك في جميع القنوات
    if not is_subscribed(update, context):
        keyboard = [[InlineKeyboardButton(f"📢 اشترك في {channel}", url=f"https://t.me/{channel[1:]}")] for channel in CHANNELS]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            "❌ يجب عليك الاشتراك في القنوات التالية لاستخدام البوت:\n\n"
            f"1️⃣ {CHANNELS[0]}\n"
            f"2️⃣ {CHANNELS[1]}\n\n"
            "🔹 بعد الاشتراك، اضغط على /start من جديد.",
            reply_markup=reply_markup
        )
        return -1  # ❌ لا يمكنه المتابعة

    # ✅ المستخدم مشترك في القنوات، يكمل العملية
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
    return SPECIALIZATION  # ✅ يجب أن يكون معرفًا مسبقًا

def choose_specialization(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    specialization = update.message.text.lower()

    if specialization not in specializations:
        update.message.reply_text("Please choose a valid specialization.")
        return SPECIALIZATION

    user_data['specialization'] = specialization
    keyboard = [[f"{specialization.capitalize()}1"], [f"{specialization.capitalize()}2"], [f"{specialization.capitalize()}3"], [f"{specialization.capitalize()}4"],[f"{specialization.capitalize()}5"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text("Please choose your level:", reply_markup=reply_markup)
    return LEVEL

levelsWithSubLevels = ["physics4", "math4", "sciences4", "info4","sciences3",'physics3']

def choose_level(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    level = update.message.text.lower()

    not_added_levels = [ "sciences4 (+4)", "sciences4 (+5)", "sciences5",
                    "physics4 (+4)", "physics5",
                    "math4 (+4)", "math5",
                    "info5"]
    not_supported_levels = ["musique1", "musique2", "musique3", "musique4 (+4)", "musique4 (+5)", "musique5"]

    if level in not_added_levels:
        update.message.reply_text("لم يتم اضافة هذا التخصص بعد، يرجى الانتظار.")
        update.message.reply_text("This level is not listed yet, Please wait for upcoming updates.")
        return ConversationHandler.END

    if level in not_supported_levels:
        update.message.reply_text("<b>هذا التخصص لن يتم دعمه.</b>", parse_mode='HTML')
        update.message.reply_text(
            "الحمد لله، والصلاة والسلام على رسول الله، وعلى آله، وصحبه، أما بعد:\n\n"
            "فالموسيقى لا تجوز دراستها، ولا تدريسها للكبار، ولا للصغار، وراجع في ذلك الفتاوى ذوات الأرقام التالية: "
            "<a href=\"https://www.islamweb.net/ar/fatwa/7932/%D9%87%D9%84-%D9%8A%D8%AC%D9%88%D8%B2-%D8%AD%D8%B6%D9%88%D8%B1-%D8%AF%D8%B1%D9%88%D8%B3-%D8%A7%D9%84%D9%85%D9%88%D8%B3%D9%8A%D9%82%D9%89-%D8%A5%D8%B0%D8%A7-%D8%AA%D9%88%D9%82%D9%81-%D8%B9%D9%84%D9%8A%D9%87%D8%A7-%D8%A7%D9%84%D8%AA%D8%AE%D8%B1%D8%AC\">7932</a>، "
            "<a href=\"https://www.islamweb.net/ar/fatwa/73834/%D8%AD%D9%83%D9%85-%D8%A7%D9%84%D8%AF%D8%B1%D8%A7%D8%B3%D8%A9-%D9%81%D9%8A-%D9%83%D9%84%D9%8A%D8%A9-%D9%85%D9%86-%D8%B6%D9%85%D9%86-%D9%85%D9%88%D8%A7%D8%AF%D9%87%D8%A7-%D8%A7%D9%84%D9%85%D9%88%D8%B3%D9%8A%D9%82%D9%89\">73834</a>، "
            "<a href=\"https://www.islamweb.net/ar/fatwa/191797/%D8%AD%D8%B1%D9%85%D8%A9-%D8%A7%D9%84%D9%85%D9%88%D8%B3%D9%8A%D9%82%D9%89-%D8%AA%D8%B4%D9%85%D9%84-%D8%AF%D8%B1%D8%A7%D8%B3%D8%AA%D9%87%D8%A7%D8%8C%20%D9%88%D9%84%D8%A7,%D8%AA%D8%AE%D9%84%D9%88%20%D9%85%D9%86%20%D9%85%D8%AB%D9%84%20%D9%87%D8%B0%D9%87%20%D8%A7%D9%84%D9%85%D8%A7%D8%AF%D8%A9.\">المصدر</a>"
        , parse_mode='HTML')
        return ConversationHandler.END

    specialization = user_data['specialization']
    if level in levelsWithSubLevels:
        user_data['level_base'] = level
        keyboard = [["+4"], ["+5"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        update.message.reply_text("Please choose your sub-level:", reply_markup=reply_markup)
        return SUB_LEVEL

    if level not in specializations[specialization]:
        update.message.reply_text("Please choose a valid level.")
        return LEVEL

    user_data['level'] = level
    user_data['current_subject_index'] = 0
    user_data['subject_grades'] = {}
    user_data['total_grades'] = 0
    user_data['total_coefficients'] = 0

    return ask_for_grades(update, context)

def choose_sub_level(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    sub_level = update.message.text.lower()
    not_added_levels = ["sciences4 (+4)", "sciences4 (+5)", "sciences5",
                    "physics4 (+4)", "physics5",
                    "math4 (+4)", "math5",
                    "info5"]
    if sub_level not in ["+4", "+5"]:
        update.message.reply_text("Please choose a valid sub-level.")
        return SUB_LEVEL

    level_base = user_data['level_base']
    if sub_level == "+4":
        if f"{level_base} (+4)" in not_added_levels:
            update.message.reply_text("لم يتم اضافة هذا التخصص بعد، يرجى الانتظار.")
            update.message.reply_text("This level is not listed yet, Please wait for upcoming updates.")
            return ConversationHandler.END
        user_data['level'] = f"{level_base} (+4)"
    elif sub_level == "+5":
        if f"{level_base} (+5)" in not_added_levels:
            update.message.reply_text("لم يتم اضافة هذا التخصص بعد، يرجى الانتظار.")
            update.message.reply_text("This level is not listed yet, Please wait for upcoming updates.")
            return ConversationHandler.END
        user_data['level'] = f"{level_base} (+5)"

    user_data['current_subject_index'] = 0
    user_data['subject_grades'] = {}
    user_data['total_grades'] = 0
    user_data['total_coefficients'] = 0

    return ask_for_grades(update, context)

def ask_for_grades(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    specialization = user_data['specialization']
    level = user_data['level']
    subjects = list(specializations[specialization][level].keys())
    current_index = user_data['current_subject_index']

    if current_index >= len(subjects):
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

    subject = subjects[current_index]
    user_data['current_subject'] = subject
    user_data['current_subject_grades'] = []

    if subject in special_subjects:
        update.message.reply_text(f"Enter the average grade for {subject} directly:", parse_mode='HTML')
        return NEXT_SUBJECT

    update.message.reply_text(f"Enter the grade for {subject} - Exam 1 :", parse_mode='HTML')
    return FIRST

def validate_grade(grade: str) -> bool:
    try:
        value = float(grade)
        return 0 <= value <= 20
    except ValueError:
        return False

def receive_first_grade(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    grade = update.message.text

    if not validate_grade(grade):
        update.message.reply_text("Please enter a valid grade between 0 and 20.")
        return FIRST

    user_data['current_subject_grades'].append(float(grade))

    if user_data['current_subject'] in exam1_subjects:
        update.message.reply_text(f"Enter the grade for {user_data['current_subject']} - Exam 2 :", parse_mode='HTML')
        return SECOND
    else:
        return receive_second_grade(update, context)

def receive_second_grade(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    grade = update.message.text

    if not validate_grade(grade):
        update.message.reply_text("Please enter a valid grade between 0 and 20.")
        return SECOND

    if user_data['current_subject'] in exam2_subjects:
        user_data['current_subject_grades'].append(float(grade))
    else:
        user_data['current_subject_grades'].append(user_data['current_subject_grades'][0])

    if user_data['current_subject'] in tp_subjects:
        update.message.reply_text(f"Enter the grade for {user_data['current_subject']} - TP :", parse_mode='HTML')
        return TP
    else:
        return receive_tp_grade(update, context)

def receive_tp_grade(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    grade = update.message.text

    if user_data['current_subject'] in tp_subjects:
        if not validate_grade(grade):
            update.message.reply_text("Please enter a valid grade between 0 and 20.")
            return TP
        user_data['current_subject_grades'].append(float(grade))
    else:
        user_data['current_subject_grades'].append(None)

    if user_data['current_subject'] in (td_subjects and subject_with_cc):
        update.message.reply_text(f"Enter the grade for {user_data['current_subject']} - CC :", parse_mode='HTML')
        return TD
    elif user_data['current_subject'] in td_subjects:
        update.message.reply_text(f"Enter the grade for {user_data['current_subject']} - TD :", parse_mode='HTML')
        return TD
    else:
        return receive_td_grade(update, context)

def receive_td_grade(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    grade = update.message.text

    if user_data['current_subject'] in td_subjects:
        if not validate_grade(grade):
            update.message.reply_text("Please enter a valid grade between 0 and 20.")
            return TD
        user_data['current_subject_grades'].append(float(grade))
    else:
        user_data['current_subject_grades'].append(None)

    return calculate_subject_average(update, context)

def calculate_subject_average(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    specialization = user_data['specialization']
    level = user_data['level']
    subject = user_data['current_subject']
    grades = user_data['current_subject_grades']
    coefficient = specializations[specialization][level][subject]

    # Ensure there are no None values before summing
    grades = [grade for grade in grades if grade is not None]

    if specialization == 'sciences' and level == 'sciences1':
        if subject in ["chimie", "biophysique", "math"]:
            # TD + Exam1 + Exam2 / 3
            average = sum(grades[:3]) / 3
        elif subject == "géologie":
            # Exam1 + Exam2 + TP / 3
            average = sum(grades[:3]) / 3
        elif subject in ["cyto", "histo", "bv", "embryo"]:
            # 0.7 * Exam + 0.3 * TP
            average = 0.7 * grades[0] + 0.3 * grades[2]
            user_data['subject_grades'][subject] = average

            update.message.reply_text(
                f"<b>The average grade for {subject} is: {average:.2f}</b>",
                parse_mode='HTML'
            )

            if all(sub in user_data['subject_grades'] for sub in ["cyto", "histo", "bv", "embryo"]):
                # Calculate general biology average
                bio_average = sum(user_data['subject_grades'][sub] for sub in ["cyto", "histo", "bv", "embryo"]) / 4
                user_data['total_grades'] += bio_average * 6
                user_data['total_coefficients'] += 6
        else:
            # Single Exam subjects (info, tarbya)
            average = grades[0]

    elif specialization == 'sciences' and level == 'sciences2':
        if subject == "Génétique":
            # TD + Exam1 + Exam2 / 3
            average = sum(grades[:3]) / 3
        elif subject == "Psycho2":
            # Exam 1 *2 + TD / 3
            average = (grades[0]*2 + grades[2]) / 3
        elif subject in ["Botanique", "Microbiologie", "Paléontologie"]:
            # Exam1 + Exam2 + TP / 3
            average = sum(grades[:3]) / 3
        elif subject == "Zoologie":
            # (Exam1 + Exam2 + 0.5 * TP + 0.5 * TD) / 3
            average = (sum(grades[:2]) + (0.5 * grades[2] + 0.5 * grades[3])) / 3
        elif subject == "Biochimie":
            # (Exam1 + Exam2 + 0.75 * TP + 0.25 * TD) / 3
            average = (sum(grades[:2]) + (0.75 * grades[2] + 0.25 * grades[3])) / 3
        else:
            # Single Exam subjects (info, tarbya)
            average = grades[0]

    elif subject == "chemistry_education":
        average = (grades[0]*2 + grades[2])/3
    else:
        # Existing calculations for other specializations
        if len(grades) == 1:
            average = grades[0]
        elif len(grades) == 2:  # No TP or TD
            average = sum(grades) / 2
        elif len(grades) == 3:  # TP or TD only
            average = sum(grades) / 3
        elif len(grades) == 4:
            if (specialization == 'physics' and level == 'physics3 (+4)') or (specialization == 'info' and (level == 'info2' or level== 'info3')):
                # Exam1 + Exam2 + (TP * 0.5 + TD * 0.5) / 3
                average = (sum(grades[:2]) + (grades[2] * 0.5 + grades[3] * 0.5)) / 3
            else:
                # Both TP and TD
                average = (sum(grades[:2]) + (2 * grades[2] + grades[3]) / 3) / 3

    # Print the average grade for the current subject if not handled by the specific subjects block
    if subject not in ["cyto", "histo", "bv", "embryo"]:
        update.message.reply_text(
            f"<b>The average grade for {subject} is: {average:.2f}</b>",
            parse_mode='HTML'
        )

        user_data['total_grades'] += average * coefficient
        user_data['total_coefficients'] += coefficient

    user_data['current_subject_index'] += 1
    return ask_for_grades(update, context)

def receive_subject_average(update: Update, context: CallbackContext) -> int:
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

def help_command(update: Update, context: CallbackContext) -> None:
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
    count = db.get_visitor_count()
    update.message.reply_text(f"The bot has been visited by {count + 600} unique users.")

def overall_average_count(update: Update, context: CallbackContext) -> None:
    count = db.get_overall_average_count()
    update.message.reply_text(f"The Bot has been used {count + 1530} times.")

def show_user_ids(update: Update, context: CallbackContext) -> None:
    user_ids = db.get_all_user_ids()
    update.message.reply_text(f"Collected user IDs: {', '.join(map(str, user_ids))}")

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Operation cancelled.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def whatsnew(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(MESSAGE_whatsnew, parse_mode='HTML')
    update.message.reply_text(MESSAGE_AR_whatsnew, parse_mode='HTML')

# إعدادات البوت و webhook
BOT_TOKEN = "7163691593:AAFmVnHxBgH4ORZ9ohTC9QQpiDmKjWTaMEI"
WEBHOOK_HOST = "ens-average-bot-599688285140.europe-west1.run.app"
WEBHOOK_URL_PATH = BOT_TOKEN
WEBHOOK_URL = f"https://{WEBHOOK_HOST}/{WEBHOOK_URL_PATH}"

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)
dispatcher = Dispatcher(bot, None, workers=4, use_context=True)

# إرسال رسالة ترحيبية عند بدء التشغيل
ADMIN_ID = 5909420341
try:
    bot.send_message(chat_id=ADMIN_ID, text="✅ Bot has started successfully on Cloud Run!")
except Exception as e:
    print(f"Failed to send startup message: {e}")

def main() -> None:
    global db
    db = Database(DB_PATH)

    # handlers
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SPECIALIZATION: [MessageHandler(Filters.text & ~Filters.command, choose_specialization)],
            LEVEL: [MessageHandler(Filters.text & ~Filters.command, choose_level)],
            SUB_LEVEL: [MessageHandler(Filters.text & ~Filters.command, choose_sub_level)],
            FIRST: [MessageHandler(Filters.text & ~Filters.command, receive_first_grade)],
            SECOND: [MessageHandler(Filters.text & ~Filters.command, receive_second_grade)],
            TP: [MessageHandler(Filters.text & ~Filters.command, receive_tp_grade)],
            TD: [MessageHandler(Filters.text & ~Filters.command, receive_td_grade)],
            NEXT_SUBJECT: [MessageHandler(Filters.text & ~Filters.command, receive_subject_average)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("visitor_count", visitor_count))
    dispatcher.add_handler(CommandHandler("usage_count", overall_average_count))
    dispatcher.add_handler(CommandHandler("showUserIDs", show_user_ids))
    dispatcher.add_handler(CommandHandler("whats_new", whatsnew))

    # تعيين الـ webhook عند التشغيل
    bot.set_webhook(url=WEBHOOK_URL)
    print(f"Webhook set to: {WEBHOOK_URL}")

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

if __name__ == '__main__':
    main()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

