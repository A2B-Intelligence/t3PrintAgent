@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo Atualizador - Print Agent
echo ========================================
echo.

set "DESTINO=%~dp0.."

if not exist "%DESTINO%\config.json" (
    echo ERRO: pasta de instalacao nao encontrada.
    echo.
    echo Esta pasta "update" deve ficar DENTRO da pasta do PrintAgent
    echo ^(a pasta que contem agent.py e config.json^).
    echo Extraia o ZIP no lugar certo e execute novamente.
    echo.
    pause
    exit /b 1
)

echo [1/4] Encerrando o agente...
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { ($_.Name -eq 'python.exe' -or $_.Name -eq 'pythonw.exe') -and $_.CommandLine -like '*agent.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>&1
taskkill /f /im PrintAgent.exe >nul 2>&1

echo [2/4] Fazendo backup da versao atual...
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "TS=%%i"
set "BACKUP=%DESTINO%\backup\%TS%"
mkdir "%BACKUP%" >nul 2>&1
copy "%DESTINO%\*.py" "%BACKUP%\" >nul 2>&1
copy "%DESTINO%\run.bat" "%BACKUP%\" >nul 2>&1
copy "%DESTINO%\run-silent.bat" "%BACKUP%\" >nul 2>&1
copy "%DESTINO%\VERSION.txt" "%BACKUP%\" >nul 2>&1
echo   Backup salvo em: %BACKUP%

echo [3/4] Instalando nova versao...
copy /y "%~dp0agent.py" "%DESTINO%\" >nul
copy /y "%~dp0printer.py" "%DESTINO%\" >nul
copy /y "%~dp0receipt_generator.py" "%DESTINO%\" >nul
copy /y "%~dp0run.bat" "%DESTINO%\" >nul
if exist "%~dp0run-silent.bat" copy /y "%~dp0run-silent.bat" "%DESTINO%\" >nul
if exist "%~dp0requirements.txt" copy /y "%~dp0requirements.txt" "%DESTINO%\" >nul
if exist "%~dp0VERSION.txt" copy /y "%~dp0VERSION.txt" "%DESTINO%\" >nul

REM IMPORTANTE: config.json (credenciais) NUNCA e alterado pela atualizacao

echo [4/4] Reiniciando o agente...
start "" "%DESTINO%\run.bat"

echo.
echo ========================================
echo Atualizacao concluida!
echo ========================================
if exist "%~dp0VERSION.txt" type "%~dp0VERSION.txt"
echo.
echo O agente foi reiniciado em uma nova janela.
echo Mantenha aquela janela aberta durante a operacao.
echo Se algo der errado, a versao anterior esta em: backup\%TS%
echo.
pause
