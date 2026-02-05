#!/usr/bin/env python3
"""
Studio AI - Audio to Video (MP4)
Converte MP3 em MP4 com tela preta para upload no YouTube.
Otimizado para Termux / Android.
"""

import os
import subprocess
import time
from pathlib import Path
from typing import Optional

# =============================================================================
# CONFIGURAÇÃO DE CORES (Fallback seguro)
# =============================================================================
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    class Fore: CYAN = GREEN = YELLOW = RED = BLUE = MAGENTA = ""
    class Style: BRIGHT = RESET_ALL = ""
    def init(**kwargs): pass

# =============================================================================
# SISTEMA DE LOGGING
# =============================================================================

class Logger:
    @staticmethod
    def info(msg: str): print(f"{Fore.BLUE}ℹ️  {msg}{Style.RESET_ALL}")
    @staticmethod
    def success(msg: str): print(f"{Fore.GREEN}✅ {msg}{Style.RESET_ALL}")
    @staticmethod
    def error(msg: str): print(f"{Fore.RED}❌ {msg}{Style.RESET_ALL}")
    @staticmethod
    def warning(msg: str): print(f"{Fore.YELLOW}⚠️  {msg}{Style.RESET_ALL}")

# =============================================================================
# MOTOR DE CONVERSÃO (FFMPEG)
# =============================================================================

class VideoEngine:
    """Gerencia a conversão de áudio para vídeo via FFmpeg."""
    
    @staticmethod
    def convert_to_mp4(input_audio: str, output_video: str) -> bool:
        """
        Cria um vídeo MP4 com tela preta.
        - f lavfi -i color: Gera a cor preta.
        - s 1280x720: Resolução HD (YouTube).
        - r 1: 1 frame por segundo (economiza processamento e bateria).
        - c:a copy: Apenas copia o áudio sem re-encodificar (mantém qualidade original).
        """
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi', '-i', 'color=c=black:s=1280x720:r=1',
            '-i', input_audio,
            '-c:v', 'libx264', '-tune', 'stillimage', '-pix_fmt', 'yuv420p',
            '-c:a', 'copy',
            '-shortest',
            output_video
        ]
        
        try:
            Logger.info("🎞️  Iniciando renderização do vídeo (Tela Preta)...")
            # Executa e captura apenas erros
            process = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
            
            if process.returncode == 0:
                return True
            else:
                Logger.error(f"Erro no FFmpeg: {process.stderr}")
                return False
        except Exception as e:
            Logger.error(f"Falha na execução: {e}")
            return False

# =============================================================================
# INTERFACE DE USUÁRIO
# =============================================================================

class TerminalUI:
    def clear(self): os.system('clear' if os.name == 'posix' else 'cls')
    
    def header(self, title: str):
        self.clear()
        print(f"{Fore.CYAN}{Style.BRIGHT}{'='*60}")
        print(f" 🎬 STUDIO AI - AUDIO TO YOUTUBE | {title}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'='*60}{Style.RESET_ALL}\n")

    def file_browser(self) -> Optional[Path]:
        path = Path("/sdcard/Download" if os.path.exists("/sdcard/Download") else Path.home())
        while True:
            self.header(f"📂 {path}")
            try:
                items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            except PermissionError:
                path = path.parent
                continue
            
            dirs = [x for x in items if x.is_dir() and not x.name.startswith('.')]
            files = [x for x in items if x.is_file() and x.suffix.lower() == '.mp3']
            
            choices = {'0': ('dir', path.parent)}
            print(f"{Fore.YELLOW}[0] 🔙 Voltar{Style.RESET_ALL}")
            
            idx = 1
            print(f"\n{Fore.CYAN}--- PASTAS ---{Style.RESET_ALL}")
            for d in dirs[:15]:
                print(f"[{idx}] 📁 {d.name}")
                choices[str(idx)] = ('dir', d)
                idx += 1
                
            print(f"\n{Fore.CYAN}--- ARQUIVOS MP3 ---{Style.RESET_ALL}")
            for f in files:
                print(f"[{idx}] 🎧 {f.name}")
                choices[str(idx)] = ('file', f)
                idx += 1
                
            print(f"\n{Fore.RED}[X] Sair{Style.RESET_ALL}")
            opt = input("\n👉 Escolha o áudio: ").strip().lower()
            
            if opt == 'x': return None
            if opt in choices:
                tipo, alvo = choices[opt]
                if tipo == 'dir': path = alvo
                else: return alvo

# =============================================================================
# MAIN
# =============================================================================

def main():
    ui = TerminalUI()
    engine = VideoEngine()
    
    while True:
        ui.header("MENU DE VÍDEO")
        print("1. 📂 Selecionar MP3 para gerar MP4")
        print("0. 🚪 Sair")
        
        opt = input("\n👉 Opção: ").strip()
        
        if opt == '0':
            Logger.info("Saindo...")
            break
            
        if opt == '1':
            audio_path = ui.file_browser()
            if not audio_path:
                continue
            
            video_name = f"{audio_path.stem}.mp4"
            output_path = audio_path.parent / video_name
            
            start_time = time.time()
            if engine.convert_to_mp4(str(audio_path), str(output_path)):
                end_time = time.time()
                Logger.success(f"Vídeo gerado em {int(end_time - start_time)}s!")
                print(f"\n📦 Caminho: {Fore.YELLOW}{output_path}{Style.RESET_ALL}")
            else:
                Logger.error("Falha na conversão do vídeo.")
            
            input("\nPressione Enter para voltar ao menu...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelado pelo usuário.")
