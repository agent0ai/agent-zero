@echo off
echo ==========================================
echo Launching Antigravity (Agent Zero)
echo ==========================================
echo.

echo 1. Checking environment...
if not exist ".env" (
    echo ⚠️ .env file not found!
    echo Creating default .env...
    echo VERTEX_PROJECT=andre-467020> .env
    echo VERTEX_LOCATION=us-central1>> .env
)

echo 2. Checking Qdrant...
docker ps | findstr "agent-zero-qdrant" >nul
if errorlevel 1 (
    echo ⚠️ Qdrant is not running. Starting it...
    docker-compose -f docker/run/docker-compose.qdrant.yml up -d
) else (
    echo ✅ Qdrant is running.
)

echo 3. Starting Agent Zero Backend...
start "Agent Zero Backend" python agent.py

echo 4. Starting Agent Zero UI...
echo.
echo    Access the UI at: http://localhost:5000
echo.
python run_ui.py

pause
