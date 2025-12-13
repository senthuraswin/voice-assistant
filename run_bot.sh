#!/usr/bin/env bash
# Helper to run the quickstart bot in a WSL/Linux environment
set -euo pipefail
if [ -f "$HOME/.local/bin/env" ]; then
  # shellcheck source=/dev/null
  source "$HOME/.local/bin/env"
fi
cd "$(dirname "$0")/pipecat-quickstart" || exit 1
uv sync
uv run hello_bot.py
