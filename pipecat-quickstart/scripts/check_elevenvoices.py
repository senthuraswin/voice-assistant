#!/usr/bin/env python3
"""Check available ElevenLabs voices using ELEVENLABS_API_KEY from .env.

Usage: python scripts/check_elevenvoices.py
"""
import os
import sys
import requests
from dotenv import load_dotenv


def main():
    load_dotenv(override=False)
    key = os.getenv("ELEVENLABS_API_KEY")
    if not key:
        print("Missing ELEVENLABS_API_KEY in environment (.env).", file=sys.stderr)
        return 2

    url = "https://api.elevenlabs.io/v1/voices"
    headers = {"xi-api-key": key}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
    except Exception as e:
        print(f"Request failed: {e}", file=sys.stderr)
        return 3

    if resp.status_code == 401:
        print("Invalid ElevenLabs API key (401).", file=sys.stderr)
        return 4

    if not resp.ok:
        print(f"Error from ElevenLabs API: {resp.status_code} {resp.text}", file=sys.stderr)
        return 5

    data = resp.json()
    voices = data.get("voices") or data.get("data") or []
    if not voices:
        print("No voices returned by ElevenLabs API.")
        return 6

    for v in voices:
        vid = v.get("voice_id") or v.get("id") or v.get("voiceId")
        name = v.get("name") or v.get("label") or v.get("title")
        vtype = "custom" if v.get("category") == "custom" or v.get("type") == "custom" else "premade"
        print(f"{vid}\t{name}\t{vtype}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
