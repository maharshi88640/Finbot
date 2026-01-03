@echo off
REM FinBot Startup Script for Windows
title FinBot

echo 🏦 FinBot Startup Script
echo =======================

REM Check if virtual environment exists
if not exist "myenv" (
    echo ❌ Virtual environment not found. Please run setup first:
    echo    python -m venv myenv
    echo    myenv\Scripts\activate
    echo    pip install -r requirements.txt
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo ❌ .env file not found. Please create it with your API keys:
    echo    OPENAI_API_KEY=your_key_here
    echo    SUPABASE_URL=your_url_here
    echo    SUPABASE_KEY=your_key_here
    pause
    exit /b 1
)

echo ✅ Environment checks passed

:menu
echo.
echo What would you like to do?
echo 1) 🌐 Start Web Interface
echo 2) 📊 Check Database Status
echo 3) 🕷️ Scrape Sample Data
echo 4) 🧹 Clear Database
echo 5) ❌ Exit
echo.
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo 🌐 Starting FinBot Web Interface...
    myenv\Scripts\python.exe -m streamlit run main.py
    goto menu
)
if "%choice%"=="2" (
    echo 📊 Checking Database Status...
    myenv\Scripts\python.exe cli.py db status
    pause
    goto menu
)
if "%choice%"=="3" (
    echo 🕷️ Scraping Sample Data...
    myenv\Scripts\python.exe cli.py scrape --sample --branches 2 --records-per-branch 5
    pause
    goto menu
)
if "%choice%"=="4" (
    echo ⚠️  This will delete ALL data!
    set /p confirm="Are you sure? (y/N): "
    if /i "%confirm%"=="y" (
        myenv\Scripts\python.exe cli.py db clear --confirm
    ) else (
        echo ❌ Operation cancelled
    )
    pause
    goto menu
)
if "%choice%"=="5" (
    echo 👋 Goodbye!
    exit /b 0
)

echo ❌ Invalid choice. Please try again.
goto menu
