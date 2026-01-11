"""Utilities for persisting and retrieving transcription data."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .config import TRANSCRIPTION_DIR, TRANSLATION_DIR


@dataclass
class TranscriptionRecord:
    """Represents a stored transcription job."""

    id: str
    created_at: str
    original_filename: str
    transcript_text: str
    transcript_path: str
    translated_text: Optional[str] = None
    translation_path: Optional[str] = None
    source_audio_path: Optional[str] = None
    tts_audio_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @property
    def json_path(self) -> Path:
        return TRANSCRIPTION_DIR / f"{self.id}.json"


def save_transcription(
    transcript_text: str,
    original_filename: str,
    *,
    record_id: str | None = None,
    translation_text: Optional[str] = None,
    source_audio_path: Optional[Path] = None,
    tts_audio_path: Optional[Path] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> TranscriptionRecord:
    """Persist a transcription payload to disk as JSON."""

    record_id = record_id or uuid.uuid4().hex
    created_at = datetime.now(timezone.utc).isoformat()
    transcript_path = TRANSCRIPTION_DIR / f"{record_id}.txt"
    transcript_path.write_text(transcript_text, encoding="utf-8")

    translation_path: Optional[Path] = None
    translated_cleaned: Optional[str] = None
    if translation_text is not None:
        translated_cleaned = (translation_text or "").strip()
        translation_path = TRANSLATION_DIR / f"{record_id}.txt"
        translation_path.write_text(translated_cleaned, encoding="utf-8")

    record = TranscriptionRecord(
        id=record_id,
        created_at=created_at,
        original_filename=original_filename,
        transcript_text=transcript_text,
        transcript_path=str(transcript_path.resolve()),
        translated_text=translated_cleaned,
        translation_path=str(translation_path.resolve()) if translation_path else None,
        source_audio_path=str(source_audio_path.resolve()) if source_audio_path else None,
        tts_audio_path=str(tts_audio_path.resolve()) if tts_audio_path else None,
        metadata=metadata or {},
    )

    with record.json_path.open("w", encoding="utf-8") as fh:
        json.dump(asdict(record), fh, indent=2)

    return record


def load_transcription(record_id: str) -> Optional[TranscriptionRecord]:
    """Load a transcription record if it exists."""

    json_path = TRANSCRIPTION_DIR / f"{record_id}.json"
    if not json_path.exists():
        return None

    with json_path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)

    return TranscriptionRecord(**payload)
