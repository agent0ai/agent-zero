@echo off
setlocal

:: Check if Ollama is already running
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel%==0 (
    echo ✅ Ollama is already running.
    pause
    exit /b 0
)

:: Start Ollama (assumes Ollama is installed and added to PATH)
echo 🚀 Starting Ollama server...
start "" /B "C:\Program Files\Ollama\ollama.exe" serve

:: Give it a few seconds to spin up
timeout /t 5 >nul

:: Verify it started
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel%==0 (
    echo ✅ Ollama started successfully.
) else (
    echo ❌ Failed to start Ollama. Check that Ollama is installed and in your PATH.
)

pause
endlocal
