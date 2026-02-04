"""
Studio AI TTS - Pós-processamento de Áudio
"""

import shutil
import subprocess
from pathlib import Path
from typing import List

from ..logger import Logger


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
                    safe_path = str(Path(fp).resolve()).replace("'", "'\\''")
                    f.write(f"file '{safe_path}'\n")
            
            # Build FFmpeg command
            cmd = [
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', str(list_file)
            ]
            
            if apply_normalization:
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
            
            if result.returncode != 0:
                Logger.debug(f"FFmpeg error: {result.stderr}")
            
            return result.returncode == 0
            
        except Exception as e:
            Logger.error(f"Erro ao unir arquivos: {e}")
            return False
        finally:
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
