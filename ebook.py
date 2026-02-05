#!/usr/bin/env python3
"""
Studio AI - Audio Scripting (Versão 5.0 - Slow Motion)
Foco: RITMO LENTO E PAUSADO.
Estratégia: Isola cada frase em uma linha e força pausas duplas entre parágrafos.
Ideal para quem acha a narração padrão muito rápida.
"""

import os
import re
import sys
import time
import textwrap
from pathlib import Path
from typing import Optional

# =============================================================================
# CONFIGURAÇÃO DE CORES
# =============================================================================
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    class Fore: CYAN = GREEN = YELLOW = RED = BLUE = MAGENTA = ""
    class Style: BRIGHT = RESET_ALL = ""
    def init(**kwargs): pass

# =============================================================================
# REGRAS DE SUBSTITUIÇÃO
# =============================================================================

class TextRules:
    ABREVIACOES = {
        r'\bSr\.': 'Senhor', r'\bSra\.': 'Senhora', r'\bDr\.': 'Doutor',
        r'\bDra\.': 'Doutora', r'\bSrta\.': 'Senhorita', r'\bV\.Exa\.': 'Vossa Excelência',
        r'\bProf\.': 'Professor', r'\bCap\.': 'Capitão', r'\bpág\.': 'página',
        r'\bcap\.': 'capítulo', r'\bvol\.': 'volume', r'\bnum\.': 'número',
        r'\betc\.': 'etcetera', r'\bex\.': 'exemplo', r'\bobs\.': 'observação',
        r'\btel\.': 'telefone', r'\bwww\.': 'dáblio dáblio dáblio ponto ',
    }

    SIMBOLOS = {
        r'%': ' por cento', r'km/h': ' quilômetros por hora', r'\bkg\b': ' quilos',
        r'\bkm\b': ' quilômetros', r'\bcm\b': ' centímetros', r'\bmm\b': ' milímetros',
        r'\bm\b': ' metros', r'°C': ' graus celsius', r'°': ' graus',
        r'\$': ' dólares ', r'R\$': ' reais ', r'€': ' euros ', r'£': ' libras ',
        r'&': ' e ', r'@': ' arroba ', r'#': ' hashtag ',
    }

    ROMANOS = {
        r'\bXVIII\b': 'dezoito', r'\bXVII\b': 'dezessete', r'\bXVI\b': 'dezesseis',
        r'\bXV\b': 'quinze', r'\bXIV\b': 'quatorze', r'\bXIII\b': 'treze',
        r'\bXII\b': 'doze', r'\bXI\b': 'onze', r'\bIX\b': 'nove',
        r'\bVIII\b': 'oito', r'\bVII\b': 'sete', r'\bVI\b': 'seis',
        r'\bIV\b': 'quatro', r'\bIII\b': 'três', r'\bII\b': 'dois', r'\bI\b': 'um',
        r'\bXXI\b': 'vinte e um', r'\bXX\b': 'vinte', r'\bXIX\b': 'dezenove',
        r'\bX\b': 'dez', r'\bV\b': 'cinco'
    }

# =============================================================================
# MOTOR DE PROCESSAMENTO
# =============================================================================

class AudioScripter:
    """Transforma texto bruto em roteiro de áudio com ritmo controlado."""
    
    def __init__(self):
        # 1. Regex para texto espaçado
        self.rx_spaced = re.compile(r'\b(?:[a-zA-ZÀ-ÿ]\s){2,}[a-zA-ZÀ-ÿ]\b')
        
        # 2. Cabeçalhos
        self.rx_headers = re.compile(
            r'(?im)^\s*(?P<tag>Capítulo|Chapter|Parte|Part|Livro|Book|Prólogo|Prologue|Epílogo|Epilogue|Prefácio|Introdução|Conclusão)'
            r'(?P<num>\s+(?:[\d]+|[IVXLCDM]+))?'
            r'(?P<sep>\s*[:.-])?'
            r'(?P<content>.*)$'
        )

        # Regexes utilitárias
        self.rx_hyphen = re.compile(r'(\w)-\n\s*(\w)')
        self.rx_broken_line = re.compile(r'(?<![.?!])\n(?=[a-zà-ú])')
        self.rx_single_break = re.compile(r'(?<!\n)\n(?!\n)') 
        self.rx_spaces = re.compile(r'\s+')
        self.rx_brackets = re.compile(r'\[.*?\]')
        self.rx_dialog = re.compile(r'[\u2010-\u2015]')
        
        # Detecta pontuação final de frase para adicionar QUEBRA DE LINHA
        # Isso força o isolamento da frase
        self.rx_sentence_end = re.compile(r'([.?!])\s+([A-ZÀ-Ú])')

    def process(self, text: str) -> str:
        if not text: return ""
        
        Logger.info("🧹 Aplicando modo SLOW MOTION (Pausas Estendidas)...")

        # --- FASE 1: Limpeza ---
        text = text.replace('\\', ' ') 
        text = self.rx_brackets.sub('', text)
        text = self.rx_hyphen.sub(r'\1\2', text)
        text = self.rx_broken_line.sub(' ', text)
        
        # --- FASE 2: Títulos ---
        text = self.rx_spaced.sub(lambda m: m.group(0).replace(" ", ""), text)

        def fix_headers(m):
            tag = m.group('tag').title()
            num = m.group('num') or ""
            content = m.group('content').strip()
            header = f"{tag}{num}"
            
            # Adiciona PAUSA TRIPLA no título
            if content:
                if content.startswith('.') or content.startswith(':'): content = content[1:].strip()
                return f"\n\n\n{header}. ... ...\n\n\n{content}"
            else:
                return f"\n\n\n{header}. ... ...\n\n\n"
            
        text = self.rx_headers.sub(fix_headers, text)

        # --- FASE 3: Normalização ---
        text = self.rx_single_break.sub(' ', text)
        text = self.rx_spaces.sub(' ', text)

        # --- FASE 4: Fonética ---
        Logger.info("🗣️  Ajustando termos...")
        for p, r in TextRules.ABREVIACOES.items(): text = re.sub(p, r, text, flags=re.IGNORECASE)
        for p, r in TextRules.SIMBOLOS.items(): text = re.sub(p, r, text)
        for p, r in TextRules.ROMANOS.items(): text = re.sub(p, r, text)

        # --- FASE 5: Pontuação e Isolamento de Frases (RADICAL) ---
        text = self.rx_dialog.sub('—', text)
        text = re.sub(r'(\s*—\s*)', r'\n— ', text)
        
        # AQUI ESTÁ A MUDANÇA PRINCIPAL:
        # Substitui "Ponto + Espaço" por "Ponto + Quebra de Linha + Espaço"
        # Cada frase vira um bloco isolado.
        text = self.rx_sentence_end.sub(r'\1\n\n\2', text)
        text = text.replace('…', '...')

        # --- FASE 6: Pausa Dupla entre Parágrafos ---
        # Detecta quebras grandes e insere PAUSA DUPLA (... ...)
        
        # Marcador temporário para parágrafos originais
        text = re.sub(r'\n\s*\n', '<PARAGRAFO>', text)
        
        # Injeta a pausa longa
        # O Edge TTS lê "..." como uma pausa de ~0.5s. Duas vezes = ~1s.
        text = text.replace('<PARAGRAFO>', " ... ...\n\n\n")
        
        # Limpeza de excessos
        text = text.replace('... ... ...', '... ...') 
        
        return text.strip()

# =============================================================================
# MANIPULAÇÃO DE ARQUIVOS
# =============================================================================

class FileHandler:
    @staticmethod
    def read_file(path: str) -> str:
        p = Path(path)
        ext = p.suffix.lower()
        try:
            if ext == '.pdf':
                import pypdf
                reader = pypdf.PdfReader(path)
                return "\n".join(page.extract_text() or "" for page in reader.pages)
            elif ext == '.epub':
                import ebooklib
                from ebooklib import epub
                from bs4 import BeautifulSoup
                import warnings
                warnings.filterwarnings("ignore")
                book = epub.read_epub(path)
                texts = []
                for item in book.get_items():
                    if item.get_type() == ebooklib.ITEM_DOCUMENT:
                        soup = BeautifulSoup(item.get_content(), 'html.parser')
                        texts.append(soup.get_text())
                return "\n".join(texts)
            elif ext in ['.docx', '.doc']:
                import docx
                doc = docx.Document(path)
                return "\n".join(para.text for para in doc.paragraphs)
            else:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
        except ImportError as ie:
            Logger.error(f"Instale dependência: {ie.name}")
            return ""
        except Exception as e:
            Logger.error(f"Erro ao ler arquivo: {e}")
            return ""

# =============================================================================
# INTERFACE
# =============================================================================

class Logger:
    @staticmethod
    def info(msg: str): print(f"{Fore.BLUE}ℹ️  {msg}{Style.RESET_ALL}")
    @staticmethod
    def success(msg: str): print(f"{Fore.GREEN}✅ {msg}{Style.RESET_ALL}")
    @staticmethod
    def error(msg: str): print(f"{Fore.RED}❌ {msg}{Style.RESET_ALL}")

class TerminalUI:
    def clear(self): os.system('clear' if os.name == 'posix' else 'cls')
    
    def header(self, title: str):
        self.clear()
        print(f"{Fore.MAGENTA}{Style.BRIGHT}{'='*60}")
        print(f" 🛠️  STUDIO AI - SLOW MOTION v5.0 | {title}")
        print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}\n")

    def file_browser(self) -> Optional[str]:
        path = Path("/sdcard/Download" if os.path.exists("/sdcard/Download") else Path.home())
        while True:
            self.header(f"📂 {path}")
            try:
                items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            except PermissionError:
                path = path.parent
                continue
            dirs = [x for x in items if x.is_dir() and not x.name.startswith('.')]
            files = [x for x in items if x.is_file() and x.suffix.lower() in ('.txt', '.pdf', '.epub', '.docx')]
            choices = {'0': ('dir', path.parent)}
            print(f"{Fore.YELLOW}[0] 🔙 Voltar{Style.RESET_ALL}")
            idx = 1
            print(f"\n{Fore.CYAN}--- PASTAS ---{Style.RESET_ALL}")
            for d in dirs[:15]:
                print(f"[{idx}] 📁 {d.name}")
                choices[str(idx)] = ('dir', d)
                idx += 1
            print(f"\n{Fore.CYAN}--- ARQUIVOS ---{Style.RESET_ALL}")
            for f in files[:20]:
                print(f"[{idx}] 📄 {f.name}")
                choices[str(idx)] = ('file', f)
                idx += 1
            print(f"\n{Fore.CYAN}[X] Sair{Style.RESET_ALL}")
            opt = input("\n👉 Escolha: ").strip().lower()
            if opt == 'x': return None
            if opt in choices:
                tipo, alvo = choices[opt]
                if tipo == 'dir': path = alvo
                else: return str(alvo)

# =============================================================================
# MAIN
# =============================================================================

def main():
    ui = TerminalUI()
    scripter = AudioScripter()
    while True:
        ui.header("MENU DE ROTEIRIZAÇÃO")
        print("Gera roteiros LENTOS (Slow Motion) para Edge TTS.\n")
        print("1. 📂 Selecionar Arquivo")
        print("0. 🚪 Sair")
        opt = input("\n👉 Opção: ").strip()
        if opt == '0': break
        if opt == '1':
            fpath = ui.file_browser()
            if not fpath: continue
            file_path = Path(fpath)
            raw_text = FileHandler.read_file(str(file_path))
            if not raw_text:
                time.sleep(2)
                continue
            optimized_text = scripter.process(raw_text)
            new_name = f"{file_path.stem}_AUDIO_SCRIPT.txt"
            out_path = file_path.parent / new_name
            try:
                with open(out_path, 'w', encoding='utf-8') as f:
                    f.write(optimized_text)
                Logger.success(f"Roteiro Slow Motion criado: {new_name}")
                print(f"\n{Fore.CYAN}--- PREVIEW (Note o isolamento de frases) ---{Style.RESET_ALL}")
                print(textwrap.shorten(optimized_text, width=350))
                print("-" * 50)
            except Exception as e:
                Logger.error(f"Erro ao salvar: {e}")
            input("\nPressione Enter para continuar...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSaindo...")
