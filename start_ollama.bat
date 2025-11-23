@echo off
echo ==========================================
echo Starting Ollama Server
echo ==========================================
echo.

echo Looking for Ollama installation...

REM Check common installation paths
set OLLAMA_EXE=
if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
    set OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe
    echo Found: %LOCALAPPDATA%\Programs\Ollama\ollama.exe
) else if exist "%ProgramFiles%\Ollama\ollama.exe" (
    set OLLAMA_EXE=%ProgramFiles%\Ollama\ollama.exe
    echo Found: %ProgramFiles%\Ollama\ollama.exe
) else if exist "%USERPROFILE%\AppData\Local\Programs\Ollama\ollama.exe" (
    set OLLAMA_EXE=%USERPROFILE%\AppData\Local\Programs\Ollama\ollama.exe
    echo Found: %USERPROFILE%\AppData\Local\Programs\Ollama\ollama.exe
) else (
    echo ❌ Ollama not found!
    echo.
    echo Please install Ollama from: https://ollama.com/download
    echo Or run: winget install --id Ollama.Ollama
    pause
    exit /b 1
)

echo.
echo Starting Ollama server...
start "Ollama Server" "%OLLAMA_EXE%" serve

echo.
echo Waiting for server to start...
timeout /t 3 >nul

echo.
echo Testing connection...
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:11434/api/tags' -UseBasicParsing -TimeoutSec 5 | Out-Null; Write-Host '✅ Ollama server is running!' } catch { Write-Host '⚠️ Server may still be starting...' }"

echo.
echo ==========================================
echo Ollama server should now be running
echo Test it: python test_ollama.py
echo ==========================================
pause
