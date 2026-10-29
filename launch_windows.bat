@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
    echo Python 3 was not found. Install Python from https://www.python.org/downloads/windows/
    echo During installation, enable the option to add Python to PATH.
    pause
    exit /b 1
)

if not exist .venv (
    py -3 -m venv .venv
    if errorlevel 1 goto :error
    call .venv\Scripts\activate.bat
    python -m pip install -r requirements.txt
    if errorlevel 1 goto :error
) else (
    call .venv\Scripts\activate.bat
)

python app.py
if errorlevel 1 goto :error
exit /b 0

:error
echo.
echo Startup failed. Read the error above and check the README.md file.
pause
exit /b 1
