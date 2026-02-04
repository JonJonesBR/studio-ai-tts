"""
Studio AI TTS - Processamento de Texto
"""

import re
from typing import List


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
