"""
Studio AI TTS - Aplicação Principal
"""

import asyncio
import sys
import time
import traceback
from colorama import Fore, Style

from .config import config_mgr
from .ui import TerminalUI
from .engine import ConversionEngine
from .cache import AudioCache, HistoryManager
from .logger import Logger


class StudioAIApp:
    """Aplicação principal."""
    
    def __init__(self):
        self.settings = config_mgr.load()
        self.ui = TerminalUI(self.settings)
        self.engine = ConversionEngine(self.settings)
        self.cache = AudioCache()
        self.history = HistoryManager()
    
    async def run(self):
        """Loop principal."""
        # Limpa cache antigo na inicialização
        self.cache.clear_old(days=7)
        
        # Passa referência do histórico para o engine
        self.engine.history = self.history
        
        while True:
            try:
                opt = self.ui.menu_principal()
                
                if opt == '0' or opt.lower() == 'sair':
                    Logger.info("Até logo! 👋")
                    break
                elif opt == '1':
                    await self.engine.convert()
                elif opt == '2':
                    files = self.ui.file_browser_multi()
                    if files:
                        await self.engine.convert_batch(files)
                elif opt == '3':
                    self.ui.menu_historico(self.history)
                elif opt == '4':
                    self.ui.menu_chaves()
                elif opt == '5':
                    self.ui.menu_preferencias()
                    self.engine = ConversionEngine(self.settings)
                    self.engine.history = self.history
                elif opt == '6':
                    removed = self.cache.clear_old(days=0)
                    Logger.success(f"Cache limpo: {removed} arquivo(s) removido(s)")
                    input("Pressione Enter...")
                else:
                    Logger.warning("Opção inválida")
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                print("\n")
                Logger.info("Operação cancelada")
                time.sleep(1)
            except Exception as e:
                Logger.error(f"Erro inesperado: {e}")
                traceback.print_exc()
                input("Pressione Enter para continuar...")


def main():
    """Entry point."""
    try:
        app = StudioAIApp()
        asyncio.run(app.run())
    except Exception as e:
        print(f"{Fore.RED}Erro fatal: {e}{Style.RESET_ALL}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
