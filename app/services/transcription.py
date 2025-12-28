"""Audio transcription helpers backed by Vosk."""
from __future__ import annotations

import contextlib
import json
import threading
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
from vosk import KaldiRecognizer, Model

from ..config import TARGET_SAMPLE_RATE, VOSK_MODEL_PATH

_MODEL: Model | None = None
_MODEL_LOCK = threading.Lock()


def _load_model() -> Model:
    """Lazily load and cache the Vosk model instance."""

    global _MODEL
    with _MODEL_LOCK:
        if _MODEL is None:
            if not VOSK_MODEL_PATH.exists():
                raise FileNotFoundError(
                    "Vosk model not found. Update VOSK_MODEL_PATH to point to a downloaded model."
                )
            _MODEL = Model(str(VOSK_MODEL_PATH))
    return _MODEL


def _convert_to_mono(raw: np.ndarray, channels: int) -> np.ndarray:
    """Collapse multi-channel audio to mono by averaging channels."""

    if channels == 1:
        return raw
    reshaped = raw.reshape((-1, channels))
    mono = reshaped.mean(axis=1)
    return mono.astype(raw.dtype)


def _resample(audio: np.ndarray, original_rate: int, target_rate: int) -> np.ndarray:
    """Resample audio using a simple linear interpolation."""

    if original_rate == target_rate:
        return audio

    duration = audio.shape[0] / original_rate
    target_length = int(duration * target_rate)
    if target_length == 0:
        return np.zeros((0,), dtype=audio.dtype)

    x_original = np.linspace(0, audio.shape[0], num=audio.shape[0], endpoint=False)
    x_target = np.linspace(0, audio.shape[0], num=target_length, endpoint=False)
    resampled = np.interp(x_target, x_original, audio).astype(np.int16)
    return resampled


def _read_wav_pcm(path: Path) -> Tuple[int, bytes]:
    """Load a WAV file and return PCM data suitable for Vosk."""

    with contextlib.closing(wave.open(str(path), "rb")) as waveform:  # type: ignore[name-defined]
        sample_width = waveform.getsampwidth()
        channels = waveform.getnchannels()
        sample_rate = waveform.getframerate()
        frames = waveform.getnframes()
        if sample_width != 2:
            raise ValueError("Only 16-bit PCM WAV files are supported.")
        pcm_bytes = waveform.readframes(frames)

    audio = np.frombuffer(pcm_bytes, dtype=np.int16)
    audio = _convert_to_mono(audio, channels)
    audio = _resample(audio, sample_rate, TARGET_SAMPLE_RATE)

    return TARGET_SAMPLE_RATE, audio.tobytes()


# Lazy import to avoid circular dependency in type checking
import wave  # noqa: E402  # isort:skip


def transcribe_audio(audio_path: Path) -> Tuple[str, Dict[str, str]]:
    """Transcribe the provided WAV audio file and return the text and raw recognizer payload."""

    sample_rate, pcm_data = _read_wav_pcm(audio_path)
    model = _load_model()
    recognizer = KaldiRecognizer(model, sample_rate)
    recognizer.SetWords(True)

    buffer_size = 4000
    for idx in range(0, len(pcm_data), buffer_size):
        chunk = pcm_data[idx : idx + buffer_size]
        recognizer.AcceptWaveform(chunk)

    result = json.loads(recognizer.FinalResult())
    text = result.get("text", "").strip()

    return text, result
