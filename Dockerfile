# استخدم صورة بايثون رسمية وخفيفة
FROM python:3.12-slim

# تعيين مجلد العمل داخل الحاوية
WORKDIR /app

# نسخ ملف المتطلبات وتثبيت الحزم
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# نسخ جميع ملفات المشروع
COPY . .

# تحديد الأمر الافتراضي لتشغيل البوت
CMD ["python", "main.py"] 