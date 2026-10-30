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

if not exist ".venv\Scripts\python.exe" (
    echo Creating the project virtual environment...
    py -3 -m venv .venv
    if errorlevel 1 goto :error
)

set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"

echo Checking required packages...
"%PYTHON_EXE%" -c "import fitz; import docx; import reportlab" >nul 2>nul
if errorlevel 1 (
    echo Installing required packages from requirements.txt...
    "%PYTHON_EXE%" -m pip install -r requirements.txt
    if errorlevel 1 goto :error
)

echo Verifying package installation...
"%PYTHON_EXE%" -c "import fitz; import docx; import reportlab"
if errorlevel 1 goto :error

echo Starting Smart Exam Paper Generator...
"%PYTHON_EXE%" app.py
if errorlevel 1 goto :error
exit /b 0

:error
echo.
echo Startup failed. Check the error above and your internet connection.
echo You can also review README.md for troubleshooting.
pause
exit /b 1
