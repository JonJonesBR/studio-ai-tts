@echo off
chcp 65001 >nul
cls

echo ========================================================
echo       🎧 Studio AI TTS - Instalador Automático
echo ========================================================
echo.

:: 1. Verificando Python
echo  [1/4] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo     ❌ Python não encontrado!
    echo.
    echo     Tentando instalar Python via Winget...
    winget install -e --id Python.Python.3.10
    if %errorlevel% neq 0 (
        echo     ❌ Falha ao instalar Python automaticamente.
        echo     Por favor, baixe e instale em: https://python.org/downloads
        echo     Lembre-se de marcar "Add Python to PATH" no instalador.
        pause
        exit /b
    )
    echo     ✅ Python instalado!
    echo     ⚠️  IMPORTANTE: Feche esta janela e abra novamente para aplicar as mudanças.
    pause
    exit /b
) else (
    echo     ✅ Python detectado.
)

:: 2. Verificando FFmpeg
echo.
echo  [2/4] Verificando FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo     ⚠️  FFmpeg não encontrado.
    echo     Tentando instalar via Winget...
    winget install -e --id Gyan.FFmpeg
    if %errorlevel% neq 0 (
        echo     ❌ Falha na instalação automática do FFmpeg.
        echo     O programa funcionará, mas não conseguirá unir os capítulos do áudio.
    ) else (
        echo     ✅ FFmpeg instalado.
    )
) else (
    echo     ✅ FFmpeg detectado.
)

:: 3. Criando VENV
echo.
echo  [3/4] Configurando ambiente virtual...
if not exist "venv" (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo     ❌ Erro ao criar ambiente virtual.
        pause
        exit /b
    )
    echo     ✅ Ambiente criado.
) else (
    echo     ✅ Ambiente já existe.
)

:: 4. Instalando dependências
echo.
echo  [4/4] Instalando bibliotecas...
venv\Scripts\python -m pip install --upgrade pip >nul
venv\Scripts\pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo     ❌ Erro ao baixar dependências. Verifique sua internet.
    pause
    exit /b
)
echo     ✅ Todas as bibliotecas instaladas.

:: 5. Configuração final
if not exist "studio_config.json" (
    if exist "config.example.json" (
        copy config.example.json studio_config.json >nul
        echo     ✅ Configuração inicial criada.
    )
)

echo.
echo ========================================================
echo       🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!
echo ========================================================
echo.
echo  Para abrir o programa, use o comando:
echo.
echo      .\run.bat
echo.
pause
