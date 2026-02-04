"""
Studio AI TTS - Cliente Edge TTS
"""

from pathlib import Path

import edge_tts

from ..cache import AudioCache
from ..logger import Logger


class EdgeTTSClient:
    """Cliente para Edge TTS com cache."""
    
    def __init__(self, cache: AudioCache):
        self.cache = cache
    
    async def synthesize(self, text: str, voice: str, rate: str, output_path: str) -> bool:
        """Sintetiza usando Edge TTS."""
        # Verifica cache
        cached = self.cache.get(text, voice, "edge")
        if cached:
            try:
                # Converte WAV cacheado para MP3 se necessário
                # Edge já retorna MP3, então salvamos direto
                Path(output_path).write_bytes(cached)
                return True
            except Exception:
                pass
        
        try:
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            audio_data = bytearray()
            
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data.extend(chunk["data"])
            
            if audio_data:
                # Salva no formato original (MP3)
                data_bytes = bytes(audio_data)
                Path(output_path).write_bytes(data_bytes)
                # Também salva no cache (como MP3)
                self.cache.put(text, voice, "edge", data_bytes)
                return True
            
            return False
            
        except Exception as e:
            Logger.error(f"Erro Edge TTS: {e}")
            return False
