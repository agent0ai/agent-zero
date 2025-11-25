@echo off
echo ==========================================
echo Restarting Agent Zero with Fixed Models
echo ==========================================
echo.

echo 1. Stopping existing Agent Zero processes...
taskkill /F /FI "WINDOWTITLE eq Agent Zero*" 2>nul
timeout /t 2 >nul

echo 2. Verifying settings...
type tmp\settings.json | findstr "util_model_name"

echo.
echo 3. Restarting Agent Zero...
start "Agent Zero Backend" python agent.py

timeout /t 3 >nul

echo 4. Starting UI...
python run_ui.py

pause
