@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo Criar Pacote de Atualizacao - Print Agent
echo ========================================
echo.

REM Le a versao do agent.py (linha VERSION = 'X.Y.Z'), ou usa o 1o argumento
set "VERSION="
for /f "tokens=2 delims='" %%i in ('findstr /b "VERSION" agent.py') do set "VERSION=%%i"
if not "%~1"=="" set "VERSION=%~1"
if "%VERSION%"=="" (
    echo ERRO: nao foi possivel detectar a versao.
    echo Informe: criar-atualizacao.bat 1.2.0
    pause
    exit /b 1
)

echo Versao: %VERSION%
echo.

set "PKG=update"
set "OUT=PrintAgent-Update-v%VERSION%.zip"

if exist %PKG% rmdir /s /q %PKG%
mkdir %PKG%

echo [1/3] Copiando arquivos...
copy agent.py %PKG%\ >nul
copy printer.py %PKG%\ >nul
copy receipt_generator.py %PKG%\ >nul
copy run.bat %PKG%\ >nul
copy run-silent.bat %PKG%\ >nul
copy requirements.txt %PKG%\ >nul
copy atualizar.bat %PKG%\ >nul
> %PKG%\VERSION.txt echo v%VERSION% - %date%

echo [2/3] Criando instrucoes...
(
echo ========================================
echo ATUALIZACAO DO PRINT AGENT
echo ========================================
echo.
echo 1. Extraia a pasta "update" deste ZIP para DENTRO da pasta do
echo    PrintAgent ^(a pasta que contem agent.py e config.json^).
echo    Exemplo: C:\t3-a2beats-PrintAgent\update
echo.
echo 2. De um duplo-clique em: update\atualizar.bat
echo    ^(nao precisa fechar o agente antes - o atualizador encerra sozinho^)
echo.
echo 3. Pronto! O agente reinicia sozinho em uma nova janela.
echo    O config.json ^(credenciais^) NAO e alterado.
echo.
echo Se algo der errado, a versao anterior fica salva na pasta backup\.
) > %PKG%\LEIA-ME.txt

echo [3/3] Gerando ZIP...
if exist "%OUT%" del /q "%OUT%"
powershell -NoProfile -Command "Compress-Archive -Path 'update' -DestinationPath '%OUT%' -Force"
if errorlevel 1 (
    echo AVISO: nao foi possivel criar o ZIP automaticamente.
    echo Compacte manualmente a pasta: %PKG%
    pause
    exit /b 1
)
rmdir /s /q %PKG%

echo.
echo ========================================
echo Pacote criado: %OUT%
echo ========================================
echo Envie este ZIP ao cliente com as instrucoes do LEIA-ME.txt
echo.
pause
