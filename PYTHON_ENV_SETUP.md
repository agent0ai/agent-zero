# Python Environment Setup for Windows

## The Issue
The error `pyenv: The term 'pyenv' is not recognized` occurs because:
- **pyenv is not natively available on Windows** - it's designed for Unix-like systems (Linux, macOS)
- Windows requires different approaches for Python version management

## Solutions

### Option 1: Use Virtual Environment (Recommended)
Instead of `pyenv shell 3.13.3`, use the provided scripts:

**PowerShell:**
```powershell
.\setup_python_env.ps1
```

**Command Prompt:**
```cmd
setup_python_env.bat
```

These scripts will:
1. Create a Python virtual environment
2. Activate it automatically
3. Install all requirements from `requirements.txt`

### Option 2: Manual Virtual Environment
```powershell
# Create virtual environment
python -m venv venv

# Activate it (PowerShell)
.\venv\Scripts\Activate.ps1

# Or activate it (Command Prompt)
venv\Scripts\activate.bat

# Install requirements
pip install -r requirements.txt
```

### Option 3: Use pyenv-win (Advanced)
If you really need pyenv functionality on Windows:

1. Install pyenv-win:
```powershell
git clone https://github.com/pyenv-win/pyenv-win.git $HOME/.pyenv
```

2. Add to your PowerShell profile:
```powershell
[System.Environment]::SetEnvironmentVariable('PYENV',$env:USERPROFILE + "\.pyenv\pyenv-win\","User")
[System.Environment]::SetEnvironmentVariable('PYENV_HOME',$env:USERPROFILE + "\.pyenv\pyenv-win\","User")
[System.Environment]::SetEnvironmentVariable('path', $env:USERPROFILE + "\.pyenv\pyenv-win\bin;" + $env:USERPROFILE + "\.pyenv\pyenv-win\shims;" + [System.Environment]::GetEnvironmentVariable('path', "User"),"User")
```

3. Restart PowerShell and use:
```powershell
pyenv install 3.13.3
pyenv shell 3.13.3
```

## Recommended Approach
For this project, **use Option 1** with the provided scripts. It's simpler and more reliable on Windows.

## Quick Start
Every time you start a new session:
```powershell
# Just run this instead of 'pyenv shell 3.13.3'
.\setup_python_env.ps1
```

The script handles everything automatically!