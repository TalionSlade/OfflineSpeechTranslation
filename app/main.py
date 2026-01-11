from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .config import DEFAULT_TTS_LANGUAGE
from .config import MAX_AUDIO_UPLOAD_BYTES
from .services.transcription import transcribe_audio
from .services.translation import list_installed_translation_pairs, translate_text
from .services.tts import synthesize_speech
from .services.tts import list_supported_tts_languages
from .storage import load_transcription
from .storage import save_transcription

app = FastAPI(title="NoAI Translation Service", version="0.1.0")

cors_origins_raw = os.getenv("CORS_ALLOW_ORIGINS", "*").strip()
if cors_origins_raw == "*":
    cors_allow_origins = ["*"]
    cors_allow_credentials = False
else:
    cors_allow_origins = [origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()]
    cors_allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allow_origins,
    allow_credentials=cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/languages")
def list_languages() -> dict[str, object]:
    """Report available language capabilities.

    This endpoint is intended for UI configuration (e.g. hide unsupported targets).
    """

    return {
        "tts_languages": list_supported_tts_languages(),
        "translation_pairs": list_installed_translation_pairs(),
    }


@app.get("/v1/transcriptions/{record_id}/source")
def get_source_audio(record_id: str) -> FileResponse:
    record = load_transcription(record_id)
    if not record or not record.source_audio_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source audio not found.")

    source_path = Path(record.source_audio_path)
    if not source_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source audio file is missing.")

    media_type = "audio/wav"
    suffix = source_path.suffix.lower()
    if suffix == ".mp3":
        media_type = "audio/mpeg"
    elif suffix == ".m4a":
        media_type = "audio/mp4"
    elif suffix == ".flac":
        media_type = "audio/flac"

    return FileResponse(path=source_path, media_type=media_type, filename=source_path.name)


@app.post("/v1/process")
async def process_audio(
    file: UploadFile = File(...),
    source_language: str = Form("auto"),
    target_language: str = Form(DEFAULT_TTS_LANGUAGE),
) -> FileResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename.")

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty audio payload.")
    if len(payload) > MAX_AUDIO_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Audio file too large.")

    suffix = Path(file.filename).suffix or ".wav"
    record_id = uuid.uuid4().hex
    source_audio_path = Path("data") / "transcriptions" / f"{record_id}_source{suffix}"
    # Ensure directory exists (config module already creates it, but keep this defensive).
    source_audio_path.parent.mkdir(parents=True, exist_ok=True)
    source_audio_path.write_bytes(payload)

    audio_path = source_audio_path

    try:
        transcript_text, recognizer_payload = transcribe_audio(audio_path)
        translation = translate_text(
            transcript_text,
            source_language=source_language,
            target_language=target_language,
        )
        tts_path = synthesize_speech(translation.translated_text, language=translation.target_language)
        record = save_transcription(
            transcript_text,
            file.filename,
            record_id=record_id,
            translation_text=translation.translated_text,
            source_audio_path=source_audio_path,
            tts_audio_path=tts_path,
            metadata={
                "recognizer": recognizer_payload,
                "source_language": translation.source_language,
                "target_language": translation.target_language,
                "translated_text": translation.translated_text,
            },
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception:
        # If processing failed, remove the persisted source audio to avoid orphaned files.
        source_audio_path.unlink(missing_ok=True)
        raise

    # Expose the synthesized audio file directly so clients avoid manual base64 decoding.
    return FileResponse(
        path=tts_path,
        media_type="audio/wav",
        filename=f"{record.id}.wav",
        headers={"X-Transcription-Id": record.id},
    )
