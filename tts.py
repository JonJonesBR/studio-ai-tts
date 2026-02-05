#!/usr/bin/env python3
"""
Studio AI TTS - Conversor de Texto para Audiobook
Versão 2.0 - Arquitetura Modular e Robusta
"""

import asyncio
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Tuple, Union
from urllib.parse import urljoin

import aiohttp
import edge_tts
from colorama import Fore, Style, init

# Inicializa colorama
init(autoreset=True)

# =============================================================================
# CONFIGURAÇÕES E CONSTANTES
# =============================================================================

@dataclass(frozen=True)
class AppConfig:
    """Configurações imutáveis da aplicação."""
    CONFIG_FILE: str = "studio_config.json"
    DEFAULT_CHUNK_LIMIT: int = 1500
    MIN_CHUNK_SIZE: int = 100
    MAX_CHUNK_SIZE: int = 5000
    MAX_RETRIES: int = 10
    RETRY_BASE_DELAY: float = 1.0
    MAX_RETRY_DELAY: float = 60.0
    SESSION_TIMEOUT: int = 120
    PCM_SAMPLE_RATE: int = 24000
    AUDIO_BITRATE: str = "192k"


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


# =============================================================================
# CATÁLOGO DE VOZES
# =============================================================================

@dataclass(frozen=True)
class Voice:
    """Representa uma voz TTS."""
    id: str
    name: str
    category: str = ""
    engine: str = ""
    gender: str = ""


class VoiceCatalog:
    """Catálogo centralizado de vozes expandido via JSON."""
    
    GEMINI_VOICES: ClassVar[List[Voice]] = [
        # Femininas Conversacionais
        Voice("Aoede", "Aoede (Conversacional)", "Gemini: Feminina Conversacional", "gemini", "F"),
        Voice("Kore", "Kore (Energética)", "Gemini: Feminina Conversacional", "gemini", "F"),
        Voice("Leda", "Leda (Profissional)", "Gemini: Feminina Conversacional", "gemini", "F"),
        Voice("Zephyr", "Zephyr (Brilhante)", "Gemini: Feminina Conversacional", "gemini", "F"),
        # Femininas Especializadas
        Voice("Achird", "Achird (Jovem/Curiosa)", "Gemini: Feminina Especializada", "gemini", "F"),
        Voice("Algenib", "Algenib (Confiante)", "Gemini: Feminina Especializada", "gemini", "F"),
        Voice("Callirrhoe", "Callirrhoe (Profissional)", "Gemini: Feminina Especializada", "gemini", "F"),
        Voice("Despina", "Despina (Acolhedora)", "Gemini: Feminina Especializada", "gemini", "F"),
        Voice("Erinome", "Erinome (Articulada)", "Gemini: Feminina Especializada", "gemini", "F"),
        Voice("Laomedeia", "Laomedeia (Inquisitiva)", "Gemini: Feminina Especializada", "gemini", "F"),
        Voice("Pulcherrima", "Pulcherrima (Animada)", "Gemini: Feminina Especializada", "gemini", "F"),
        Voice("Sulafat", "Sulafat (Persuasiva)", "Gemini: Feminina Especializada", "gemini", "F"),
        Voice("Vindemiatrix", "Vindemiatrix (Calma)", "Gemini: Feminina Especializada", "gemini", "F"),
        # Masculinas Principais
        Voice("Puck", "Puck (Animado)", "Gemini: Masculina Principal", "gemini", "M"),
        Voice("Charon", "Charon (Suave)", "Gemini: Masculina Principal", "gemini", "M"),
        Voice("Orus", "Orus (Maduro/Grave)", "Gemini: Masculina Principal", "gemini", "M"),
        Voice("Autonoe", "Autonoe (Maduro/Ressonante)", "Gemini: Masculina Principal", "gemini", "M"),
        Voice("Iapetus", "Iapetus (Clara)", "Gemini: Masculina Principal", "gemini", "M"),
        Voice("Umbriel", "Umbriel (Suave/Experiente)", "Gemini: Masculina Principal", "gemini", "M"),
        # Masculinas Especializadas
        Voice("Achernar", "Achernar (Amigável)", "Gemini: Masculina Especializada", "gemini", "M"),
        Voice("Alnilam", "Alnilam (Energético)", "Gemini: Masculina Especializada", "gemini", "M"),
        Voice("Enceladus", "Enceladus (Entusiasta)", "Gemini: Masculina Especializada", "gemini", "M"),
        Voice("Fenrir", "Fenrir (Natural)", "Gemini: Masculina Especializada", "gemini", "M"),
        Voice("Gacrux", "Gacrux (Confiante)", "Gemini: Masculina Especializada", "gemini", "M"),
        Voice("Rasalgethi", "Rasalgethi (Conversacional)", "Gemini: Masculina Especializada", "gemini", "M"),
        Voice("Sadachbia", "Sadachbia (Grave/Cool)", "Gemini: Masculina Especializada", "gemini", "M"),
        Voice("Sadaltager", "Sadaltager (Entusiasta)", "Gemini: Masculina Especializada", "gemini", "M"),
        Voice("Schedar", "Schedar (Casual)", "Gemini: Masculina Especializada", "gemini", "M"),
        Voice("Zubenelgenubi", "Zubenelgenubi (Poderoso)", "Gemini: Masculina Especializada", "gemini", "M"),
    ]
    
    EDGE_VOICES: ClassVar[List[Voice]] = [
        # --- Multilingual (As melhores para Audiobooks) ---
        Voice("pt-BR-ThalitaMultilingualNeural", "Thalita Multilingual (PT-BR) ⭐", "Edge: Multilingual", "edge", "F"),
        Voice("en-US-AvaMultilingualNeural", "Ava (Multilingual EUA) ⭐", "Edge: Multilingual", "edge", "F"),
        Voice("en-US-BrianMultilingualNeural", "Brian (Multilingual EUA) ⭐", "Edge: Multilingual", "edge", "M"),
        Voice("en-US-AndrewMultilingualNeural", "Andrew (Multilingual EUA) ⭐", "Edge: Multilingual", "edge", "M"),
        Voice("en-US-EmmaMultilingualNeural", "Emma (Multilingual EUA) ⭐", "Edge: Multilingual", "edge", "F"),
        Voice("en-AU-WilliamMultilingualNeural", "William (Multilingual AUS)", "Edge: Multilingual", "edge", "M"),
        Voice("fr-FR-RemyMultilingualNeural", "Remy (Multilingual FR)", "Edge: Multilingual", "edge", "M"),
        Voice("fr-FR-VivienneMultilingualNeural", "Vivienne (Multilingual FR)", "Edge: Multilingual", "edge", "F"),
        Voice("de-DE-FlorianMultilingualNeural", "Florian (Multilingual DE)", "Edge: Multilingual", "edge", "M"),
        Voice("de-DE-SeraphinaMultilingualNeural", "Seraphina (Multilingual DE)", "Edge: Multilingual", "edge", "F"),
        Voice("it-IT-GiuseppeMultilingualNeural", "Giuseppe (Multilingual IT)", "Edge: Multilingual", "edge", "M"),
        Voice("ko-KR-HyunsuMultilingualNeural", "Hyunsu (Multilingual KR)", "Edge: Multilingual", "edge", "M"),
    ]


    @classmethod
    def get_by_engine(cls, engine: str) -> List[Voice]:
        if engine == "gemini":
            return cls.GEMINI_VOICES
        return cls.EDGE_VOICES
    
    @classmethod
    def get_by_id(cls, voice_id: str) -> Optional[Voice]:
        all_voices = cls.GEMINI_VOICES + cls.EDGE_VOICES
        for v in all_voices:
            if v.id == voice_id:
                return v
        return None

# =============================================================================
# EXCEÇÕES CUSTOMIZADAS
# =============================================================================

class TTSError(Exception):
    """Base para erros de TTS."""
    pass


class RateLimitError(TTSError):
    """Erro de rate limiting (429)."""
    pass


class APIKeyError(TTSError):
    """Erro de API key inválida."""
    pass


class AudioProcessingError(TTSError):
    """Erro no processamento de áudio."""
    pass


class NetworkError(TTSError):
    """Erro de rede."""
    pass


# =============================================================================
# SISTEMA DE LOGGING
# =============================================================================

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
    def progress(current: int, total: int, prefix: str = ""):
        """Mostra barra de progresso."""
        pct = int((current / total) * 20) if total > 0 else 0
        bar = f"[{'█' * pct}{'-' * (20 - pct)}]"
        print(f"\r{bar} {prefix} {current}/{total}", end="", flush=True)


# =============================================================================
# GERENCIADOR DE CONFIGURAÇÕES
# =============================================================================

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


# =============================================================================
# SISTEMA DE CACHE DE ÁUDIO
# =============================================================================

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
        import hashlib
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
            
        import time
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


# =============================================================================
# GERENCIADOR DE CHAVES API
# =============================================================================

class KeyManager:
    """Gerencia rotação de chaves API com thread-safety."""
    
    def __init__(self, keys: List[str]):
        self._keys = [k.strip() for k in keys if k.strip()]
        self._current_index = 0
        self._lock = asyncio.Lock()
    
    @property
    def has_keys(self) -> bool:
        return len(self._keys) > 0
    
    @property
    def count(self) -> int:
        return len(self._keys)
    
    async def get_current(self) -> Optional[str]:
        """Retorna chave atual de forma thread-safe."""
        async with self._lock:
            if not self._keys:
                return None
            return self._keys[self._current_index]
    
    async def rotate(self):
        """Rotaciona para próxima chave."""
        async with self._lock:
            old_idx = self._current_index
            self._current_index = (self._current_index + 1) % len(self._keys)
            Logger.warning(f"Rotação de chave: {old_idx + 1} -> {self._current_index + 1}")
    
    async def get_next(self) -> Optional[str]:
        """Retorna próxima chave e rotaciona."""
        await self.rotate()
        return await self.get_current()


# =============================================================================
# CLIENTE GEMINI TTS
# =============================================================================

class GeminiTTSClient:
    """Cliente robusto para API Gemini TTS."""
    
    API_BASE: ClassVar[str] = "https://generativelanguage.googleapis.com/v1beta/models"
    
    def __init__(self, key_manager: KeyManager, settings: UserSettings):
        self.km = key_manager
        self.settings = settings
        self.cache = AudioCache()
        self.primary_model = settings.modelo_gemini
        self.backup_model = "gemini-2.0-flash-exp"
        self.current_model = self.primary_model
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=CONFIG.SESSION_TIMEOUT)
        self._session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
            self._session = None
    
    def _pcm_to_wav(self, pcm_data: bytes) -> bytes:
        """Converte dados PCM para WAV com header correto."""
        import struct
        
        if not pcm_data:
            return b""
        
        # Header WAV para PCM 16-bit, 24kHz, mono
        num_channels = 1
        sample_rate = CONFIG.PCM_SAMPLE_RATE
        bits_per_sample = 16
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        data_size = len(pcm_data)
        
        header = bytearray()
        header.extend(b"RIFF")
        header.extend(struct.pack("<I", 36 + data_size))
        header.extend(b"WAVE")
        header.extend(b"fmt ")
        header.extend(struct.pack("<I", 16))
        header.extend(struct.pack("<H", 1))  # PCM
        header.extend(struct.pack("<H", num_channels))
        header.extend(struct.pack("<I", sample_rate))
        header.extend(struct.pack("<I", byte_rate))
        header.extend(struct.pack("<H", block_align))
        header.extend(struct.pack("<H", bits_per_sample))
        header.extend(b"data")
        header.extend(struct.pack("<I", data_size))
        
        return bytes(header) + pcm_data
    
    async def synthesize(self, text: str, voice: str, output_path: str) -> bool:
        """
        Sintetiza texto para áudio com retry, cache e fallback de modelo.
        """
        # Verifica cache primeiro
        cached = self.cache.get(text, voice, "gemini")
        if cached:
            try:
                Path(output_path).write_bytes(cached)
                return True
            except Exception:
                pass
        
        if not self.km.has_keys:
            raise APIKeyError("Nenhuma chave API configurada")
        
        for attempt in range(CONFIG.MAX_RETRIES):
            try:
                success = await self._try_synthesize(text, voice, output_path)
                if success:
                    # Salva no cache
                    try:
                        audio_data = Path(output_path).read_bytes()
                        self.cache.put(text, voice, "gemini", audio_data)
                    except Exception:
                        pass
                    return True
                
            except RateLimitError:
                Logger.warning("Rate limit atingido, aguardando...")
                await asyncio.sleep(min(CONFIG.MAX_RETRY_DELAY, CONFIG.RETRY_BASE_DELAY * (2 ** attempt)))
                await self.km.rotate()
                
            except APIKeyError:
                Logger.error("Chave API inválida")
                await self.km.rotate()
                
            except NetworkError as e:
                Logger.warning(f"Erro de rede: {e}")
                await asyncio.sleep(5)
                
            except Exception as e:
                Logger.debug(f"Tentativa {attempt + 1} falhou: {e}")
                # Calcula delay com jitter
                delay = min(CONFIG.MAX_RETRY_DELAY, CONFIG.RETRY_BASE_DELAY * (2 ** attempt))
                jitter = (hash(text) % 100) / 100  # Pseudo-random jitter 0-1s
                await asyncio.sleep(delay + jitter)
        
        return False
    
    async def _try_synthesize(self, text: str, voice: str, output_path: str) -> bool:
        """Tenta uma única sintetização."""
        if not text.strip():
            return True
        
        key = await self.km.get_current()
        if not key:
            raise APIKeyError("Sem chaves disponíveis")
        
        url = f"{self.API_BASE}/{self.current_model}:generateContent?key={key}"
        
        payload = {
            "contents": [{"parts": [{"text": text}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {"voiceName": voice}
                    }
                }
            }
        }
        
        try:
            async with self._session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return await self._process_success_response(data, output_path)
                
                elif resp.status == 429:
                    raise RateLimitError("Too many requests")
                
                elif resp.status == 400:
                    # Erro de modelo, tenta fallback
                    if self.current_model == self.primary_model:
                        Logger.warning("Erro 400 no modelo primário, tentando backup...")
                        self.current_model = self.backup_model
                        return await self._try_synthesize(text, voice, output_path)
                    raise TTSError("Erro 400 persistente")
                
                elif resp.status == 403:
                    raise APIKeyError("Chave inválida ou sem permissão")
                
                else:
                    text = await resp.text()
                    raise TTSError(f"HTTP {resp.status}: {text[:100]}")
                    
        except aiohttp.ClientError as e:
            raise NetworkError(f"Erro de conexão: {e}")
    
    async def _process_success_response(self, data: dict, output_path: str) -> bool:
        """Processa resposta bem-sucedida da API."""
        try:
            candidates = data.get("candidates", [])
            if not candidates:
                raise TTSError("Resposta sem candidates")
            
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise TTSError("Resposta sem parts")
            
            inline_data = parts[0].get("inlineData", {})
            audio_b64 = inline_data.get("data", "")
            
            if not audio_b64:
                raise TTSError("Resposta sem dados de áudio")
            
            pcm_bytes = base64.b64decode(audio_b64)
            
            if len(pcm_bytes) < 100:
                raise TTSError("Dados de áudio muito pequenos")
            
            # Converte para WAV
            wav_data = self._pcm_to_wav(pcm_bytes)
            
            # Salva arquivo
            Path(output_path).write_bytes(wav_data)
            return True
            
        except Exception as e:
            Logger.debug(f"Erro ao processar resposta: {e}")
            return False


# =============================================================================
# CLIENTE EDGE TTS
# =============================================================================

class EdgeTTSClient:
    """Cliente para Edge TTS com cache."""
    
    def __init__(self, cache: AudioCache):
        self.cache = cache
    
    async def synthesize(self, text: str, voice: str, rate: str, output_path: str) -> bool:
        # Verifica cache
        cached = self.cache.get(text, voice, "edge")
        if cached:
            try:
                Path(output_path).write_bytes(cached)
                return True
            except Exception:
                pass
        
        try:
            
            
            # Microsoft bloqueou SSML customizado na versão 5.0.0+
            # Usamos apenas os parâmetros padrão rate/voice
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate
            )
            
            # Processa o áudio
            audio_data = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data.extend(chunk["data"])
            
            if audio_data:
                data_bytes = bytes(audio_data)
                Path(output_path).write_bytes(data_bytes)
                self.cache.put(text, voice, "edge", data_bytes)
                return True
            
            return False
            
        except Exception as e:
            Logger.error(f"Erro Edge TTS: {e}")
            return False



# =============================================================================
# PROCESSAMENTO DE TEXTO
# =============================================================================

class TextProcessor:
    """Processador avançado de texto."""
    
    @staticmethod
    def clean(text: str) -> str:
        """Limpa e normaliza texto."""
        if not text:
            return ""
        
        # Remove headers markdown
        text = re.sub(r'(?m)^#+\s*', '', text)
        # Remove caracteres de controle
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        # Resolve hifenização
        text = re.sub(r'-\n', '', text)
        # Normaliza quebras de linha
        text = re.sub(r'\n(?!\n)', ' ', text)
        # Remove markdown básico
        text = re.sub(r'[\*#`_]', '', text)
        # Normaliza espaços
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def smart_split(text: str, limit: int) -> List[str]:
        """
        Divide texto em chunks inteligentemente, respeitando limites
        de sentença e pontuação.
        """
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) <= limit:
            return [text]
        
        # Divide por sentenças
        sentences = re.split(r'(?<=[.!?…])\s+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # Sentença muito longa, divide por vírgula/ponto-vírgula
            if len(sentence) > limit:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                parts = re.split(r'(?<=[,;:])\s+', sentence)
                sub_chunk = ""
                for part in parts:
                    if len(sub_chunk) + len(part) < limit:
                        sub_chunk += part + " "
                    else:
                        if sub_chunk:
                            chunks.append(sub_chunk.strip())
                        sub_chunk = part + " "
                if sub_chunk:
                    chunks.append(sub_chunk.strip())
            
            # Cabe no chunk atual
            elif len(current_chunk) + len(sentence) < limit:
                current_chunk += sentence + " "
            
            # Fecha chunk atual e começa novo
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return [c for c in chunks if c]


# =============================================================================
# PÓS-PROCESSAMENTO DE ÁUDIO
# =============================================================================

class AudioPostProcessor:
    """Processamento final de áudio com FFmpeg."""
    
    @staticmethod
    def merge_files(file_list: List[str], output_path: str, apply_normalization: bool = True) -> bool:
        """Une múltiplos arquivos de áudio."""
        if not file_list:
            return False
        
        if len(file_list) == 1:
            shutil.copy(file_list[0], output_path)
            return True
        
        # Cria lista de concatenação
        list_file = Path(output_path).parent / "concat_list.txt"
        
        try:
            with open(list_file, 'w', encoding='utf-8') as f:
                for fp in file_list:
                    # Escapa aspas simples no path
                    safe_path = str(Path(fp).resolve()).replace("'", "'\\''")
                    f.write(f"file '{safe_path}'\n")
            
            # Build FFmpeg command
            cmd = [
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', str(list_file)
            ]
            
            if apply_normalization:
                # dynaudnorm + loudnorm para correção de volume
                cmd.extend([
                    '-af', 'dynaudnorm=f=150:g=15,loudnorm=I=-16:TP=-1.5:LRA=11'
                ])
            
            cmd.extend([
                '-c:a', 'libmp3lame',
                '-q:a', '2',
                output_path
            ])
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True
            )
            
            return result.returncode == 0
            
        except Exception as e:
            Logger.error(f"Erro ao unir arquivos: {e}")
            return False
        finally:
            # Limpa arquivo temporário
            try:
                list_file.unlink(missing_ok=True)
            except:
                pass
    
    @staticmethod
    def get_duration(file_path: str) -> float:
        """Retorna duração do áudio em segundos."""
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'default=noprint_wrappers=1:nokey=1', file_path],
                capture_output=True, text=True
            )
            return float(result.stdout.strip())
        except:
            return 0.0


# =============================================================================
# INTERFACE DE USUÁRIO (UI)
# =============================================================================

class TerminalUI:
    """Interface terminal interativa."""
    
    def __init__(self, settings: UserSettings):
        self.settings = settings
        self.catalog = VoiceCatalog()
    
    def clear(self):
        """Limpa tela."""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def header(self, title: str):
        """Exibe cabeçalho formatado."""
        self.clear()
        print(f"{Fore.CYAN}{Style.BRIGHT}{'='*50}")
        print(f"{Fore.WHITE}{Style.BRIGHT} 🎧 STUDIO AI v2.0 | {title}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'='*50}{Style.RESET_ALL}\n")
    
    def menu_principal(self) -> str:
        """Menu principal."""
        self.header("MENU PRINCIPAL")
        print("1. 🎙️  Novo Audiobook")
        print("2. 🔑  Gerenciar Chaves API")
        print("3. ⚙️   Preferências")
        print("4. 🧹  Limpar Cache")
        print("0. 🚪  Sair")
        return input("\n👉 Opção: ").strip()
    
    def menu_vozes(self, engine: str) -> Optional[str]:
        """Menu de seleção de voz."""
        voices = self.catalog.get_by_engine(engine)
        current = self.settings.voz_google if engine == "gemini" else self.settings.voz_edge
        
        while True:
            self.header(f"Selecionar Voz ({engine.upper()})")
            print(f"Atual: {Fore.GREEN}{current}{Style.RESET_ALL}\n")
            
            # Agrupa por categoria se Gemini
            if engine == "gemini":
                categories = {}
                for v in voices:
                    cat = v.category or "Outras"
                    categories.setdefault(cat, []).append(v)
                
                idx = 1
                voice_map = {}
                for cat in sorted(categories.keys()):
                    print(f"\n{Fore.YELLOW}--- {cat.upper()} ---{Style.RESET_ALL}")
                    for v in categories[cat]:
                        marker = "✅" if v.id == current else "  "
                        print(f"{marker} [{idx}] {v.name}")
                        voice_map[str(idx)] = v.id
                        idx += 1
            else:
                voice_map = {}
                for i, v in enumerate(voices, 1):
                    marker = "✅" if v.id == current else "  "
                    print(f"{marker} [{i}] {v.name}")
                    voice_map[str(i)] = v.id
            
            print(f"\n{Fore.CYAN}[M] ID Manual | [V] Voltar{Style.RESET_ALL}")
            opt = input("\n👉 Opção: ").strip().lower()
            
            if opt == 'v':
                return None
            if opt == 'm':
                manual = input("ID da voz: ").strip()
                return manual if manual else None
            if opt in voice_map:
                return voice_map[opt]
    
    def menu_preferencias(self):
        """Menu de preferências."""
        while True:
            self.header("⚙️  PREFERÊNCIAS")
            
            m_google = " (ATIVO)" if self.settings.motor_padrao == 'google' else ""
            m_edge = " (ATIVO)" if self.settings.motor_padrao == 'edge' else ""
            
            print(f"1. Motor Padrão [{self.settings.motor_padrao.upper()}]")
            print(f"2. 🗣️  Voz Gemini ({self.settings.voz_google}){m_google}")
            print(f"3. 🗣️  Voz Edge ({self.settings.voz_edge}){m_edge}")
            print(f"4. ⚡  Velocidade Edge ({self.settings.velocidade})")
            print(f"5. 📏 Tamanho do Chunk ({self.settings.limite_chunk})")
            print(f"6. 🤖 Modelo Gemini ({self.settings.modelo_gemini})")
            print("\n[V] Voltar")
            
            opt = input("\n👉 Opção: ").strip().lower()
            
            if opt == 'v':
                break
            elif opt == '1':
                self.settings.motor_padrao = "google" if self.settings.motor_padrao == "edge" else "edge"
                config_mgr.save(self.settings)
            elif opt == '2':
                nova = self.menu_vozes("gemini")
                if nova:
                    self.settings.voz_google = nova
                    config_mgr.save(self.settings)
            elif opt == '3':
                nova = self.menu_vozes("edge")
                if nova:
                    self.settings.voz_edge = nova
                    config_mgr.save(self.settings)
            elif opt == '4':
                v = input("Nova velocidade (ex: +20%, -10%): ").strip()
                if '%' in v:
                    self.settings.velocidade = v
                    config_mgr.save(self.settings)
            elif opt == '5':
                try:
                    novo = int(input(f"Novo limite ({CONFIG.MIN_CHUNK_SIZE}-{CONFIG.MAX_CHUNK_SIZE}): "))
                    if CONFIG.MIN_CHUNK_SIZE <= novo <= CONFIG.MAX_CHUNK_SIZE:
                        self.settings.limite_chunk = novo
                        config_mgr.save(self.settings)
                except ValueError:
                    pass
            elif opt == '6':
                print("\nModelos disponíveis:")
                print("1. gemini-2.5-flash-preview-tts (Recomendado)")
                print("2. gemini-2.0-flash-exp (Fallback)")
                esc = input("Opção: ").strip()
                if esc == "1":
                    self.settings.modelo_gemini = "gemini-2.5-flash-preview-tts"
                elif esc == "2":
                    self.settings.modelo_gemini = "gemini-2.0-flash-exp"
                config_mgr.save(self.settings)
    
    def menu_chaves(self):
        """Menu de gerenciamento de chaves."""
        while True:
            self.header("🔑 GERENCIADOR DE CHAVES")
            
            keys = self.settings.google_keys
            if not keys:
                print(f"{Fore.RED}Nenhuma chave configurada.{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}{len(keys)} chave(s) configurada(s):{Style.RESET_ALL}")
                for i, k in enumerate(keys, 1):
                    masked = k[:4] + "•" * 8 + k[-4:] if len(k) > 12 else "•" * len(k)
                    print(f"   {i}. {masked}")
            
            print(f"\n{Fore.CYAN}[A] Adicionar | [R] Remover | [L] Limpar | [V] Voltar{Style.RESET_ALL}")
            opt = input("\n👉 Opção: ").strip().lower()
            
            if opt == 'v':
                break
            elif opt == 'a':
                print(f"{Fore.CYAN}Cole as chaves separadas por vírgula:{Style.RESET_ALL}")
                entrada = input("> ").strip()
                if entrada:
                    novas = [k.strip() for k in entrada.split(',') if len(k.strip()) > 20]
                    if novas:
                        self.settings.google_keys.extend(novas)
                        config_mgr.save(self.settings)
                        Logger.success(f"{len(novas)} chave(s) adicionada(s)!")
                        time.sleep(1)
            elif opt == 'r' and keys:
                try:
                    idx = int(input("Número da chave para remover: ")) - 1
                    if 0 <= idx < len(keys):
                        removed = self.settings.google_keys.pop(idx)
                        config_mgr.save(self.settings)
                        Logger.success("Chave removida!")
                        time.sleep(1)
                except ValueError:
                    pass
            elif opt == 'l':
                if input("Confirma limpar todas? (s/n): ").lower() == 's':
                    self.settings.google_keys = []
                    config_mgr.save(self.settings)
    
    def file_browser(self) -> Optional[str]:
        """Navegador de arquivos interativo."""
        # Detecta diretório inicial adequado
        path = Path("/sdcard/Download" if os.path.exists("/sdcard/Download") else "/sdcard" if os.path.exists("/sdcard") else Path.home())
        
        while True:
            self.header(f"📂 {path.name}")
            
            try:
                items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            except PermissionError:
                Logger.error("Sem permissão para acessar este diretório")
                path = path.parent
                continue
            
            # Filtra itens relevantes
            dirs = [x for x in items if x.is_dir() and not x.name.startswith('.')]
            files = [x for x in items if x.is_file() and x.suffix.lower() in ('.txt', '.md', '.pdf', '.epub')]
            
            print(f"{Fore.CYAN}--- DIRETÓRIOS ---{Style.RESET_ALL}")
            choices = {'0': ('..', path.parent)}
            idx = 1
            
            if path != Path('/'):
                print("[0] 🔙 ..")
            
            for d in dirs[:10]:
                print(f"[{idx}] 📁 {d.name}")
                choices[str(idx)] = ('dir', d)
                idx += 1
            
            print(f"\n{Fore.CYAN}--- ARQUIVOS ---{Style.RESET_ALL}")
            for f in files:
                print(f"[{idx}] 📄 {f.name}")
                choices[str(idx)] = ('file', f)
                idx += 1
            
            print(f"\n{Fore.CYAN}[M] Caminho manual | [X] Cancelar{Style.RESET_ALL}")
            opt = input("\n👉 Opção: ").strip().lower()
            
            if opt == 'x':
                return None
            if opt == 'm':
                manual = input("Caminho completo: ").strip()
                return manual if os.path.exists(manual) else None
            
            if opt in choices:
                tipo, alvo = choices[opt]
                if tipo == 'dir':
                    path = alvo
                else:
                    return str(alvo)
    
    def text_input_manual(self) -> str:
        """Entrada de texto manual multi-linha."""
        self.header("✍️  ENTRADA MANUAL")
        print("Cole ou digite o texto. Digite 'FIM' sozinho na última linha para terminar:\n")
        
        lines = []
        while True:
            try:
                line = input()
                if line.strip().upper() == 'FIM':
                    break
                lines.append(line)
            except EOFError:
                break
        
        return '\n'.join(lines)


# =============================================================================
# MOTOR DE CONVERSÃO PRINCIPAL
# =============================================================================

class ConversionEngine:
    """Motor principal de conversão TTS."""
    
    def __init__(self, settings: UserSettings):
        self.settings = settings
        self.text_processor = TextProcessor()
        self.audio_processor = AudioPostProcessor()
        self.cache = AudioCache()
        self.ui = TerminalUI(settings)
    
    async def convert(self):
        """Fluxo principal de conversão."""
        # Seleção de fonte
        source = self.ui.file_browser()
        if source is None:
            return
        
        # Coleta de texto
        if source == "":
            text = self.ui.text_input_manual()
            base_name = "manual"
            source_dir = str(Path.home())
        else:
            source_path = Path(source)
            base_name = source_path.stem
            source_dir = str(source_path.parent)
            
            # Extrai texto baseado na extensão
            text = await self._extract_text(source)
        
        if not text:
            Logger.error("Nenhum texto extraído")
            input("Pressione Enter...")
            return
        
        # Processamento do texto
        text = self.text_processor.clean(text)
        if not text:
            Logger.error("Texto vazio após limpeza")
            return
        
        # Configurações de saída
        self.ui.header("🚀 CONFIGURAÇÃO DE SAÍDA")
        Logger.info(f"Arquivo: {base_name}")
        Logger.info(f"Motor: {self.settings.motor_padrao.upper()}")
        
        if self.settings.motor_padrao == "google":
            Logger.info(f"Voz: {self.settings.voz_google}")
            Logger.info(f"Modelo: {self.settings.modelo_gemini}")
            
            if not shutil.which("ffmpeg"):
                Logger.error("FFmpeg não encontrado. Instale com: pkg install ffmpeg")
                input("Pressione Enter...")
                return
        else:
            Logger.info(f"Voz: {self.settings.voz_edge}")
        
        # Confirmação
        if input("\nPressione Enter para iniciar (ou 'n' para cancelar): ").lower() == 'n':
            return
        
        # Configuração de saída
        default_name = f"{base_name}.mp3"
        nome_out = input(f"Nome do arquivo [{default_name}]: ").strip() or default_name
        if not nome_out.endswith('.mp3'):
            nome_out += '.mp3'
        
        output_path = os.path.join(source_dir, nome_out)
        
        # Execução
        try:
            if self.settings.motor_padrao == "google":
                await self._convert_gemini(text, output_path)
            else:
                await self._convert_edge(text, output_path)
            
            # Oferece reprodução
            if input("\n🎵 Tocar arquivo? (s/n): ").lower() == 's':
                self._play_audio(output_path)
                
        except Exception as e:
            Logger.error(f"Erro na conversão: {e}")
            traceback.print_exc()
            input("Pressione Enter...")
    
    async def _extract_text(self, filepath: str) -> str:
        """Extrai texto de diferentes formatos de arquivo."""
        path = Path(filepath)
        
        if path.suffix.lower() == '.pdf':
            try:
                import pypdf
                reader = pypdf.PdfReader(filepath)
                return "\n".join(page.extract_text() or "" for page in reader.pages)
            except ImportError:
                Logger.error("Instale pypdf: pip install pypdf")
                return ""
            except Exception as e:
                Logger.error(f"Erro ao ler PDF: {e}")
                return ""
        
        elif path.suffix.lower() == '.epub':
            try:
                import ebooklib
                from ebooklib import epub
                from bs4 import BeautifulSoup
                
                book = epub.read_epub(filepath)
                texts = []
                for item in book.get_items():
                    if item.get_type() == ebooklib.ITEM_DOCUMENT:
                        soup = BeautifulSoup(item.get_content(), 'html.parser')
                        texts.append(soup.get_text())
                return "\n".join(texts)
            except ImportError:
                Logger.error("Instale: pip install ebooklib beautifulsoup4")
                return ""
            except Exception as e:
                Logger.error(f"Erro ao ler EPUB: {e}")
                return ""
        
        else:  # TXT, MD, etc
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            except Exception as e:
                Logger.error(f"Erro ao ler arquivo: {e}")
                return ""

    async def _convert_gemini(self, text: str, output_path: str):
        """Conversão usando Gemini TTS."""
        # Prepara chunks
        chunks = self.text_processor.smart_split(text, self.settings.limite_chunk)
        total = len(chunks)
        
        Logger.info(f"Processando {total} chunks...")
        
        # Setup
        km = KeyManager(self.settings.google_keys)
        if not km.has_keys:
            raise ValueError("Nenhuma chave API configurada")
        
        temp_files = []
        temp_dir = Path(output_path).parent / f".temp_{int(time.time())}"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            async with GeminiTTSClient(km, self.settings) as client:
                for idx, chunk in enumerate(chunks, 1):
                    Logger.progress(idx, total, "Chunk")
                    
                    temp_file = temp_dir / f"chunk_{idx:04d}.wav"
                    chunk_sucesso = False
                    
                    # Loop infinito até que ESTE chunk seja convertido com sucesso
                    while not chunk_sucesso:
                        chunk_sucesso = await client.synthesize(
                            chunk, 
                            self.settings.voz_google, 
                            str(temp_file)
                        )
                        
                        if chunk_sucesso and temp_file.exists():
                            temp_files.append(str(temp_file))
                        else:
                            # Se falhar todas as tentativas do client (incluindo rotações),
                            # paramos aqui, esperamos 60s e tentamos de novo o MESMO chunk.
                            print() # Quebra de linha para não sobrescrever a barra de progresso
                            Logger.error(f"❌ Falha crítica no chunk {idx}. Todas as chaves limitadas.")
                            Logger.warning("⏳ Aguardando 60 segundos para resfriar a API e tentar novamente...")
                            await asyncio.sleep(60)
                            Logger.info(f"🔄 Retomando tentativa do chunk {idx}...")
            
            # --- Fim do Loop For ---
            
            print()  # Nova linha após progresso
            
            if not temp_files:
                raise AudioProcessingError("Nenhum áudio gerado")
            
            # Pós-processamento
            Logger.info("Masterizando áudio...")
            success = self.audio_processor.merge_files(temp_files, output_path)
            
            if success:
                duration = self.audio_processor.get_duration(output_path)
                Logger.success(f"✅ Concluído: {output_path}")
                Logger.info(f"⏱️  Duração: {duration/60:.1f} minutos")
            else:
                raise AudioProcessingError("Falha na masterização")
                
        finally:
            # Limpeza
            self._cleanup(temp_dir, temp_files)

    
    async def _convert_edge(self, text: str, output_path: str):
        """Conversão usando Edge TTS com concorrência e RETRY automático."""
        client = EdgeTTSClient(self.cache)
        limite_caracteres = self.settings.limite_chunk
        
        # Define o limite de tarefas simultâneas
        CONCURRENCY_LIMIT = 5 
        semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

        if len(text) > limite_caracteres:
            chunks = self.text_processor.smart_split(text, limite_caracteres)
            total_chunks = len(chunks)
            Logger.info(f"Iniciando conversão simultânea de {total_chunks} chunks (Limite: {CONCURRENCY_LIMIT})...")
            
            temp_dir = Path(output_path).parent / f".temp_edge_{int(time.time())}"
            temp_dir.mkdir(exist_ok=True)
            
            # Lista para manter a ordem correta dos arquivos
            temp_files = [str(temp_dir / f"chunk_{i+1:04d}.mp3") for i in range(total_chunks)]
            
            async def semaphore_task(chunk_text, chunk_idx, chunk_path):
                async with semaphore:
                    max_retries = 5  # Aumentado para 5 tentativas
                    base_delay = 2.0
                    
                    for attempt in range(max_retries):
                        # Tenta converter o chunk
                        success = await client.synthesize(
                            chunk_text,
                            self.settings.voz_edge,
                            self.settings.velocidade,
                            chunk_path
                        )
                        
                        if success:
                            Logger.info(f"✔ Chunk {chunk_idx}/{total_chunks} concluído.")
                            return True
                        else:
                            # Calcula espera: 2s, 4s, 8s... (Backoff Exponencial)
                            wait_time = base_delay * (2 ** attempt)
                            Logger.warning(f"⚠️ Falha no chunk {chunk_idx} (Tentativa {attempt+1}/{max_retries}). Aguardando {wait_time}s...")
                            await asyncio.sleep(wait_time)
                    
                    # Se esgotar as tentativas
                    Logger.error(f"❌ DESISTINDO do chunk {chunk_idx} após {max_retries} tentativas.")
                    return False

            # Cria a lista de tarefas
            tasks = [
                semaphore_task(chunks[i], i + 1, temp_files[i]) 
                for i in range(total_chunks)
            ]
            
            # Executa todas simultaneamente respeitando o semáforo
            results = await asyncio.gather(*tasks)
            
            if all(results):
                Logger.info("Unindo partes e masterizando...")
                self.audio_processor.merge_files(temp_files, output_path, apply_normalization=False)
                Logger.success(f"✅ Audiobook completo gerado: {output_path}")
            else:
                Logger.error("❌ ERRO CRÍTICO: Alguns chunks falharam definitivamente. O áudio está incompleto.")
            
            self._cleanup(temp_dir, temp_files)
        
        else:
            # Texto pequeno: Processamento simples com retry básico
            # Não cria arquivos temporários, converte direto para o output_path
            success = False
            for attempt in range(3):
                success = await client.synthesize(
                    text, self.settings.voz_edge, self.settings.velocidade, output_path
                )
                if success:
                    Logger.success(f"✅ Concluído: {output_path}")
                    break
                else:
                    Logger.warning(f"⚠️ Tentativa {attempt+1} falhou para texto curto. Retentando...")
                    await asyncio.sleep(2)
            
            if not success:
                Logger.error("Falha ao converter texto curto.")

    
    def _play_audio(self, file_path: str):
        """Reproduz arquivo de áudio de forma segura (sem injeção de comando)."""
        import platform
        
        try:
            system = platform.system().lower()
            
            if system == "windows":
                # Windows: usa start através de cmd
                subprocess.run(
                    ["cmd", "/c", "start", "", file_path],
                    shell=False,
                    check=False,
                    capture_output=True
                )
            elif system == "darwin":
                # macOS
                subprocess.run(
                    ["open", file_path],
                    shell=False,
                    check=False,
                    capture_output=True
                )
            elif os.path.exists("/data/data/com.termux"):
                # Termux (Android)
                subprocess.run(
                    ["termux-media-player", "play", file_path],
                    shell=False,
                    check=False,
                    capture_output=True
                )
            else:
                # Linux e outros
                subprocess.run(
                    ["xdg-open", file_path],
                    shell=False,
                    check=False,
                    capture_output=True
                )
        except Exception as e:
            Logger.warning(f"Não foi possível reproduzir o áudio: {e}")

    def _cleanup(self, temp_dir: Path, temp_files: List[str]):
        """Remove arquivos temporários e diretório de forma segura."""
        try:
            # Remove arquivos individuais
            for f in temp_files:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except Exception:
                        pass
            
            # Remove o diretório vazio (ou com sobras)
            if temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                
            Logger.debug("Limpeza de arquivos temporários concluída.")
            
        except Exception as e:
            Logger.debug(f"Aviso não-crítico na limpeza: {e}")


# =============================================================================
# APLICAÇÃO PRINCIPAL
# =============================================================================

class StudioAIApp:
    """Aplicação principal."""
    
    def __init__(self):
        self.settings = config_mgr.load()
        self.ui = TerminalUI(self.settings)
        self.engine = ConversionEngine(self.settings)
        self.cache = AudioCache()
    
    async def run(self):
        """Loop principal."""
        # Limpa cache antigo na inicialização
        self.cache.clear_old(days=7)
        
        while True:
            try:
                opt = self.ui.menu_principal()
                
                if opt == '0' or opt.lower() == 'sair':
                    Logger.info("Até logo! 👋")
                    break
                elif opt == '1':
                    await self.engine.convert()
                elif opt == '2':
                    self.ui.menu_chaves()
                elif opt == '3':
                    self.ui.menu_preferencias()
                    self.engine = ConversionEngine(self.settings)  # Recria com novas settings
                elif opt == '4':
                    removed = self.cache.clear_old(days=0)  # Limpa tudo
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


# =============================================================================
# PONTO DE ENTRADA
# =============================================================================

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
