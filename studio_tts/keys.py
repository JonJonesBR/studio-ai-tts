"""
Studio AI TTS - Gerenciador de Chaves API
"""

import asyncio
from typing import List, Optional

from .logger import Logger


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
