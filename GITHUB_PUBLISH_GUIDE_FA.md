# راهنمای انتشار پروژه در GitHub

## نام پیشنهادی Repository

`SANA-Price-Monitoring`

## Description پیشنهادی

`Desktop market price monitoring and historical analysis system built with Python, PySide6, Playwright and SQLite.`

## Topics پیشنهادی

`python`, `pyside6`, `playwright`, `sqlite`, `desktop-app`, `web-scraping`, `price-monitoring`, `data-analysis`, `persian`, `portfolio-project`

## مراحل انتشار از طریق Git

1. در GitHub یک Repository جدید با نام `SANA-Price-Monitoring` بسازید.
2. گزینه‌های افزودن README و .gitignore را در GitHub فعال نکنید، چون داخل این پوشه آماده شده‌اند.
3. داخل پوشه پروژه Terminal / PowerShell باز کنید.
4. دستورات زیر را اجرا کنید و `YOUR_USERNAME` را با نام کاربری GitHub خودتان جایگزین کنید:

```bash
git init
git add .
git commit -m "Initial portfolio release"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/SANA-Price-Monitoring.git
git push -u origin main
```

## بعد از Push

- در بخش About، Description و Topics بالا را وارد کنید.
- 4 تا 6 اسکرین‌شات تمیز به `docs/screenshots/` اضافه کنید.
- Repository را Pin کنید تا بالای پروفایل GitHub دیده شود.
- لینک Repository را در رزومه و LinkedIn قرار دهید.
- در صورت داشتن مالکیت کامل حقوقی روی کد، می‌توانید بعداً یک License مناسب مثل MIT اضافه کنید. بدون اطمینان از مالکیت، License متن‌باز اضافه نکنید.

## نکته مهم

این بسته Portfolio Edition است. دارایی‌های سازمانی، فایل‌های طراحی اولیه، نسخه‌های Legacy و Credential ثابت از نسخه عمومی حذف شده‌اند. قبل از Public کردن نسخه دیگری از پروژه، حتماً دوباره Secret Scan انجام دهید.
