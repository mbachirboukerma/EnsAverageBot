import math
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from retrying import retry
from telegram.error import TimedOut
from specializations import specializations, exam1_subjects, exam2_subjects, td_subjects, tp_subjects, subject_with_cc, special_subjects, levelsWithSubLevels

# تعريف حالات المحادثة
SPECIALIZATION, LEVEL, SUB_LEVEL, FIRST, SECOND, TP, TD, NEXT_SUBJECT = range(8)

def validate_grade(grade: str) -> bool:
    """التحقق من صحة الدرجة المدخلة"""
    try:
        value = float(grade)
        return 0 <= value <= 20
    except ValueError:
        return False

def get_menu_keyboard():
    """إنشاء لوحة المفاتيح للقائمة"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Follow us on facebook", url='https://m.facebook.com/hqlaptop')],
        [InlineKeyboardButton("Follow us on Instagram", url='https://www.instagram.com/Hq.laptop')]
    ])

@retry(wait_fixed=2000, stop_max_attempt_number=5, retry_on_exception=lambda x: isinstance(x, TimedOut))
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بدء البوت والتحقق من الاشتراك"""
    from error_handler import is_subscribed, CHANNELS
    
    user_id = update.message.from_user.id
    context.db.update_visitors(user_id)

    # 🔹 التحقق من الاشتراك في جميع القنوات
    if not await is_subscribed(update, context):
        keyboard = [[InlineKeyboardButton(f"📢 اشترك في {channel}", url=f"https://t.me/{channel[1:]}")] for channel in CHANNELS]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "❌ يجب عليك الاشتراك في القنوات التالية لاستخدام البوت:\n\n"
            f"1️⃣ {CHANNELS[0]}\n"
            f"2️⃣ {CHANNELS[1]}\n\n"
            "🔹 بعد الاشتراك، اضغط على /start من جديد.",
            reply_markup=reply_markup
        )
        return ConversationHandler.END

    # ✅ المستخدم مشترك في القنوات، يكمل العملية
    keyboard = [
        ["Math"],
        ["Physics"],
        ["Info"],
        ["Sciences"],
        ["Musique"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text(
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

async def choose_specialization(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """اختيار التخصص"""
    user_data = context.user_data
    specialization = update.message.text.lower()

    if specialization not in specializations:
        await update.message.reply_text("Please choose a valid specialization.")
        return SPECIALIZATION

    user_data['specialization'] = specialization
    keyboard = [[f"{specialization.capitalize()}1"], [f"{specialization.capitalize()}2"], [f"{specialization.capitalize()}3"], [f"{specialization.capitalize()}4"],[f"{specialization.capitalize()}5"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Please choose your level:", reply_markup=reply_markup)
    return LEVEL

async def choose_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """اختيار المستوى"""
    user_data = context.user_data
    level = update.message.text.lower()

    not_added_levels = [ "sciences4 (+4)", "sciences4 (+5)", "sciences5",
                    "physics4 (+4)", "physics5",
                    "math4 (+4)", "math5",
                    "info5"]
    not_supported_levels = ["musique1", "musique2", "musique3", "musique4 (+4)", "musique4 (+5)", "musique5"]

    if level in not_added_levels:
        await update.message.reply_text("لم يتم اضافة هذا التخصص بعد، يرجى الانتظار.")
        await update.message.reply_text("This level is not listed yet, Please wait for upcoming updates.")
        return ConversationHandler.END

    if level in not_supported_levels:
        await update.message.reply_text("<b>هذا التخصص لن يتم دعمه.</b>", parse_mode='HTML')
        await update.message.reply_text(
            "الحمد لله، والصلاة والسلام على رسول الله، وعلى آله، وصحبه، أما بعد:\n\n"
            "فالموسيقى لا تجوز دراستها، ولا تدريسها للكبار، ولا للصغار، وراجع في ذلك الفتاوى ذوات الأرقام التالية: "
            "<a href=\"https://www.islamweb.net/ar/fatwa/7932/\">7932</a>، "
            "<a href=\"https://www.islamweb.net/ar/fatwa/73834/\">73834</a>، "
            "<a href=\"https://www.islamweb.net/ar/fatwa/191797/\">المصدر</a>"
        , parse_mode='HTML')
        return ConversationHandler.END

    specialization = user_data['specialization']
    if level in levelsWithSubLevels:
        user_data['level_base'] = level
        keyboard = [["+4"], ["+5"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        await update.message.reply_text("Please choose your sub-level:", reply_markup=reply_markup)
        return SUB_LEVEL

    if level not in specializations[specialization]:
        await update.message.reply_text("Please choose a valid level.")
        return LEVEL

    user_data['level'] = level
    user_data['current_subject_index'] = 0
    user_data['subject_grades'] = {}
    user_data['total_grades'] = 0
    user_data['total_coefficients'] = 0

    return await ask_for_grades(update, context)

async def choose_sub_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """اختيار المستوى الفرعي"""
    user_data = context.user_data
    sub_level = update.message.text.lower()
    not_added_levels = ["sciences4 (+4)", "sciences4 (+5)", "sciences5",
                    "physics4 (+4)", "physics5",
                    "math4 (+4)", "math5",
                    "info5"]
    if sub_level not in ["+4", "+5"]:
        await update.message.reply_text("Please choose a valid sub-level.")
        return SUB_LEVEL

    level_base = user_data['level_base']
    if sub_level == "+4":
        if f"{level_base} (+4)" in not_added_levels:
            await update.message.reply_text("لم يتم اضافة هذا التخصص بعد، يرجى الانتظار.")
            await update.message.reply_text("This level is not listed yet, Please wait for upcoming updates.")
            return ConversationHandler.END
        user_data['level'] = f"{level_base} (+4)"
    elif sub_level == "+5":
        if f"{level_base} (+5)" in not_added_levels:
            await update.message.reply_text("لم يتم اضافة هذا التخصص بعد، يرجى الانتظار.")
            await update.message.reply_text("This level is not listed yet, Please wait for upcoming updates.")
            return ConversationHandler.END
        user_data['level'] = f"{level_base} (+5)"

    user_data['current_subject_index'] = 0
    user_data['subject_grades'] = {}
    user_data['total_grades'] = 0
    user_data['total_coefficients'] = 0

    return await ask_for_grades(update, context)

async def ask_for_grades(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """طلب الدرجات من المستخدم"""
    user_data = context.user_data
    specialization = user_data['specialization']
    level = user_data['level']
    subjects = list(specializations[specialization][level].keys())
    current_index = user_data.get('current_subject_index', 0)

    if current_index >= len(subjects):
        if user_data['total_coefficients'] == 0:
            await update.message.reply_text("No subjects found for this level.")
            return ConversationHandler.END

        average = user_data['total_grades'] / user_data['total_coefficients']
        context.db.increment_overall_average_count()
        await update.message.reply_text("<b>---------------------------------------------</b>", parse_mode='HTML')
        average = math.ceil(average * 100) / 100
        await update.message.reply_text(f"<b>Your overall average grade is: <span class=\"tg-spoiler\">{average:.2f}</span></b>", parse_mode='HTML')

        if average >= 10.00:
            await update.message.reply_text("<b><span class=\"tg-spoiler\">Congratulations!! YA LKHABACH</span></b>", parse_mode='HTML')
        else:
            await update.message.reply_text("<b><span class=\"tg-spoiler\">Don't worry, Rana ga3 f rattrapage.</span></b>", parse_mode='HTML')

        await update.message.reply_text(
            "<b>Thank you for using our bot</b>\n\n"
            "<b>Developed by <a href=\"https://www.instagram.com/yassine_boukerma\">Yassine Boukerma</a> with ❤️</b>",
            reply_markup=get_menu_keyboard(),
            parse_mode='HTML'
        )

        return ConversationHandler.END

    subject = subjects[current_index]
    coefficient = specializations[specialization][level][subject]
    
    if subject in special_subjects:
        await update.message.reply_text(
            f"Please enter your average grade for <b>{subject}</b> (coefficient: {coefficient}):",
            parse_mode='HTML'
        )
        return NEXT_SUBJECT
    
    if subject in exam1_subjects and subject in exam2_subjects:
        await update.message.reply_text(
            f"Please enter your first exam grade for <b>{subject}</b> (coefficient: {coefficient}):",
            parse_mode='HTML'
        )
        return FIRST
    else:
        await update.message.reply_text(
            f"Please enter your exam grade for <b>{subject}</b> (coefficient: {coefficient}):",
            parse_mode='HTML'
        )
        return FIRST

async def receive_first_grade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال الدرجة الأولى"""
    user_data = context.user_data
    grade_text = update.message.text
    
    if not validate_grade(grade_text):
        await update.message.reply_text("Please enter a valid grade between 0 and 20.")
        return FIRST
    
    grade = float(grade_text)
    specialization = user_data['specialization']
    level = user_data['level']
    subjects = list(specializations[specialization][level].keys())
    current_index = user_data.get('current_subject_index', 0)
    subject = subjects[current_index]
    
    if subject in exam1_subjects and subject in exam2_subjects:
        user_data['first_grade'] = grade
        await update.message.reply_text(f"Please enter your second exam grade for <b>{subject}</b>:", parse_mode='HTML')
        return SECOND
    else:
        coefficient = specializations[specialization][level][subject]
        user_data.setdefault('total_grades', 0)
        user_data.setdefault('total_coefficients', 0)
        user_data['total_grades'] += grade * coefficient
        user_data['total_coefficients'] += coefficient
        user_data['current_subject_index'] = current_index + 1
        return await ask_for_grades(update, context)

async def receive_second_grade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال الدرجة الثانية"""
    user_data = context.user_data
    grade_text = update.message.text
    
    if not validate_grade(grade_text):
        await update.message.reply_text("Please enter a valid grade between 0 and 20.")
        return SECOND
    
    grade = float(grade_text)
    first_grade = user_data['first_grade']
    average = (first_grade + grade) / 2
    
    specialization = user_data['specialization']
    level = user_data['level']
    subjects = list(specializations[specialization][level].keys())
    current_index = user_data.get('current_subject_index', 0)
    subject = subjects[current_index]
    coefficient = specializations[specialization][level][subject]
    
    user_data.setdefault('total_grades', 0)
    user_data.setdefault('total_coefficients', 0)
    user_data['total_grades'] += average * coefficient
    user_data['total_coefficients'] += coefficient
    user_data['current_subject_index'] = current_index + 1
    
    return await ask_for_grades(update, context)

async def receive_tp_grade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال درجة TP"""
    # This logic seems incomplete, assuming a simple addition for now
    user_data = context.user_data
    grade_text = update.message.text
    if not validate_grade(grade_text):
        await update.message.reply_text("Please enter a valid grade between 0 and 20.")
        return TP
    
    grade = float(grade_text)
    specialization = user_data['specialization']
    level = user_data['level']
    subjects = list(specializations[specialization][level].keys())
    current_index = user_data.get('current_subject_index', 0)
    subject = subjects[current_index]
    coefficient = specializations[specialization][level][subject]
    
    user_data.setdefault('total_grades', 0)
    user_data.setdefault('total_coefficients', 0)
    user_data['total_grades'] += grade * coefficient
    user_data['total_coefficients'] += coefficient
    user_data['current_subject_index'] = current_index + 1
    
    return await ask_for_grades(update, context)

async def receive_td_grade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال درجة TD"""
    # This logic seems incomplete, assuming a simple addition for now
    user_data = context.user_data
    grade_text = update.message.text
    if not validate_grade(grade_text):
        await update.message.reply_text("Please enter a valid grade between 0 and 20.")
        return TD
    
    grade = float(grade_text)
    specialization = user_data['specialization']
    level = user_data['level']
    subjects = list(specializations[specialization][level].keys())
    current_index = user_data.get('current_subject_index', 0)
    subject = subjects[current_index]
    coefficient = specializations[specialization][level][subject]
    
    user_data.setdefault('total_grades', 0)
    user_data.setdefault('total_coefficients', 0)
    user_data['total_grades'] += grade * coefficient
    user_data['total_coefficients'] += coefficient
    user_data['current_subject_index'] = current_index + 1
    
    return await ask_for_grades(update, context)

async def receive_subject_average(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال متوسط المادة"""
    user_data = context.user_data
    grade_text = update.message.text
    
    if not validate_grade(grade_text):
        await update.message.reply_text("Please enter a valid grade between 0 and 20.")
        return NEXT_SUBJECT
    
    grade = float(grade_text)
    specialization = user_data['specialization']
    level = user_data['level']
    subjects = list(specializations[specialization][level].keys())
    current_index = user_data.get('current_subject_index', 0)
    subject = subjects[current_index]
    coefficient = specializations[specialization][level][subject]
    
    user_data.setdefault('total_grades', 0)
    user_data.setdefault('total_coefficients', 0)
    user_data['total_grades'] += grade * coefficient
    user_data['total_coefficients'] += coefficient
    user_data['current_subject_index'] = current_index + 1
    
    return await ask_for_grades(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """إلغاء العملية"""
    await update.message.reply_text(
        "Operation cancelled. Type /start to begin again.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END 
