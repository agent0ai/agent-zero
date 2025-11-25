@echo off
echo =====================================
echo MLcreator Memory Initialization
echo =====================================
echo.

cd /d D:\GithubRepos\agent-zero

echo Activating Python environment...
call python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

echo Running memory initialization...
python init_mlcreator_memory.py

if errorlevel 0 (
    echo.
    echo =====================================
    echo SUCCESS: Memory initialized!
    echo =====================================
) else (
    echo.
    echo =====================================
    echo ERROR: Memory initialization failed
    echo =====================================
)

pause
