@echo off
REM Batch script for Python environment setup on Windows
REM This replaces the need for pyenv on Windows

if exist venv (
    echo Virtual environment already exists. Activating...
    call venv\Scripts\activate.bat
) else (
    echo Creating new virtual environment...
    python -m venv venv

    echo Activating virtual environment...
    call venv\Scripts\activate.bat

    echo Upgrading pip...
    python -m pip install --upgrade pip

    echo Installing requirements...
    if exist requirements.txt (
        pip install -r requirements.txt
    ) else (
        echo No requirements.txt found
    )
)

echo.
echo Python environment is ready!
echo Python version:
python --version
echo Pip version:
pip --version