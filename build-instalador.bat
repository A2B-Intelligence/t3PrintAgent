@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo Gerador de Instalador - Print Agent
echo ========================================
echo.
echo Gera PrintAgent-Setup-vX.Y.Z.exe com as credenciais EMBUTIDAS.
echo Envie ao cliente APENAS o instalador - nada de config.json.
echo.

echo [1/6] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Instale Python 3.10+ de https://www.python.org/
    pause
    exit /b 1
)

echo [2/6] Verificando config.json ^(credenciais^)...
if not exist "config.json" (
    echo ERRO: config.json nao encontrado!
    echo Coloque a service account do Firebase nesta pasta e gere com:
    echo   python gerar-config.py sua-service-account.json
    pause
    exit /b 1
)

echo [3/6] Verificando SumatraPDF.exe...
if not exist "SumatraPDF.exe" (
    echo ERRO: SumatraPDF.exe nao encontrado nesta pasta!
    echo Baixe a versao portable em https://www.sumatrapdfreader.org/
    pause
    exit /b 1
)

REM Le a versao do agent.py (linha VERSION = 'X.Y.Z')
set "VERSION="
for /f "tokens=2 delims='" %%i in ('findstr /b "VERSION" agent.py') do set "VERSION=%%i"
if "%VERSION%"=="" set "VERSION=1.0.0"
echo Versao: %VERSION%

echo.
echo [4/6] Instalando dependencias...
python -m pip install -q -r requirements.txt pyinstaller
if errorlevel 1 (
    echo ERRO: falha ao instalar dependencias
    pause
    exit /b 1
)

echo.
echo [5/6] Gerando PrintAgent.exe com credenciais embutidas...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist PrintAgent.spec del /q PrintAgent.spec

python -m PyInstaller --onefile --console --clean --name "PrintAgent" ^
    --add-data "config.json;." ^
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
    agent.py
if errorlevel 1 (
    echo ERRO: falha ao gerar o executavel
    pause
    exit /b 1
)

echo.
echo [6/6] Compilando o instalador ^(Inno Setup^)...
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "%LocalAppData%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"
if "%ISCC%"=="" (
    echo ERRO: Inno Setup 6 nao encontrado!
    echo Baixe gratis em: https://jrsoftware.org/isdl.php
    echo Instale com as opcoes padrao e rode este script novamente.
    pause
    exit /b 1
)

"%ISCC%" /Qp /DMyAppVersion=%VERSION% instalador.iss
if errorlevel 1 (
    echo ERRO: falha ao compilar o instalador
    pause
    exit /b 1
)

echo.
echo ========================================
echo Instalador gerado com sucesso!
echo ========================================
echo.
echo Arquivo: PrintAgent-Setup-v%VERSION%.exe
echo.
echo Envie APENAS este arquivo ao cliente. Ele contem:
echo   - PrintAgent.exe com credenciais e banco embutidos
echo   - SumatraPDF.exe
echo O cliente so precisa: duplo-clique - Avancar - Concluir.
echo.
pause
