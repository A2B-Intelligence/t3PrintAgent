@echo off
cd /d "%~dp0"

if not exist "config.json" (
    echo ERRO: config.json nao encontrado.
    exit /b 1
)

if not exist "venv" (
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install -r requirements.txt -q 2>nul

pythonw agent.py
