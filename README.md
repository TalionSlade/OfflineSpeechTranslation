# NoAI Translation Service

Offline-first service that exposes a REST API for speech-to-text transcription using Vosk and text-to-speech synthesis using pyttsx3.

## Features
- Accepts audio uploads via FastAPI endpoint and validates payload size.
- Transcribes speech locally with a configurable Vosk model.
- Persists transcription artifacts under `data/transcriptions` and caches generated speech in `data/tts`.
- Synthesizes the transcript with pyttsx3 and returns the resulting audio (base64 encoded) in the response.

## Prerequisites
- Python 3.11+
- Download a Vosk model (for example, `vosk-model-small-en-us-0.15`) and extract it locally.
- Ensure the host can play audio through `pyttsx3` (Windows SAPI is used by default).

## Setup
```bash
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

Create a `models` directory beside the `app` package and unpack the Vosk model inside it so the folder structure looks like:
```
models/
  vosk-model-small-en-us-0.15/
```
If you place the model elsewhere, set the `VOSK_MODEL_PATH` environment variable.

## Running the API
```bash
uvicorn app.main:app --reload
```
The service exposes:
- `GET /health` – basic liveness probe.
- `POST /v1/process` – accepts `multipart/form-data` with an `audio` file (16-bit PCM WAV recommended).

### Sample request
```bash
curl -X POST http://localhost:8000/v1/process \
  -F "file=@sample.wav" \
  --output output.wav
```
The response streams the synthesized speech as a WAV file; the generated transcription data is persisted under `data/transcriptions`.

## Configuration
Environment variables:
- `VOSK_MODEL_PATH` – absolute or relative path to the Vosk model directory.
- `TRANSCRIPTION_DIR` – path for persisted transcription outputs (default: `data/transcriptions`).
- `TTS_OUTPUT_DIR` – path for synthesized audio cache (default: `data/tts`).
- `TARGET_SAMPLE_RATE` – sample rate for recognition (default: `16000`).
- `MAX_AUDIO_UPLOAD_BYTES` – upload size guardrail (default: 20 MiB).

## Notes
- Only 16-bit PCM WAV files are fully supported. Non-mono channels are downmixed to mono; other sample rates are resampled linearly to 16 kHz.
- Large uploads or long-form synthesis run sequentially to preserve `pyttsx3` stability. Consider queueing or worker processes for production workloads.


curl --location 'http://localhost:8000/v1/process' \
--header 'Accept: application/json' \
--form 'file=@"/C:/Users/Arpan/Documents/Innovations/NoAI Translation/archive/50_speakers_audio_data/Speaker_0000/Speaker_0000_00000.wav"'