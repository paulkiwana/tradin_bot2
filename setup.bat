@echo off
echo ============================================
echo Crypto Monitor Setup
echo ============================================
echo.

echo Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)
echo.

echo Installing required packages...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

echo Creating .env file from template...
if not exist .env (
    copy .env.example .env
    echo .env file created! Please edit it to configure your settings.
) else (
    echo .env file already exists, skipping...
)
echo.

echo ============================================
echo Setup Complete!
echo ============================================
echo.
echo Next steps:
echo 1. Edit .env file to configure your cryptocurrency symbols
echo 2. Run start_gui.bat to launch the GUI version
echo    OR run start_monitor.bat for console version
echo.
pause
