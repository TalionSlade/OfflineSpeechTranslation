# NoAI Translation Service

Offline-first service that exposes a REST API for speech-to-text transcription using Vosk and text-to-speech synthesis using Piper.

## Features
- Accepts audio uploads via FastAPI endpoint and validates payload size.
- Transcribes speech locally with a configurable Vosk model.
- Optionally translates the transcript offline (Argos Translate) into a requested target language.
- Persists transcription artifacts under `data/transcriptions` and caches generated speech in `data/tts`.
- Synthesizes the transcript with Piper TTS and streams the resulting WAV audio back to the caller.

## Prerequisites
- Python 3.11+
- Download a Vosk model (for example, `vosk-model-small-en-us-0.15`) and extract it locally.
- Download one or more [Piper voice models](https://github.com/rhasspy/piper/releases) for English and/or Spanish. Place the `.onnx` model and accompanying `.json` metadata files under `models/piper/<language>/` or in the project-level `onnx/` directory (for example, `onnx/en_US-norman-medium.onnx`).

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
  piper/
    en/
      en_US-amy-medium.onnx
      en_US-amy-medium.onnx.json
    es/
      es_ES-dione-medium.onnx
      es_ES-dione-medium.onnx.json
onnx/
  en_US-norman-medium.onnx
  en_US-norman-medium.onnx.json
```
If you place the model elsewhere, set the `VOSK_MODEL_PATH` environment variable.

## Running the API
```bash
uvicorn app.main:app --reload
```
The service exposes:
- `GET /health` – basic liveness probe.
- `GET /v1/languages` – reports which TTS languages and translation pairs are available.
- `POST /v1/process` – accepts `multipart/form-data` with an `audio` file (16-bit PCM WAV recommended).

### Sample request
```bash
curl -X POST http://localhost:8000/v1/process \
  -F "file=@sample.wav" \
  -F "source_language=auto" \
  -F "target_language=es" \
  --output output.wav
```
The response streams the synthesized speech as a WAV file; the generated transcription data is persisted under `data/transcriptions`.

The original uploaded/recorded audio is also persisted under `data/transcriptions` and can be fetched via:
- `GET /v1/transcriptions/{id}/source`

## Configuration
Environment variables:
- `VOSK_MODEL_PATH` – absolute or relative path to the Vosk model directory.
- `TRANSCRIPTION_DIR` – path for persisted transcription outputs (default: `data/transcriptions`).
- `TTS_OUTPUT_DIR` – path for synthesized audio cache (default: `data/tts`).
- `PIPER_MODEL_DIR` – primary directory that contains Piper voice models (default: `models/piper`).
- `PIPER_MODEL_DIRS` – optional path list (separated by your OS path separator) to search for Piper voices. Defaults to `models/piper` and `onnx` beneath the project root.
- `DEFAULT_TTS_LANGUAGE` – fallback ISO language code for speech synthesis when detection is inconclusive (default: `en`).
- `DEFAULT_SOURCE_LANGUAGE` – fallback language code used when `source_language=auto` is sent (default: `en`).
- `PIPER_<LANG>_MODEL` – optional absolute path to a Piper `.onnx` file for the given language code (for example, `PIPER_ES_MODEL`).
- `PIPER_<LANG>_CONFIG` – optional absolute path to the Piper voice metadata file matching the configured model (for example, `PIPER_ES_CONFIG`).
- `ARGOS_MODEL_DIRS` – optional path list (separated by your OS path separator) containing `.argosmodel` translation packages. Defaults to `models/argos` under the project root.
- `TARGET_SAMPLE_RATE` – sample rate for recognition (default: `16000`).
- `MAX_AUDIO_UPLOAD_BYTES` – upload size guardrail (default: 20 MiB).

## Notes
- Only 16-bit PCM WAV files are fully supported without extra tooling. Non-mono channels are downmixed to mono; other sample rates are resampled linearly to 16 kHz.
- Browser microphone recording often produces WebM/OGG containers; to transcribe those (and other formats like MP3/M4A/FLAC), install `ffmpeg` and ensure it's on PATH so the service can convert audio to PCM WAV automatically.
- Piper runs entirely offline; synthesis executes within a guarded section to avoid overlapping CLI invocations. Acquire additional voices by downloading the desired `.onnx` model files and placing them under `models/piper` or by pointing the `PIPER_<LANG>_MODEL` environment variables to their locations.

### Offline translation models (Argos)
Argos Translate uses downloadable language packages (`*.argosmodel`). You have two common offline-friendly options:

1) Download packages from the official package index
- Browse: https://www.argosopentech.com/argospm/index/
- Find your desired `From` → `To` pair and use the `get` link to download the `.argosmodel` file.
- Place the downloaded files into `models/argos/` (default) or set `ARGOS_MODEL_DIRS` to point to your package folder.

2) Install packages via Argos tooling (online once, then cached/offline)
- The Argos docs show both Python and CLI approaches:
  - Python example: https://github.com/argosopentech/argos-translate#download-and-install-argos-translate-package
  - CLI example (argospm): https://github.com/argosopentech/argos-translate#command-line-interface


curl --location 'http://localhost:8000/v1/process' \
--header 'Accept: application/json' \
--form 'file=@"/C:/Users/Arpan/Documents/Innovations/NoAI Translation/archive/50_speakers_audio_data/Speaker_0000/Speaker_0000_00000.wav"'