"""
Studio AI TTS - Cache de Áudio e Histórico
"""

import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from typing import ClassVar, List, Optional

from .logger import Logger


class AudioCache:
    """Cache para chunks de áudio já processados."""
    
    CACHE_DIR: ClassVar[Path] = Path.home() / ".studio_ai_cache"
    MIN_VALID_SIZE: ClassVar[int] = 200
    
    def __init__(self):
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Garante que diretório de cache existe."""
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    def _generate_key(self, text: str, voice: str, engine: str) -> str:
        """Gera chave única para o chunk."""
        content = f"{engine}:{voice}:{text}".encode('utf-8')
        return hashlib.sha256(content).hexdigest()[:16]
    
    def _get_cache_path(self, key: str) -> Path:
        """Retorna caminho do arquivo em cache."""
        return self.CACHE_DIR / f"{key}.wav"
    
    def get(self, text: str, voice: str, engine: str) -> Optional[bytes]:
        """Recupera áudio do cache se existir e for válido."""
        key = self._generate_key(text, voice, engine)
        cache_file = self._get_cache_path(key)
        
        if cache_file.exists() and cache_file.stat().st_size > self.MIN_VALID_SIZE:
            try:
                return cache_file.read_bytes()
            except Exception:
                return None
        return None
    
    def put(self, text: str, voice: str, engine: str, audio_data: bytes) -> bool:
        """Salva áudio no cache."""
        if not audio_data or len(audio_data) < self.MIN_VALID_SIZE:
            return False
            
        key = self._generate_key(text, voice, engine)
        cache_file = self._get_cache_path(key)
        
        try:
            cache_file.write_bytes(audio_data)
            return True
        except Exception as e:
            Logger.debug(f"Erro ao salvar cache: {e}")
            return False
    
    def clear_old(self, days: int = 7) -> int:
        """Remove arquivos de cache mais antigos que X dias."""
        if not self.CACHE_DIR.exists():
            return 0
            
        cutoff = time.time() - (days * 86400)
        removed = 0
        
        for f in self.CACHE_DIR.glob("*.wav"):
            try:
                if f.stat().st_mtime < cutoff:
                    f.unlink()
                    removed += 1
            except Exception:
                pass
        
        if removed > 0:
            Logger.info(f"🧹 Cache limpo: {removed} arquivo(s) removido(s)")
        return removed


class HistoryManager:
    """Gerencia histórico de conversões."""
    
    HISTORY_FILE: ClassVar[Path] = Path.home() / ".studio_ai_history.json"
    MAX_ENTRIES: ClassVar[int] = 50
    
    def __init__(self):
        self._history: List[dict] = []
        self._load()
    
    def _load(self):
        """Carrega histórico do arquivo."""
        try:
            if self.HISTORY_FILE.exists():
                with open(self.HISTORY_FILE, 'r', encoding='utf-8') as f:
                    self._history = json.load(f)
        except Exception:
            self._history = []
    
    def _save(self):
        """Salva histórico no arquivo."""
        try:
            with open(self.HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            Logger.debug(f"Erro ao salvar histórico: {e}")
    
    def add(self, source: str, output: str, duration: float, engine: str, voice: str):
        """Adiciona entrada ao histórico."""
        entry = {
            "source": source,
            "output": output,
            "duration": round(duration, 1),
            "engine": engine,
            "voice": voice,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self._history.insert(0, entry)
        self._history = self._history[:self.MAX_ENTRIES]
        self._save()
    
    def get_recent(self, limit: int = 10) -> List[dict]:
        """Retorna conversões recentes."""
        return self._history[:limit]
    
    def clear(self):
        """Limpa histórico."""
        self._history = []
        self._save()
        try:
            self.HISTORY_FILE.unlink(missing_ok=True)
        except Exception:
            pass
