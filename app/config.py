"""Application-wide configuration helpers."""
from __future__ import annotations

import os
from pathlib import Path

# Resolve project root (directory that contains the app package)
ROOT_DIR = Path(__file__).resolve().parent.parent

# Directory for storing persisted transcription payloads
TRANSCRIPTION_DIR = Path(os.getenv("TRANSCRIPTION_DIR", ROOT_DIR / "data" / "transcriptions"))
TRANSCRIPTION_DIR.mkdir(parents=True, exist_ok=True)

# Directory for caching synthesized audio files
TTS_OUTPUT_DIR = Path(os.getenv("TTS_OUTPUT_DIR", ROOT_DIR / "data" / "tts"))
TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Location of the Vosk model on disk. The default points to a sibling models folder.
VOSK_MODEL_PATH = Path(
    os.getenv("VOSK_MODEL_PATH", ROOT_DIR / "models" / "vosk-model-small-en-us-0.15")
)

# Default sample rate expected by the recognizer.
TARGET_SAMPLE_RATE = int(os.getenv("TARGET_SAMPLE_RATE", "16000"))

# Maximum size (in bytes) for uploaded recordings to prevent exhaustion.
MAX_AUDIO_UPLOAD_BYTES = int(os.getenv("MAX_AUDIO_UPLOAD_BYTES", str(20 * 1024 * 1024)))
