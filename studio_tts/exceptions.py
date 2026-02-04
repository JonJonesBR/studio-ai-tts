"""
Studio AI TTS - Exceções customizadas
"""


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
