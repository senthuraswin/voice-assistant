# Voice Assistant using Pipecat

A simple voice chatbot built with Pipecat that responds to voice input:
- Say "hello" → Bot says "Hello!"
- Say anything else → Bot says "Not understand."

## Features

- 🎤 **Speech-to-Text**: Deepgram
- 🧠 **Logic**: Custom Python processor (no LLM needed)
- 🔊 **Text-to-Speech**: Cartesia
- 🌐 **WebRTC**: Real-time voice communication in browser

## Prerequisites

- **Windows with WSL2** (Ubuntu 22.04)
- **Python 3.11+**
- **uv** package manager
- API Keys:
  - [Deepgram](https://deepgram.com/) (Speech-to-Text)
  - [Cartesia](https://cartesia.ai/) (Text-to-Speech)

## Installation

### 1. Install WSL and Ubuntu

```powershell
wsl --install -d Ubuntu-22.04
```

### 2. Install uv in WSL

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env
```

### 3. Navigate to Project

```bash
cd /mnt/e/voiceassistent/pipecat-quickstart
```

### 4. Configure Environment

Create `.env` file in `pipecat-quickstart/`:

```bash
cd pipecat-quickstart
cp .env.example .env
```

Edit `.env` and add your API keys:

```
DEEPGRAM_API_KEY=your_deepgram_key_here
CARTESIA_API_KEY=your_cartesia_key_here
```

### 5. Install Dependencies

```bash
uv sync
```

## Usage

### Run the Bot

From the `pipecat-quickstart` directory in WSL:

```bash
uv run hello_bot.py
```

Wait for:
```
🚀 Bot ready!
   → Open http://localhost:7860/client in your browser
```

### Connect

1. Open http://localhost:7860/client in your browser
2. Click **"Connect"**
3. Allow microphone access
4. Say "hello" and listen for the response!

## How It Works

```
Your Voice → Deepgram STT → HelloProcessor → Cartesia TTS → Speaker
              (Speech to Text)   (Logic)      (Text to Speech)
```

**HelloProcessor Logic:**
```python
if "hello" in user_input or "hi" in user_input:
    response = "Hello!"
else:
    response = "Not understand."
```

## Project Structure

```
voiceassistent/
├── pipecat-quickstart/
│   ├── hello_bot.py         # Simple hello bot (our custom bot)
│   ├── bot.py               # Full Pipecat bot (with OpenAI)
│   ├── .env                 # API keys (create from .env.example)
│   ├── .env.example         # Environment template
│   └── pyproject.toml       # Dependencies
├── simple_chatbot.py        # Old console version
├── requirements.txt         # Old requirements
└── README.md                # This file
```

## Key Files

- **`pipecat-quickstart/hello_bot.py`**: Simple voice bot (hello/not understand logic)
- **`pipecat-quickstart/bot.py`**: Full conversational bot using OpenAI LLM
- **`pipecat-quickstart/.env`**: Your API keys (not in git)
- **`pipecat-quickstart/pyproject.toml`**: Python dependencies

## Troubleshooting

### Port Already in Use
```bash
fuser -k 7860/tcp
```

### Python Version Error
Make sure Python 3.11+ is installed in WSL:
```bash
python3.11 --version
```

### No Audio Output
1. Check browser volume
2. Check speaker settings
3. Look for "Bot started speaking" in terminal logs

## API Keys

Get your free API keys:
- **Deepgram**: https://console.deepgram.com/signup
- **Cartesia**: https://play.cartesia.ai/

## Technologies

- [Pipecat](https://github.com/pipecat-ai/pipecat) - Voice AI framework
- [Deepgram](https://deepgram.com/) - Speech-to-Text
- [Cartesia](https://cartesia.ai/) - Text-to-Speech
- [WebRTC](https://webrtc.org/) - Real-time communication

## License

MIT

---

**Note**: This project requires Linux/WSL because the `daily-python` package (used by Pipecat) only supports Linux/macOS.

MIT
