@echo off
cd /d "%~dp0"

if not exist "config.json" (
    echo ERRO: config.json nao encontrado.
    echo Copie config.json.example para config.json e configure.
    pause
    exit /b 1
)

if not exist "venv" (
    echo Criando ambiente virtual...
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install -r requirements.txt -q

echo.
echo Iniciando agente de impressao...
echo Mantenha esta janela aberta. Pressione Ctrl+C para encerrar.
echo.

python agent.py

pause
