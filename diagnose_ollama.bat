@echo off
echo ==========================================
echo Ollama Diagnostic Tool
echo ==========================================
echo.

echo 1. Checking if Ollama is running...
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo    ✅ Ollama process is running
) else (
    echo    ❌ Ollama is not running
    echo    Try: Start Ollama from Start Menu
    pause
    exit /b 1
)

echo.
echo 2. Checking Ollama service...
sc query OllamaService 2>NUL
if errorlevel 1 (
    echo    ⚠️ Ollama service not found
    echo    This is normal - Ollama may run as an app
) else (
    echo    ✅ Ollama service exists
)

echo.
echo 3. Testing connection to localhost:11434...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:11434/api/tags' -UseBasicParsing -TimeoutSec 2; Write-Host '   ✅ Ollama API is responding'; Write-Host '   Models:'; ($response.Content | ConvertFrom-Json).models | ForEach-Object { Write-Host \"      - $($_.name)\" } } catch { Write-Host '   ❌ Cannot connect to Ollama API'; Write-Host '   Error:' $_.Exception.Message }"

echo.
echo 4. Checking for Ollama in common locations...
if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
    echo    ✅ Found: %LOCALAPPDATA%\Programs\Ollama\ollama.exe
    set OLLAMA_PATH=%LOCALAPPDATA%\Programs\Ollama
) else if exist "%ProgramFiles%\Ollama\ollama.exe" (
    echo    ✅ Found: %ProgramFiles%\Ollama\ollama.exe
    set OLLAMA_PATH=%ProgramFiles%\Ollama
) else (
    echo    ⚠️ Ollama executable not found in common locations
)

echo.
echo 5. Suggested fixes:
echo    a) Restart Ollama: Close it completely and reopen
echo    b) Check Windows Firewall: Allow Ollama
echo    c) Try running: ollama serve
echo    d) Reinstall Ollama if issues persist
echo.

pause
