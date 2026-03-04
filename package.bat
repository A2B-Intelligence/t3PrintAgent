@echo off
cd /d "%~dp0"

echo ========================================
echo Empacotador - Print Agent para Cliente
echo ========================================
echo.

if not exist dist\PrintAgent.exe (
    echo ERRO: Executavel nao encontrado!
    echo Execute build.bat primeiro para gerar PrintAgent.exe
    pause
    exit /b 1
)

set PACKAGE_DIR=PrintAgent-Package
set PACKAGE_NAME=PrintAgent-%date:~-4,4%%date:~-7,2%%date:~-10,2%.zip

echo [1/4] Criando pasta do pacote...
if exist %PACKAGE_DIR% rmdir /s /q %PACKAGE_DIR%
mkdir %PACKAGE_DIR%

echo.
echo [2/4] Copiando arquivos essenciais...
copy dist\PrintAgent.exe %PACKAGE_DIR%\ >nul
copy instalador.bat %PACKAGE_DIR%\ >nul
copy config.json.example %PACKAGE_DIR%\config.json.example >nul
copy config-embutido.json.example %PACKAGE_DIR%\config-embutido.json.example >nul
copy README.md %PACKAGE_DIR%\ >nul

if exist SumatraPDF.exe (
    copy SumatraPDF.exe %PACKAGE_DIR%\ >nul
    echo   - SumatraPDF.exe incluido
) else (
    echo   - AVISO: SumatraPDF.exe nao encontrado (cliente precisara instalar)
)

echo.
echo [3/4] Criando arquivo de instrucoes...
(
echo ========================================
echo INSTRUCOES DE INSTALACAO
echo ========================================
echo.
echo METODO RECOMENDADO - Usar o Instalador:
echo.
echo 1. Extraia todos os arquivos para uma pasta
echo    Exemplo: C:\PrintAgent
echo.
echo 2. Execute instalador.bat (duplo-clique)
echo    - O instalador guiara voce pela configuracao
echo    - Escolha "Instalacao completa" para configurar tudo
echo    - Siga as instrucoes na tela
echo.
echo METODO MANUAL:
echo.
echo 1. Extraia todos os arquivos para uma pasta
echo    Exemplo: C:\PrintAgent
echo.
echo 2. Configure o config.json:
echo    - Copie config-embutido.json.example para config.json
echo    - Abra config.json e cole as credenciais Firebase na chave "firebase"
echo    - OU use config.json.example e coloque service-account.json na pasta
echo.
echo 3. Instale SumatraPDF (se nao estiver incluido):
echo    - Baixe em: https://www.sumatrapdfreader.org/
echo    - Instale OU coloque SumatraPDF.exe na mesma pasta do PrintAgent.exe
echo.
echo 4. Execute PrintAgent.exe
echo    - Duplo-clique para iniciar
echo    - Mantenha a janela aberta enquanto o agente estiver rodando
echo    - Pressione Ctrl+C para encerrar
echo.
echo ========================================
echo REQUISITOS
echo ========================================
echo - Windows 10 ou superior
echo - Impressora configurada como padrao
echo - Acesso a internet (conexao com Firebase)
echo - Configuracao correta do config.json
echo.
echo ========================================
echo SUPORTE
echo ========================================
echo Em caso de problemas, verifique:
echo - Se config.json esta configurado corretamente
echo - Se a impressora esta configurada como padrao
echo - Se SumatraPDF esta instalado ou na pasta
echo - Se ha conexao com a internet
echo - Os logs em orders_log_*.txt na pasta
) > %PACKAGE_DIR%\INSTRUCOES.txt

echo.
echo [4/4] Criando arquivo ZIP...
if exist "%PACKAGE_NAME%" del /q "%PACKAGE_NAME%"

REM Tenta usar PowerShell para criar ZIP (Windows 10+)
powershell -Command "Compress-Archive -Path '%PACKAGE_DIR%\*' -DestinationPath '%PACKAGE_NAME%' -Force" 2>nul
if errorlevel 1 (
    echo   AVISO: Nao foi possivel criar ZIP automaticamente
    echo   Empacote manualmente a pasta: %PACKAGE_DIR%
) else (
    echo   ZIP criado: %PACKAGE_NAME%
)

echo.
echo ========================================
echo Pacote criado com sucesso!
echo ========================================
echo.
echo Pasta do pacote: %PACKAGE_DIR%\
if exist "%PACKAGE_NAME%" echo Arquivo ZIP: %PACKAGE_NAME%
echo.
echo Conteudo do pacote:
dir /b %PACKAGE_DIR%
echo.
echo Envie a pasta %PACKAGE_DIR%\ ou o arquivo %PACKAGE_NAME% ao cliente
echo.
pause
