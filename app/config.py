"""Application-wide configuration helpers."""
from __future__ import annotations

import os
from pathlib import Path

# Resolve project root (directory that contains the app package)
ROOT_DIR = Path(__file__).resolve().parent.parent

# Directory for storing persisted transcription payloads
TRANSCRIPTION_DIR = Path(os.getenv("TRANSCRIPTION_DIR", ROOT_DIR / "data" / "transcriptions"))
TRANSCRIPTION_DIR.mkdir(parents=True, exist_ok=True)

# Directory for storing persisted translation outputs (validation/auditing)
TRANSLATION_DIR = Path(os.getenv("TRANSLATION_DIR", ROOT_DIR / "data" / "translations"))
TRANSLATION_DIR.mkdir(parents=True, exist_ok=True)

# Directory for caching synthesized audio files
TTS_OUTPUT_DIR = Path(os.getenv("TTS_OUTPUT_DIR", ROOT_DIR / "data" / "tts"))
TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _parse_path_list(raw: str | None) -> list[Path]:
    if not raw:
        return []
    paths: list[Path] = []
    for entry in raw.split(os.pathsep):
        trimmed = entry.strip()
        if not trimmed:
            continue
        path = Path(trimmed).expanduser()
        if not path.is_absolute():
            path = ROOT_DIR / path
        paths.append(path)
    return paths


_configured_piper_dirs = _parse_path_list(os.getenv("PIPER_MODEL_DIRS"))

if _configured_piper_dirs:
    PIPER_MODEL_DIRS = _configured_piper_dirs
else:
    default_primary = ROOT_DIR / "models" / "piper"
    default_primary.mkdir(parents=True, exist_ok=True)
    default_secondary = ROOT_DIR / "onnx"
    default_secondary.mkdir(parents=True, exist_ok=True)
    PIPER_MODEL_DIRS = [default_primary, default_secondary]

PIPER_MODEL_DIR = PIPER_MODEL_DIRS[0]

# Default language used for TTS when detection cannot decide
DEFAULT_TTS_LANGUAGE = os.getenv("DEFAULT_TTS_LANGUAGE", "en").strip().lower() or "en"

# Default source language when STT language is unknown/auto.
# Note: current Vosk setup is usually a single-language model, so this is a pragmatic default.
DEFAULT_SOURCE_LANGUAGE = os.getenv("DEFAULT_SOURCE_LANGUAGE", "en").strip().lower() or "en"

# Location of the Vosk model on disk. The default points to a sibling models folder.
VOSK_MODEL_PATH = Path(
    os.getenv("VOSK_MODEL_PATH", ROOT_DIR / "models" / "vosk-model-small-en-us-0.15")
)

# Default sample rate expected by the recognizer.
TARGET_SAMPLE_RATE = int(os.getenv("TARGET_SAMPLE_RATE", "16000"))

# Maximum size (in bytes) for uploaded recordings to prevent exhaustion.
MAX_AUDIO_UPLOAD_BYTES = int(os.getenv("MAX_AUDIO_UPLOAD_BYTES", str(20 * 1024 * 1024)))


# Optional local directory list for Argos Translate packages (.argosmodel).
# This enables an offline-first translation setup: drop model packages here and the service
# will install them on demand.
_configured_argos_dirs = _parse_path_list(os.getenv("ARGOS_MODEL_DIRS"))
if _configured_argos_dirs:
    ARGOS_MODEL_DIRS = _configured_argos_dirs
else:
    default_argos = ROOT_DIR / "models" / "argos"
    default_argos.mkdir(parents=True, exist_ok=True)
    ARGOS_MODEL_DIRS = [default_argos]
