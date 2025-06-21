import math
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext, ConversationHandler
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
def start(update: Update, context: CallbackContext, db) -> int:
    """بدء البوت والتحقق من الاشتراك"""
    from error_handler import is_subscribed, CHANNELS
    
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
    return SPECIALIZATION

def choose_specialization(update: Update, context: CallbackContext) -> int:
    """اختيار التخصص"""
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

def choose_level(update: Update, context: CallbackContext) -> int:
    """اختيار المستوى"""
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
            "<a href=\"https://www.islamweb.net/ar/fatwa/73834/%D8%AD%D9%83%D9%85-%D8%A7%D9%84%D8%AF%D8%B1%D8%A7%D8%B3%D8%A9-%D9%81%D9%8A-%D9%83%D9%84%D9%8A%D9%87-%D9%85%D9%86-%D8%B6%D9%85%D9%86-%D9%85%D9%88%D8%A7%D8%AF%D9%87%D8%A7-%D9%84%D9%85%D9%88%D8%B3%D9%8A%D9%82%D9%89\">73834</a>، "
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

    return ask_for_grades(update, context, db)

def choose_sub_level(update: Update, context: CallbackContext) -> int:
    """اختيار المستوى الفرعي"""
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

    return ask_for_grades(update, context, db)

def ask_for_grades(update: Update, context: CallbackContext, db) -> int:
    """طلب الدرجات من المستخدم"""
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

def receive_first_grade(update: Update, context: CallbackContext) -> int:
    """استقبال الدرجة الأولى"""
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
    """استقبال الدرجة الثانية"""
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
    """استقبال درجة TP"""
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
    """استقبال درجة TD"""
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
    """حساب متوسط المادة"""
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
    return ask_for_grades(update, context, db)

def receive_subject_average(update: Update, context: CallbackContext) -> int:
    """استقبال متوسط المادة مباشرة"""
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
    return ask_for_grades(update, context, db)

def cancel(update: Update, context: CallbackContext) -> int:
    """إلغاء العملية"""
    update.message.reply_text('Operation cancelled.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END 
