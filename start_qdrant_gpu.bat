@echo off
setlocal

:: -------------------------------------------------
:: 1️⃣  Verify Docker is running
:: -------------------------------------------------
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker does not appear to be running.
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

:: -------------------------------------------------
:: 2️⃣  Pull the latest Qdrant image (GPU‑enabled)
:: -------------------------------------------------
echo 📦 Pulling Qdrant image...
docker pull qdrant/qdrant:latest

:: -------------------------------------------------
:: 3️⃣  Stop any existing Qdrant container (named qdrant-gpu)
:: -------------------------------------------------
docker rm -f qdrant-gpu >nul 2>&1

:: -------------------------------------------------
:: 4️⃣  Run Qdrant with GPU support
:: -------------------------------------------------
echo 🚀 Starting Qdrant with GPU...
docker run -d ^
    --name qdrant-gpu ^
    --restart unless-stopped ^
    -p 6333:6333 ^
    -p 6334:6334 ^
    --gpus all ^
    -e QDRANT__SERVICE__GRPC_PORT=6334 ^
    -e QDRANT__SERVICE__HTTP_PORT=6333 ^
    -e QDRANT__STORAGE__DISK__CACHE_SIZE_MB=4096 ^
    qdrant/qdrant:latest

if errorlevel 1 (
    echo ❌ Failed to start the Qdrant container.
    pause
    exit /b 1
)

:: -------------------------------------------------
:: 5️⃣  Wait a few seconds for the service to be ready
:: -------------------------------------------------
echo ⏳ Waiting for Qdrant to become healthy...
timeout /t 5 >nul

:: -------------------------------------------------
:: 6️⃣  Verify the API is reachable
:: -------------------------------------------------
powershell -Command "try { $r = Invoke-WebRequest -Uri http://localhost:6333/health -UseBasicParsing -TimeoutSec 5; if ($r.StatusCode -eq 200) { Write-Host '✅ Qdrant is up and running (GPU enabled)'} else { Write-Host '⚠️ Qdrant responded but not healthy' } } catch { Write-Host '❌ Cannot reach Qdrant API' }"

pause
endlocal
