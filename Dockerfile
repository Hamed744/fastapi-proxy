# از یک ایمیج پایه پایتون استفاده کن
FROM python:3.9-slim

# دایرکتوری کاری را در کانتینر تنظیم کن
WORKDIR /code

# فایل‌های نیازمندی‌ها را کپی و نصب کن
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# تمام کدهای اپلیکیشن را کپی کن
COPY . /code/

# دستوری که برای اجرای اپلیکیشن باید اجرا شود
# اپلیکیشن را روی پورت 7860 اجرا می‌کند که پورت استاندارد هاگینگ فیس است
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
