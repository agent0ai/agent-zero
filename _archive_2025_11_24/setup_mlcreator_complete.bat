@echo off
setlocal enabledelayedexpansion

echo =========================================================
echo    Agent Zero - MLcreator Project Complete Setup
echo =========================================================
echo.

:: Check if we're in the right directory
if not exist "agent.py" (
    echo ERROR: This script must be run from the Agent Zero root directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

:: Set variables
set AGENT_ZERO_PATH=%CD%
set MLCREATOR_PATH=D:\GithubRepos\MLcreator
set MEMORY_DIR=%AGENT_ZERO_PATH%\memory\mlcreator
set KNOWLEDGE_DIR=%AGENT_ZERO_PATH%\knowledge\mlcreator
set PROMPTS_DIR=%AGENT_ZERO_PATH%\prompts\mlcreator
set INSTRUMENTS_DIR=%AGENT_ZERO_PATH%\instruments\mlcreator

echo [1/8] Checking MLcreator project...
if not exist "%MLCREATOR_PATH%" (
    echo ERROR: MLcreator project not found at %MLCREATOR_PATH%
    pause
    exit /b 1
)
echo ✓ MLcreator project found

echo.
echo [2/8] Creating directory structure...

:: Create all necessary directories
mkdir "%MEMORY_DIR%" 2>nul
mkdir "%MEMORY_DIR%\db" 2>nul
mkdir "%MEMORY_DIR%\embeddings" 2>nul

mkdir "%KNOWLEDGE_DIR%" 2>nul
mkdir "%KNOWLEDGE_DIR%\main" 2>nul
mkdir "%KNOWLEDGE_DIR%\fragments" 2>nul
mkdir "%KNOWLEDGE_DIR%\solutions" 2>nul
mkdir "%KNOWLEDGE_DIR%\instruments" 2>nul

mkdir "%PROMPTS_DIR%" 2>nul
mkdir "%INSTRUMENTS_DIR%" 2>nul

echo ✓ Directory structure created

echo.
echo [3/8] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10 or higher
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo ✓ Python %PYTHON_VER% found

echo.
echo [4/8] Installing Python dependencies...
pip install -q --upgrade pip
if errorlevel 1 (
    echo WARNING: Could not upgrade pip
)

:: Check for key dependencies
pip show langchain >nul 2>&1
if errorlevel 1 (
    echo Installing missing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        echo Please run: pip install -r requirements.txt
        pause
        exit /b 1
    )
)
echo ✓ Dependencies verified

echo.
echo [5/8] Populating knowledge base...
if exist "populate_mlcreator_knowledge.py" (
    python populate_mlcreator_knowledge.py
    if errorlevel 1 (
        echo WARNING: Knowledge population had issues
    ) else (
        echo ✓ Knowledge base populated
    )
) else (
    echo WARNING: populate_mlcreator_knowledge.py not found
    echo Please run it manually later
)

echo.
echo [6/8] Initializing memory database...
if exist "init_mlcreator_memory.py" (
    python init_mlcreator_memory.py
    if errorlevel 1 (
        echo WARNING: Memory initialization had issues
    ) else (
        echo ✓ Memory database initialized
    )
) else (
    echo WARNING: init_mlcreator_memory.py not found
    echo Please run it manually later
)

echo.
echo [7/8] Updating configuration files...

:: Check if .env exists, create from example if not
if not exist ".env" (
    if exist "example.env" (
        copy "example.env" ".env" >nul
        echo ✓ Created .env from example
    ) else (
        echo WARNING: No .env file found. Please create one manually
    )
) else (
    echo ✓ .env file exists
)

:: Add MLcreator settings to .env if not present
findstr /C:"MEMORY_SUBDIR=mlcreator" .env >nul
if errorlevel 1 (
    echo.>> .env
    echo # MLcreator Project Settings>> .env
    echo MEMORY_SUBDIR=mlcreator>> .env
    echo KNOWLEDGE_SUBDIRS=mlcreator>> .env
    echo PROJECT_PATH=%MLCREATOR_PATH%>> .env
    echo ✓ Added MLcreator settings to .env
) else (
    echo ✓ MLcreator settings already in .env
)

echo.
echo [8/8] Creating quick start scripts...

:: Create run script
echo @echo off > run_mlcreator.bat
echo echo Starting Agent Zero for MLcreator... >> run_mlcreator.bat
echo set MEMORY_SUBDIR=mlcreator >> run_mlcreator.bat
echo python run_ui.py >> run_mlcreator.bat

echo ✓ Created run_mlcreator.bat

:: Create status check script
echo @echo off > check_mlcreator_status.bat
echo echo Checking MLcreator setup status... >> check_mlcreator_status.bat
echo echo. >> check_mlcreator_status.bat
echo if exist "%MEMORY_DIR%" (echo ✓ Memory directory exists) else (echo ✗ Memory directory missing) >> check_mlcreator_status.bat
echo if exist "%KNOWLEDGE_DIR%" (echo ✓ Knowledge directory exists) else (echo ✗ Knowledge directory missing) >> check_mlcreator_status.bat
echo if exist "%PROMPTS_DIR%\CLAUDE.md" (echo ✓ CLAUDE.md configured) else (echo ✗ CLAUDE.md missing) >> check_mlcreator_status.bat
echo if exist "%PROMPTS_DIR%\AGENTS.md" (echo ✓ AGENTS.md configured) else (echo ✗ AGENTS.md missing) >> check_mlcreator_status.bat
echo dir /b "%KNOWLEDGE_DIR%\main" 2^>nul ^| find /c /v "" ^> temp.txt >> check_mlcreator_status.bat
echo set /p KNOW_COUNT=^<temp.txt >> check_mlcreator_status.bat
echo del temp.txt >> check_mlcreator_status.bat
echo echo ✓ Knowledge files: %%KNOW_COUNT%% >> check_mlcreator_status.bat
echo pause >> check_mlcreator_status.bat

echo ✓ Created check_mlcreator_status.bat

echo.
echo =========================================================
echo    ✅ SETUP COMPLETE!
echo =========================================================
echo.
echo 📁 Project Directories Created:
echo    - Memory: %MEMORY_DIR%
echo    - Knowledge: %KNOWLEDGE_DIR%
echo    - Prompts: %PROMPTS_DIR%
echo    - Instruments: %INSTRUMENTS_DIR%
echo.
echo 🚀 Quick Start:
echo    1. Run: run_mlcreator.bat
echo    2. Open: http://localhost:5000
echo    3. Check settings for "mlcreator" memory
echo.
echo 📊 Status Check:
echo    Run: check_mlcreator_status.bat
echo.
echo 🔧 Manual Steps Required:
echo    1. Add your API keys to .env file
echo    2. Configure MCP servers if needed
echo    3. Test Unity integration
echo.
echo 💡 Tips:
echo    - Memory auto-recall is configured for every 3 messages
echo    - Use appropriate activation scripts in MLcreator:
echo      * activate-unity.ps1 for Unity work
echo      * activate-ai.ps1 for ML training
echo    - All Game Creator patterns are in memory
echo.
echo =========================================================

pause