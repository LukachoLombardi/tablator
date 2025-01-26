@echo off

:: Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python 3.
    exit /b 1
)

:: Install dependencies from requirements.txt
if exist "requirements.txt" (
    python -m pip install -r requirements.txt
) else (
    echo requirements.txt not found.
    exit /b 1
)

:: Run the main script
python src\main.py