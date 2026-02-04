#!/usr/bin/env python3
"""
Studio AI TTS - Wrapper de Compatibilidade
Redireciona para o novo pacote studio_tts.
"""

import sys
import os

# Adiciona diretório atual ao path se necessário
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from studio_tts.app import main
except ImportError as e:
    print(f"Erro ao importar studio_tts: {e}")
    sys.exit(1)

if __name__ == "__main__":
    main()
