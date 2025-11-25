@echo off
echo ==========================================
echo Setup Antigravity with GCP Resources
echo ==========================================
echo.
echo 1. Authenticating with Google Cloud...
echo    (A browser window will open for you to login)
call gcloud auth application-default login --scopes=https://www.googleapis.com/auth/cloud-platform
if errorlevel 1 (
    echo.
    echo ❌ Authentication failed. Please try again.
    pause
    exit /b 1
)

echo.
echo 2. Optimizing Antigravity Configuration...
python optimize_antigravity.py

if errorlevel 0 (
    echo.
    echo ==========================================
    echo ✅ SUCCESS: Antigravity is now optimized!
    echo ==========================================
) else (
    echo.
    echo ❌ Optimization failed. Check the errors above.
)

pause
