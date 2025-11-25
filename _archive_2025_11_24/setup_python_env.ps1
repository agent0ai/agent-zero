# PowerShell script for Python environment setup on Windows
# This replaces the need for pyenv on Windows

# Check if virtual environment exists
if (Test-Path ".\venv") {
    Write-Host "Virtual environment already exists. Activating..." -ForegroundColor Green
    .\venv\Scripts\Activate.ps1
} else {
    Write-Host "Creating new virtual environment..." -ForegroundColor Yellow
    python -m venv venv

    Write-Host "Activating virtual environment..." -ForegroundColor Green
    .\venv\Scripts\Activate.ps1

    Write-Host "Upgrading pip..." -ForegroundColor Yellow
    python -m pip install --upgrade pip

    Write-Host "Installing requirements..." -ForegroundColor Yellow
    if (Test-Path "requirements.txt") {
        pip install -r requirements.txt
    } else {
        Write-Host "No requirements.txt found" -ForegroundColor Red
    }
}

Write-Host "Python environment is ready!" -ForegroundColor Green
Write-Host "Python version:" -ForegroundColor Cyan
python --version
Write-Host "Pip version:" -ForegroundColor Cyan
pip --version