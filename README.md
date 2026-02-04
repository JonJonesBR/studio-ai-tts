# 🎧 Studio AI TTS

### Conversor de Texto para Audiobook com IA

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS%20%7C%20Android-lightgrey.svg)]()

Transforme qualquer texto, PDF ou EPUB em audiobooks de alta qualidade usando as melhores vozes de IA disponíveis.

**[📖 Guia para Iniciantes](#-guia-para-iniciantes)** • **[🔧 Documentação Técnica](#-documentação-técnica)** • **[❓ FAQ](#-perguntas-frequentes)**

---

## ✨ Recursos

- 🎙️ **Duas engines de TTS:** Google Gemini (qualidade premium) e Microsoft Edge TTS (gratuito e ilimitado)
- 📚 **Suporte a múltiplos formatos:** TXT, MD, PDF e EPUB
- 🌍 **30+ vozes multilíngues:** Português, Inglês, Espanhol, Francês e mais
- 💾 **Sistema de cache inteligente:** Evita reprocessar textos já convertidos
- 🔄 **Rotação automática de API keys:** Maximiza uso das cotas gratuitas
- 📱 **Multiplataforma:** Funciona em Windows, Linux, macOS e Android (Termux)

---

# 📖 GUIA PARA INICIANTES

> **Esta seção é para você que nunca usou Python ou linha de comando antes.**  
> Siga o passo a passo do seu sistema operacional.

---

## 📱 Android (Termux)

### Passo 1: Instalar o Termux

1. Baixe o **Termux** da [F-Droid](https://f-droid.org/packages/com.termux/) (NÃO use a versão da Play Store, está desatualizada)
2. Abra o Termux e aguarde a instalação inicial

### Passo 2: Preparar o ambiente

Cole os comandos abaixo **um de cada vez** e pressione Enter:

```bash
# Atualiza os pacotes
pkg update && pkg upgrade -y

# Instala Python e FFmpeg
pkg install python ffmpeg git -y

# Dá permissão para acessar seus arquivos
termux-setup-storage
```

### Passo 3: Baixar o Studio AI

```bash
# Vai para a pasta de downloads
cd ~/storage/downloads

# Baixa o projeto
git clone https://github.com/JonJonesBR/AUDIOBOOK.PY.git

# Entra na pasta
cd AUDIOBOOK.PY
```

### Passo 4: Instalar dependências

```bash
pip install aiohttp edge-tts colorama pypdf ebooklib beautifulsoup4
```

### Passo 5: Configurar (se quiser usar vozes Gemini)

```bash
# Copia o arquivo de exemplo
cp config.example.json studio_config.json

# Edita com suas chaves (veja seção "Como obter API Key")
nano studio_config.json
```

> 💡 **Dica:** Se não tiver API key, não se preocupe! O Edge TTS funciona sem chave.

### Passo 6: Executar!

```bash
python tts.py
```

---

## 🪟 Windows

### Passo 1: Instalar Python

1. Acesse [python.org/downloads](https://www.python.org/downloads/)
2. Clique em **"Download Python 3.x.x"**
3. **IMPORTANTE:** Na instalação, marque a opção ✅ **"Add Python to PATH"**
4. Clique em "Install Now"

### Passo 2: Instalar FFmpeg

1. Acesse [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/)
2. Baixe **"ffmpeg-release-essentials.zip"**
3. Extraia para `C:\ffmpeg`
4. Adicione ao PATH:
   - Pressione `Win + R`, digite `sysdm.cpl` e pressione Enter
   - Vá em **Avançado** → **Variáveis de Ambiente**
   - Em "Path", clique em **Editar** → **Novo**
   - Adicione: `C:\ffmpeg\bin`
   - Clique OK em tudo

### Passo 3: Baixar o Studio AI

1. Acesse a página do projeto no GitHub
2. Clique no botão verde **"Code"** → **"Download ZIP"**
3. Extraia o ZIP para uma pasta (ex: `C:\StudioAI`)

### Passo 4: Instalar dependências

1. Abra o **Prompt de Comando** (pesquise por "cmd" no menu Iniciar)
2. Navegue até a pasta:

```cmd
cd C:\StudioAI
```

3. Instale as bibliotecas:

```cmd
pip install aiohttp edge-tts colorama pypdf ebooklib beautifulsoup4
```

### Passo 5: Configurar (opcional)

1. Na pasta do projeto, copie `config.example.json` e renomeie para `studio_config.json`
2. Abra com o Bloco de Notas e adicione suas API keys (veja seção abaixo)

### Passo 6: Executar!

```cmd
python tts.py
```

---

## 🐧 Linux (Ubuntu/Debian)

### Instalação rápida

```bash
# Instala dependências do sistema
sudo apt update
sudo apt install python3 python3-pip ffmpeg git -y

# Baixa o projeto
git clone https://github.com/JonJonesBR/AUDIOBOOK.PY.git
cd AUDIOBOOK.PY

# Instala bibliotecas Python
pip3 install aiohttp edge-tts colorama pypdf ebooklib beautifulsoup4

# Configura (opcional)
cp config.example.json studio_config.json
nano studio_config.json

# Executa
python3 tts.py
```

---

## 🍎 macOS

### Instalação rápida

```bash
# Instala Homebrew (se não tiver)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instala Python e FFmpeg
brew install python ffmpeg git

# Baixa o projeto
git clone https://github.com/JonJonesBR/AUDIOBOOK.PY.git
cd AUDIOBOOK.PY

# Instala bibliotecas
pip3 install aiohttp edge-tts colorama pypdf ebooklib beautifulsoup4

# Configura (opcional)
cp config.example.json studio_config.json
nano studio_config.json

# Executa
python3 tts.py
```

---

## 🔑 Como Obter API Key do Google (Gratuita!)

> **Necessário apenas se você quiser usar as vozes premium do Gemini.**  
> O Edge TTS funciona sem nenhuma chave!

1. Acesse [aistudio.google.com](https://aistudio.google.com/)
2. Faça login com sua conta Google
3. Clique em **"Get API Key"** no menu lateral
4. Clique em **"Create API Key"**
5. Copie a chave gerada
6. Cole no arquivo `studio_config.json`:

```json
{
    "google_keys": ["SUA_CHAVE_AQUI"]
}
```

> 💡 **Dica:** Você pode adicionar múltiplas chaves para aumentar sua cota diária!

---

## 🎯 Como Usar o Programa

1. **Execute o programa** (`python tts.py`)
2. **Menu Principal:**
   - `1` - Novo Audiobook: Converte um arquivo
   - `2` - Gerenciar Chaves: Adiciona/remove API keys
   - `3` - Preferências: Muda voz, velocidade, motor
   - `4` - Limpar Cache: Libera espaço
   - `0` - Sair

3. **Navegue até seu arquivo** usando o navegador integrado
4. **Confirme as configurações** e aguarde a conversão
5. **Pronto!** Seu audiobook MP3 estará na mesma pasta do arquivo original

---

# 🔧 DOCUMENTAÇÃO TÉCNICA

> **Esta seção é para desenvolvedores e usuários avançados.**

---

## 📁 Estrutura do Projeto

```
AUDIOBOOK.PY/
├── tts.py                  # Script principal
├── config.example.json     # Template de configuração
├── studio_config.json      # Configurações do usuário (gitignored)
├── .gitignore
├── README.md
└── LICENSE
```

---

## ⚙️ Configuração Avançada

### Arquivo `studio_config.json`

```json
{
    "motor_padrao": "edge",
    "velocidade": "+0%",
    "limite_chunk": 3000,
    "modelo_gemini": "gemini-2.5-flash-preview-tts",
    "google_keys": [
        "KEY_1",
        "KEY_2"
    ],
    "voz_edge": "pt-BR-AntonioNeural",
    "voz_google": "Puck"
}
```

| Campo | Descrição | Valores |
|-------|-----------|---------|
| `motor_padrao` | Engine padrão | `"edge"` ou `"google"` |
| `velocidade` | Velocidade Edge TTS | `-50%` a `+100%` |
| `limite_chunk` | Caracteres por chunk | `100` a `5000` |
| `modelo_gemini` | Modelo Gemini | Ver opções abaixo |
| `google_keys` | Array de API keys | Strings |
| `voz_edge` | Voz padrão Edge | Ver lista abaixo |
| `voz_google` | Voz padrão Gemini | Ver lista abaixo |

---

## 🎤 Vozes Disponíveis

### Vozes Gemini (30 vozes)

**Femininas Conversacionais:**
`Aoede`, `Kore`, `Leda`, `Zephyr`

**Femininas Especializadas:**
`Achird`, `Algenib`, `Callirrhoe`, `Despina`, `Erinome`, `Laomedeia`, `Pulcherrima`, `Sulafat`, `Vindemiatrix`

**Masculinas Principais:**
`Puck`, `Charon`, `Orus`, `Autonoe`, `Iapetus`, `Umbriel`

**Masculinas Especializadas:**
`Achernar`, `Alnilam`, `Enceladus`, `Fenrir`, `Gacrux`, `Rasalgethi`, `Sadachbia`, `Sadaltager`, `Schedar`, `Zubenelgenubi`

### Vozes Edge TTS (Multilingual)

| Voz | Idioma | Gênero |
|-----|--------|--------|
| `pt-BR-ThalitaMultilingualNeural` ⭐ | PT-BR | F |
| `pt-BR-AntonioNeural` | PT-BR | M |
| `en-US-AvaMultilingualNeural` | EN-US | F |
| `en-US-BrianMultilingualNeural` | EN-US | M |
| `en-US-AndrewMultilingualNeural` | EN-US | M |
| `en-US-EmmaMultilingualNeural` | EN-US | F |

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                      StudioAIApp                            │
│  ┌─────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │ TerminalUI  │  │ ConversionEngine│  │  ConfigManager │  │
│  └─────────────┘  └────────┬────────┘  └────────────────┘  │
│                            │                                │
│         ┌──────────────────┼──────────────────┐            │
│         ▼                  ▼                  ▼            │
│  ┌─────────────┐  ┌─────────────────┐  ┌─────────────┐    │
│  │TextProcessor│  │ GeminiTTSClient │  │EdgeTTSClient│    │
│  └─────────────┘  └────────┬────────┘  └─────────────┘    │
│                            │                                │
│         ┌──────────────────┼──────────────────┐            │
│         ▼                  ▼                  ▼            │
│  ┌─────────────┐  ┌─────────────────┐  ┌─────────────┐    │
│  │  AudioCache │  │   KeyManager    │  │AudioProcessor│   │
│  └─────────────┘  └─────────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Reference

### GeminiTTSClient

```python
async with GeminiTTSClient(key_manager, settings) as client:
    success = await client.synthesize(
        text="Seu texto aqui",
        voice="Puck",
        output_path="/path/to/output.wav"
    )
```

### EdgeTTSClient

```python
client = EdgeTTSClient(cache)
success = await client.synthesize(
    text="Seu texto aqui",
    voice="pt-BR-AntonioNeural",
    rate="+10%",
    output_path="/path/to/output.mp3"
)
```

### TextProcessor

```python
# Limpa e normaliza texto
cleaned = TextProcessor.clean(raw_text)

# Divide em chunks inteligentes
chunks = TextProcessor.smart_split(text, limit=3000)
```

### KeyManager

```python
km = KeyManager(["key1", "key2", "key3"])
current_key = await km.get_current()
await km.rotate()  # Muda para próxima chave
```

---

## 🧪 Desenvolvimento

### Ambiente de Desenvolvimento

```bash
# Clone o repositório
git clone https://github.com/JonJonesBR/AUDIOBOOK.PY.git
cd AUDIOBOOK.PY

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Instale dependências
pip install aiohttp edge-tts colorama pypdf ebooklib beautifulsoup4

# Execute em modo debug (descomente Logger.debug no código)
python tts.py
```

### Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

---

## 📊 Rate Limits e Quotas

| Engine | Limite Gratuito | Recomendação |
|--------|-----------------|--------------|
| **Gemini** | ~200 requests/dia/key | Use múltiplas keys |
| **Edge TTS** | Ilimitado | Preferir para textos longos |

---

## 🛡️ Segurança

- ✅ API keys armazenadas localmente (nunca commitadas)
- ✅ Proteção contra injeção de comandos
- ✅ Hashing SHA256 para cache
- ✅ Timeouts configurados para conexões

---

# ❓ Perguntas Frequentes

### O programa trava no meio da conversão

Isso geralmente acontece por rate limiting. O programa automaticamente:
1. Rotaciona entre suas API keys
2. Aguarda 60 segundos se todas as keys estiverem limitadas
3. Retenta o chunk que falhou

**Solução:** Adicione mais API keys ou use Edge TTS para textos longos.

### Erro "FFmpeg não encontrado"

FFmpeg é necessário para unir os chunks de áudio. Instale conforme seu sistema:
- **Windows:** Siga o guia na seção Windows
- **Linux:** `sudo apt install ffmpeg`
- **macOS:** `brew install ffmpeg`
- **Termux:** `pkg install ffmpeg`

### Posso usar comercialmente?

- **Edge TTS:** Verifique os termos de uso da Microsoft
- **Gemini TTS:** Verifique os termos da API do Google

Este software é MIT, mas as vozes têm suas próprias licenças.

### Como converter um livro muito grande?

1. Use Edge TTS (sem limite de requests)
2. Ou adicione múltiplas API keys do Gemini
3. O programa salva progresso no cache, então você pode retomar se parar

---

## 📜 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

---

**Feito com ❤️ para a comunidade de audiobooks**

[⬆ Voltar ao topo](#-studio-ai-tts)
