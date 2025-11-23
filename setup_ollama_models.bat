@echo off
setlocal enabledelayedexpansion
echo ==========================================
echo Ollama Model Setup for Agent Zero
echo ==========================================
echo.

set OLLAMA_EXE=C:\Users\andre_wjgj23f\AppData\Local\Programs\Ollama\ollama.exe

echo This will download the following models:
echo   1. llama3.2:3b (Chat - 2GB)
echo   2. llama3.2:1b (Utility - 1.3GB)
echo   3. nomic-embed-text (Embeddings - 274MB)
echo.
echo Total download: ~3.6GB
echo.
choice /C YN /M "Continue with download"
if errorlevel 2 goto :cancel

echo.
echo ==========================================
echo Downloading Models (this may take a while)
echo ==========================================

echo.
echo [1/3] Pulling llama3.2:3b (Chat model)...
"%OLLAMA_EXE%" pull llama3.2:3b
if errorlevel 1 (
    echo ❌ Failed to pull llama3.2:3b
    goto :error
)

echo.
echo [2/3] Pulling llama3.2:1b (Utility model)...
"%OLLAMA_EXE%" pull llama3.2:1b
if errorlevel 1 (
    echo ❌ Failed to pull llama3.2:1b
    goto :error
)

echo.
echo [3/3] Pulling nomic-embed-text (Embeddings)...
"%OLLAMA_EXE%" pull nomic-embed-text
if errorlevel 1 (
    echo ❌ Failed to pull nomic-embed-text
    goto :error
)

echo.
echo ==========================================
echo ✅ All models downloaded successfully!
echo ==========================================
echo.
echo Installed models:
"%OLLAMA_EXE%" list

echo.
echo Next steps:
echo   1. Run: python optimize_antigravity.py
echo   2. Run: python test_ollama.py
echo   3. Run: .\restart_agent_zero.bat
echo.
pause
exit /b 0

:cancel
echo.
echo ❌ Setup cancelled
pause
exit /b 1

:error
echo.
echo ❌ An error occurred during setup
echo.
echo Troubleshooting:
echo   - Check your internet connection
echo   - Ensure Ollama server is running
echo   - Try running: .\start_ollama.bat
echo.
pause
exit /b 1
