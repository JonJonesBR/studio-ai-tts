"""
Studio AI TTS - Interface de Usuário
"""

import os
import subprocess
import time
from pathlib import Path
from typing import List, Optional

from colorama import Fore, Style

from .config import CONFIG, UserSettings, config_mgr
from .logger import Logger, TimeEstimator
from .voices import VoiceCatalog
from .cache import HistoryManager


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
        print("2. 📚  Modo Lote (Múltiplos Arquivos)")
        print("3. 📜  Histórico")
        print("4. 🔑  Gerenciar Chaves API")
        print("5. ⚙️   Preferências")
        print("6. 🧹  Limpar Cache")
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
    
    def menu_historico(self, history_mgr: HistoryManager):
        """Menu de histórico de conversões."""
        while True:
            self.header("📜 HISTÓRICO DE CONVERSÕES")
            
            entries = history_mgr.get_recent(10)
            if not entries:
                print(f"{Fore.YELLOW}Nenhuma conversão no histórico.{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}{len(entries)} conversão(ões) recente(s):{Style.RESET_ALL}\n")
                for i, entry in enumerate(entries, 1):
                    duration_str = TimeEstimator.format_time(entry.get('duration', 0))
                    engine = entry.get('engine', '?').upper()
                    date = entry.get('date', '?')
                    source = Path(entry.get('source', '?')).name
                    print(f"  {i}. [{date}] {source}")
                    print(f"     {Fore.CYAN}→ {engine} | {duration_str}{Style.RESET_ALL}")
            
            print(f"\n{Fore.CYAN}[A] Abrir Pasta | [L] Limpar Histórico | [V] Voltar{Style.RESET_ALL}")
            opt = input("\n👉 Opção: ").strip().lower()
            
            if opt == 'v':
                break
            elif opt == 'l':
                if input("Confirma limpar histórico? (s/n): ").lower() == 's':
                    history_mgr.clear()
                    Logger.success("Histórico limpo!")
                    time.sleep(1)
            elif opt == 'a' and entries:
                try:
                    idx = int(input("Número para abrir pasta: ")) - 1
                    if 0 <= idx < len(entries):
                        output = entries[idx].get('output', '')
                        if output and Path(output).exists():
                            folder = str(Path(output).parent)
                            import platform
                            system = platform.system().lower()
                            if system == 'windows':
                                os.startfile(folder)
                            elif system == 'darwin':
                                subprocess.run(['open', folder])
                            else:
                                subprocess.run(['xdg-open', folder])
                except (ValueError, Exception):
                    pass
    
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
            files = [x for x in items if x.is_file() and x.suffix.lower() in ('.txt', '.md', '.pdf', '.epub', '.docx')]
            
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
    
    def file_browser_multi(self) -> List[str]:
        """Navegador para selecionar múltiplos arquivos."""
        selected = []
        while True:
            self.header(f"📚 MODO LOTE - {len(selected)} arquivo(s) selecionado(s)")
            if selected:
                print(f"{Fore.GREEN}Arquivos selecionados:{Style.RESET_ALL}")
                for i, f in enumerate(selected, 1):
                    print(f"  {i}. {Path(f).name}")
                print()
            
            arquivo = self.file_browser()
            if arquivo:
                if arquivo not in selected:
                    selected.append(arquivo)
                    Logger.success(f"Adicionado: {Path(arquivo).name}")
                else:
                    Logger.warning("Arquivo já selecionado")
                
                if input(f"\n✅ {len(selected)} selecionado(s). Adicionar mais? (s/n): ").lower() != 's':
                    break
            else:
                if selected:
                    break
                return []
        return selected
