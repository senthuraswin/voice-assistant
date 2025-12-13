# Run the quickstart bot inside WSL/Ubuntu from Windows PowerShell
wsl -d Ubuntu-22.04 -e bash -c "source ~/.local/bin/env && cd /mnt/e/voice/voice-assistant/pipecat-quickstart && uv sync && uv run hello_bot.py"
