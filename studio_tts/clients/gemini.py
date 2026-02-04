"""
Studio AI TTS - Cliente Gemini TTS
"""

import base64
import struct
import asyncio
from typing import ClassVar, Optional
from pathlib import Path

import aiohttp

from ..config import CONFIG, UserSettings
from ..keys import KeyManager
from ..cache import AudioCache
from ..logger import Logger
from ..exceptions import TTSError, APIKeyError, RateLimitError, NetworkError


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
                    raise TTSError(f"Erro 400 persistente: {await resp.text()}")
                
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
