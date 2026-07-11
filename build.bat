@echo off
cd /d "%~dp0"

echo ========================================
echo Gerador de Executavel - Print Agent
echo ========================================
echo.

echo [1/4] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Instale Python 3.10 ou superior de https://www.python.org/
    pause
    exit /b 1
)
python --version

echo.
echo [2/4] Instalando PyInstaller...
python -m pip install pyinstaller -q
if errorlevel 1 (
    echo ERRO: Falha ao instalar PyInstaller
    echo Tente executar manualmente: python -m pip install pyinstaller
    pause
    exit /b 1
)

echo.
echo [3/4] Limpando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist PrintAgent.spec del /q PrintAgent.spec

echo.
echo [4/4] Gerando executavel...
python -m PyInstaller --onefile --name "PrintAgent" ^
    --hidden-import=firebase_admin ^
    --hidden-import=xhtml2pdf ^
    --hidden-import=xhtml2pdf.pisa ^
    --hidden-import=google.cloud.firestore ^
    --hidden-import=google.cloud ^
    --hidden-import=receipt_generator ^
    --hidden-import=printer ^
    --hidden-import=pisa ^
    --hidden-import=reportlab ^
    --hidden-import=google.auth ^
    --hidden-import=google.auth.transport.requests ^
    --hidden-import=charset_normalizer ^
    --collect-submodules=charset_normalizer ^
    --collect-submodules=xhtml2pdf ^
    --collect-submodules=reportlab ^
    --console ^
    --clean ^
    agent.py

if errorlevel 1 (
    echo.
    echo ERRO: Falha ao gerar executavel
    pause
    exit /b 1
)

echo.
echo ========================================
echo Executavel gerado com sucesso!
echo ========================================
echo.
echo Localizacao: dist\PrintAgent.exe
echo.
echo Para enviar ao cliente, crie um pacote com:
echo   1. PrintAgent.exe
echo   2. config.json (ou config.json.example como modelo)
echo   3. SumatraPDF.exe (opcional - pode instalar separadamente)
echo   4. README.md (instrucoes de uso)
echo.
echo O cliente precisara:
echo   - Windows 10 ou superior
echo   - Configurar config.json com credenciais Firebase
echo   - Ter impressora configurada como padrao
echo   - SumatraPDF instalado OU SumatraPDF.exe na mesma pasta
echo.
pause
