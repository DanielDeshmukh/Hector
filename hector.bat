@echo off
REM HECTOR CLI Launcher for Windows
REM Usage: hector <command> [options]

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%"
set "VENV_PYTHON=%PROJECT_DIR%venv\Scripts\python.exe"

cd /d "%PROJECT_DIR%"

if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" "%PROJECT_DIR%main.py" %*
    exit /b %errorlevel%
)

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Expected "%VENV_PYTHON%" or a global Python 3.9+ installation.
    exit /b 1
)

python "%PROJECT_DIR%main.py" %*
