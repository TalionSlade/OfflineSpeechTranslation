"""Text-to-speech helpers powered by pyttsx3."""
from __future__ import annotations

import threading
import uuid
from pathlib import Path

import pyttsx3

from ..config import TTS_OUTPUT_DIR

_ENGINE_LOCK = threading.Lock()


def synthesize_speech(text: str, *, voice: str | None = None, rate: int | None = None) -> Path:
    """Generate speech audio for the supplied text and return the output path."""

    if not text.strip():
        raise ValueError("Cannot synthesize empty text.")

    output_path = TTS_OUTPUT_DIR / f"{uuid.uuid4().hex}.wav"

    with _ENGINE_LOCK:
        engine = pyttsx3.init()
        if voice:
            engine.setProperty("voice", voice)
        if rate:
            engine.setProperty("rate", rate)
        engine.save_to_file(text, str(output_path))
        engine.runAndWait()
        engine.stop()

    return output_path
