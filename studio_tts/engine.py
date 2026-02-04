"""
Studio AI TTS - Motor de Conversão
"""

import asyncio
import os
import shutil
import time
import traceback
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from colorama import Fore, Style

from .config import CONFIG, UserSettings
from .logger import Logger, TimeEstimator
from .cache import AudioCache, HistoryManager
from .keys import KeyManager
from .exceptions import AudioProcessingError
from .ui import TerminalUI

from .processors.text import TextProcessor
from .processors.audio import AudioPostProcessor
from .clients.gemini import GeminiTTSClient
from .clients.edge import EdgeTTSClient


class ConversionEngine:
    """Motor principal de conversão TTS."""
    
    def __init__(self, settings: UserSettings):
        self.settings = settings
        self.text_processor = TextProcessor()
        self.audio_processor = AudioPostProcessor()
        self.cache = AudioCache()
        self.ui = TerminalUI(settings)
        self.history: Optional[HistoryManager] = None  # Será injetado pelo App
    
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
        
        # Estimação de tempo
        est_seconds, est_str = TimeEstimator.estimate(text, self.settings.motor_padrao)
        Logger.info(f"⏱️  Tempo estimado: {est_str}")
        
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
            
            # Salva no histórico
            if self.history and Path(output_path).exists():
                duration = self.audio_processor.get_duration(output_path)
                voice = self.settings.voz_google if self.settings.motor_padrao == "google" else self.settings.voz_edge
                self.history.add(source, output_path, duration, self.settings.motor_padrao, voice)
            
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
        
        elif path.suffix.lower() == '.docx':
            try:
                from docx import Document
                doc = Document(filepath)
                return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            except ImportError:
                Logger.error("Instale python-docx: pip install python-docx")
                return ""
            except Exception as e:
                Logger.error(f"Erro ao ler DOCX: {e}")
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
        
        temp_dir = Path(output_path).parent / f".temp_{int(time.time())}"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            start_time = time.time()
            semaphore = asyncio.Semaphore(CONFIG.MAX_CONCURRENT)
            results: Dict[int, str] = {}  # idx -> filepath
            completed = [0]  # Contador para progresso
            
            async def process_chunk(idx: int, chunk: str, client: GeminiTTSClient):
                """Processa um chunk com controle de concorrência."""
                async with semaphore:
                    temp_file = temp_dir / f"chunk_{idx:04d}.wav"
                    chunk_sucesso = False
                    
                    while not chunk_sucesso:
                        chunk_sucesso = await client.synthesize(
                            chunk,
                            self.settings.voz_google,
                            str(temp_file)
                        )
                        
                        if chunk_sucesso and temp_file.exists():
                            results[idx] = str(temp_file)
                            completed[0] += 1
                            elapsed = time.time() - start_time
                            Logger.progress(completed[0], total, "Chunks", elapsed)
                        else:
                            Logger.debug(f"Chunk {idx} falhou, aguardando...")
                            await asyncio.sleep(30)
                    
                    return idx
            
            async with GeminiTTSClient(km, self.settings) as client:
                # Cria todas as tasks
                tasks = [process_chunk(i, c, client) for i, c in enumerate(chunks, 1)]
                # Executa em paralelo (limitado pelo semáforo)
                await asyncio.gather(*tasks)
            
            print()  # Nova linha após progresso
            
            # Ordena os resultados
            temp_files = [results[i] for i in sorted(results.keys())]
            
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
            self._cleanup(temp_dir, list(results.values()) if 'results' in dir() else [])

    
    async def _convert_edge(self, text: str, output_path: str):
        """Conversão usando Edge TTS."""
        client = EdgeTTSClient(self.cache)
        
        Logger.info("Gerando áudio com Edge TTS...")
        
        # Edge TTS gera tudo de uma vez (sem chunks para arquivos pequenos)
        # ou podemos dividir para arquivos grandes
        if len(text) > 5000:
            chunks = self.text_processor.smart_split(text, 5000)
            temp_files = []
            temp_dir = Path(output_path).parent / f".temp_{int(time.time())}"
            temp_dir.mkdir(exist_ok=True)
            
            try:
                start_time = time.time()
                for idx, chunk in enumerate(chunks, 1):
                    elapsed = time.time() - start_time
                    Logger.progress(idx, len(chunks), "Chunk", elapsed)
                    temp_file = temp_dir / f"chunk_{idx:04d}.mp3"
                    
                    success = await client.synthesize(
                        chunk,
                        self.settings.voz_edge,
                        self.settings.velocidade,
                        str(temp_file)
                    )
                    
                    if success:
                        temp_files.append(str(temp_file))
                
                print()
                Logger.info("Unindo partes...")
                self.audio_processor.merge_files(temp_files, output_path, apply_normalization=False)
                
            finally:
                self._cleanup(temp_dir, temp_files)
        else:
            # Arquivo pequeno: gera direto
            success = await client.synthesize(
                text,
                self.settings.voz_edge,
                self.settings.velocidade,
                output_path
            )
            
            if success:
                Logger.success(f"✅ Concluído: {output_path}")
            else:
                raise AudioProcessingError("Falha na geração")
    
    async def convert_batch(self, files: List[str]):
        """Converte múltiplos arquivos em sequência."""
        results = []
        total = len(files)
        start_time = time.time()
        
        self.ui.header(f"📚 MODO LOTE - {total} arquivo(s)")
        Logger.info(f"Motor: {self.settings.motor_padrao.upper()}")
        
        if self.settings.motor_padrao == "google":
            if not self.settings.google_keys:
                Logger.error("Nenhuma chave API configurada para Gemini")
                input("Pressione Enter...")
                return
            if not shutil.which("ffmpeg"):
                Logger.error("FFmpeg não encontrado.")
                input("Pressione Enter...")
                return
        
        # Confirmação
        if input("\nPressione Enter para iniciar (ou 'n' para cancelar): ").lower() == 'n':
            return
        
        for idx, filepath in enumerate(files, 1):
            file_start = time.time()
            filename = Path(filepath).name
            Logger.info(f"\n📁 [{idx}/{total}] Processando: {filename}")
            
            try:
                # Extrai texto
                text = await self._extract_text(filepath)
                if not text:
                    results.append((filename, False, "Texto vazio"))
                    continue
                
                # Processa
                text = self.text_processor.clean(text)
                if not text:
                    results.append((filename, False, "Texto vazio após limpeza"))
                    continue
                
                # Output path
                output_path = str(Path(filepath).with_suffix('.mp3'))
                
                # Estimação
                _, est_str = TimeEstimator.estimate(text, self.settings.motor_padrao)
                Logger.info(f"⏱️  Estimado: {est_str}")
                
                if self.settings.motor_padrao == "google":
                    await self._convert_gemini(text, output_path)
                else:
                    await self._convert_edge(text, output_path)
                
                elapsed = time.time() - file_start
                results.append((filename, True, f"{TimeEstimator.format_time(elapsed)}"))
                
            except Exception as e:
                results.append((filename, False, str(e)[:50]))
        
        # Relatório final
        self._print_batch_report(results, time.time() - start_time)
    
    def _print_batch_report(self, results: List[Tuple[str, bool, str]], total_time: float):
        """Imprime relatório do processamento em lote."""
        print("\n" + "=" * 50)
        Logger.info("📊 RELATÓRIO DO MODO LOTE")
        print("=" * 50)
        
        success = sum(1 for _, ok, _ in results if ok)
        failed = len(results) - success
        
        for filename, ok, info in results:
            if ok:
                print(f"{Fore.GREEN}✅ {filename} ({info}){Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ {filename}: {info}{Style.RESET_ALL}")
        
        print("\n" + "-" * 50)
        Logger.success(f"Concluído: {success}/{len(results)} arquivos")
        if failed > 0:
            Logger.warning(f"Falhas: {failed}")
        Logger.info(f"Tempo total: {TimeEstimator.format_time(total_time)}")
        input("\nPressione Enter para continuar...")
    
    def _cleanup(self, temp_dir: Path, temp_files: List[str]):
        """Limpa arquivos temporários."""
        try:
            for f in temp_files:
                Path(f).unlink(missing_ok=True)
            temp_dir.rmdir()
        except Exception:
            pass
    
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
