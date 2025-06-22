# استخدم صورة بايثون رسمية وخفيفة
FROM python:3.12-slim

# تعيين مجلد العمل داخل الحاوية
WORKDIR /app

# نسخ ملف المتطلبات وتثبيت الحزم
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# نسخ جميع ملفات المشروع
COPY . .

# الأمر لتشغيل uvicorn
# سيقوم بتشغيل الكائن 'application' من ملف 'main.py'
# سيستمع على جميع الواجهات على المنفذ المحدد من PORT أو 8080
CMD ["uvicorn", "main:application", "--host", "0.0.0.0", "--port", "8080"] 
