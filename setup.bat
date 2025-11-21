@echo off
REM Movie Reservation System - Setup Script for Windows

echo 🎬 Movie Reservation System Setup
echo ==================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.11+
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ Python found: %PYTHON_VERSION%

REM Backend setup
echo.
echo 📦 Setting up backend...

REM Create virtual environment
if not exist ".venv\" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat
echo ✅ Virtual environment activated

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo ✅ Dependencies installed

REM Run tests
echo.
echo 🧪 Running tests...
pytest tests/test_auth.py -v
echo ✅ Tests passed

REM Frontend setup
echo.
echo 📦 Setting up frontend...

cd frontend

REM Check if Node is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found. Please install Node.js 16+
    exit /b 1
)

for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo ✅ Node.js found: %NODE_VERSION%

REM Install dependencies
echo Installing npm dependencies...
call npm install
echo ✅ Frontend dependencies installed

cd ..

echo.
echo ==================================
echo ✅ Setup complete!
echo.
echo To start development:
echo.
echo Backend (open terminal in project root):
echo   .venv\Scripts\activate
echo   uvicorn app.main:app --reload
echo.
echo Frontend (open new terminal in project root):
echo   cd frontend
echo   npm run dev
echo.
echo API Documentation: http://localhost:8000/docs
echo Frontend: http://localhost:3000
echo.
echo 🎬 Happy booking!
pause
