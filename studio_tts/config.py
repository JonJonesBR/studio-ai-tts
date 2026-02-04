"""
Studio AI TTS - Configurações e Gerenciamento
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .logger import Logger


@dataclass(frozen=True)
class AppConfig:
    """Configurações imutáveis da aplicação."""
    CONFIG_FILE: str = "studio_config.json"
    DEFAULT_CHUNK_LIMIT: int = 3000
    MIN_CHUNK_SIZE: int = 100
    MAX_CHUNK_SIZE: int = 5000
    MAX_RETRIES: int = 10
    RETRY_BASE_DELAY: float = 1.0
    MAX_RETRY_DELAY: float = 60.0
    SESSION_TIMEOUT: int = 120
    PCM_SAMPLE_RATE: int = 24000
    AUDIO_BITRATE: str = "192k"
    MAX_CONCURRENT: int = 3


# Instância global de configurações
CONFIG = AppConfig()


@dataclass
class UserSettings:
    """Configurações mutáveis do usuário persistidas em JSON."""
    motor_padrao: str = "edge"
    velocidade: str = "+0%"
    limite_chunk: int = 3000
    modelo_gemini: str = "gemini-2.5-flash-preview-tts"
    google_keys: List[str] = field(default_factory=list)
    voz_edge: str = "pt-BR-AntonioNeural"
    voz_google: str = "Puck"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "motor_padrao": self.motor_padrao,
            "velocidade": self.velocidade,
            "limite_chunk": self.limite_chunk,
            "modelo_gemini": self.modelo_gemini,
            "google_keys": self.google_keys,
            "voz_edge": self.voz_edge,
            "voz_google": self.voz_google,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserSettings":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class ConfigManager:
    """Gerencia persistência de configurações."""
    
    def __init__(self, filepath: str = CONFIG.CONFIG_FILE):
        self.filepath = Path(filepath)
        self._settings: Optional[UserSettings] = None
    
    def load(self) -> UserSettings:
        """Carrega configurações do arquivo."""
        if self._settings is not None:
            return self._settings
            
        default = UserSettings()
        
        if not self.filepath.exists():
            self._settings = default
            self.save(default)
            return default
        
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._settings = UserSettings.from_dict({**default.to_dict(), **data})
                return self._settings
        except Exception as e:
            Logger.warning(f"Erro ao carregar config: {e}. Usando padrões.")
            self._settings = default
            return default
    
    def save(self, settings: UserSettings):
        """Salva configurações no arquivo."""
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(settings.to_dict(), f, indent=4, ensure_ascii=False)
            self._settings = settings
        except Exception as e:
            Logger.error(f"Erro ao salvar config: {e}")
    
    @property
    def settings(self) -> UserSettings:
        """Acesso rápido às configurações carregadas."""
        if self._settings is None:
            return self.load()
        return self._settings


# Instância global do gerenciador de config
config_mgr = ConfigManager()
