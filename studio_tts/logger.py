"""
Studio AI TTS - Sistema de Logging
"""

from typing import Tuple
from colorama import Fore, Style


class Logger:
    """Logger colorido e estruturado."""
    
    @staticmethod
    def info(msg: str):
        print(f"{Fore.BLUE}ℹ️  {msg}{Style.RESET_ALL}")
    
    @staticmethod
    def success(msg: str):
        print(f"{Fore.GREEN}✅ {msg}{Style.RESET_ALL}")
    
    @staticmethod
    def warning(msg: str):
        print(f"{Fore.YELLOW}⚠️  {msg}{Style.RESET_ALL}")
    
    @staticmethod
    def error(msg: str):
        print(f"{Fore.RED}❌ {msg}{Style.RESET_ALL}")
    
    @staticmethod
    def debug(msg: str):
        # Descomente para debugging
        # print(f"{Fore.MAGENTA}🔍 {msg}{Style.RESET_ALL}")
        pass
    
    @staticmethod
    def progress(current: int, total: int, prefix: str = "", elapsed: float = 0):
        """Mostra barra de progresso com tempo estimado."""
        pct = int((current / total) * 20) if total > 0 else 0
        bar = f"[{'█' * pct}{'-' * (20 - pct)}]"
        
        # Calcula tempo restante
        eta = ""
        if elapsed > 0 and current > 0:
            avg_per_item = elapsed / current
            remaining = avg_per_item * (total - current)
            eta = f" | ETA: {TimeEstimator.format_time(remaining)}"
        
        print(f"\r{bar} {prefix} {current}/{total}{eta}    ", end="", flush=True)


class TimeEstimator:
    """Calcula estimativas de tempo para conversão."""
    # Tempo médio por caractere (segundos) - ajustado empiricamente
    GEMINI_CHAR_TIME: float = 0.015  # ~15ms por caractere
    EDGE_CHAR_TIME: float = 0.008    # ~8ms por caractere
    
    @classmethod
    def estimate(cls, text: str, engine: str) -> Tuple[float, str]:
        """Retorna (segundos, string formatada)."""
        chars = len(text)
        rate = cls.GEMINI_CHAR_TIME if engine == "google" else cls.EDGE_CHAR_TIME
        seconds = chars * rate
        return seconds, cls.format_time(seconds)
    
    @staticmethod
    def format_time(seconds: float) -> str:
        """Formata segundos em string legível."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds//60)}min {int(seconds%60)}s"
        else:
            return f"{int(seconds//3600)}h {int((seconds%3600)//60)}min"
