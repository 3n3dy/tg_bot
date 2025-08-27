@echo off
cd /d C:\Users\en3dy\tg_bot
call venv\Scripts\activate.bat
.\venv\Scripts\watchmedo auto-restart --pattern="*.py" --recursive -- python run.py
pause
