@echo off
if not exist "venv" (
    echo ❌ Erro: Ambiente nao instalado.
    echo Execute install.bat primeiro.
    pause
    exit /b
)
echo 🚀 Iniciando Studio AI TTS...
venv\Scripts\python tts.py
if %errorlevel% neq 0 (
    echo.
    echo O programa encerrou.
    pause
)
