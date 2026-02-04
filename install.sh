#!/bin/bash

clear
echo "====================================="
echo "📱 Studio AI TTS - Instalador Termux"
echo "====================================="
echo ""

# 1. Atualizar e instalar pacotes do sistema
echo "📦 [1/4] Atualizando pacotes do sistema..."
pkg update -y && pkg upgrade -y

echo "📦 [2/4] Instalando dependências (Python, FFmpeg)..."
pkg install python ffmpeg -y

# 2. Configurar armazenamento
echo "📂 [3/4] Configurando permissão de armazenamento..."
echo "⚠️  Uma janela pop-up pode aparecer pedindo permissão. Clique em PERMITIR!"
termux-setup-storage
sleep 3

# 3. Instalar bibliotecas Python
echo "🐍 [4/4] Instalando bibliotecas Python..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configuração inicial
if [ ! -f "studio_config.json" ]; then
    if [ -f "config.example.json" ]; then
        cp config.example.json studio_config.json
        echo "✅ Configuração inicial criada."
    fi
fi

# Tornar o run.sh executável
chmod +x run.sh

echo ""
echo "🎉 INSTALAÇÃO CONCLUÍDA!"
echo "====================================="
echo "Para iniciar o programa, digite:"
echo ""
echo "./run.sh"
echo ""
