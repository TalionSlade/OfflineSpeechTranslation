from __future__ import annotations

import base64
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from .config import MAX_AUDIO_UPLOAD_BYTES
from .services.transcription import transcribe_audio
from .services.tts import synthesize_speech
from .storage import save_transcription

app = FastAPI(title="NoAI Translation Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/process")
async def process_audio(file: UploadFile = File(...)) -> dict[str, str]:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename.")

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty audio payload.")
    if len(payload) > MAX_AUDIO_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Audio file too large.")

    suffix = Path(file.filename).suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
        temp_audio.write(payload)
        temp_path = Path(temp_audio.name)

    try:
        transcript_text, recognizer_payload = transcribe_audio(temp_path)
        tts_path = synthesize_speech(transcript_text)
        record = save_transcription(
            transcript_text,
            file.filename,
            tts_audio_path=tts_path,
            metadata={"recognizer": recognizer_payload},
        )
        audio_bytes = tts_path.read_bytes()
        audio_base64 = base64.b64encode(audio_bytes).decode("ascii")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    finally:
        temp_path.unlink(missing_ok=True)

    return {
        "transcription_id": record.id,
        "transcript": transcript_text,
        "audio_mime_type": "audio/wav",
        "audio_base64": audio_base64,
    }
