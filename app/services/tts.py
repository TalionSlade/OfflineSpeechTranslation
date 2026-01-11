"""Text-to-speech helpers backed by Piper TTS."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import uuid
from pathlib import Path

from ..config import DEFAULT_TTS_LANGUAGE, PIPER_MODEL_DIRS, TTS_OUTPUT_DIR

_SPANISH_MARKERS = set("áéíóúñü¿¡")
_SPANISH_KEYWORDS = {
    "gracias",
    "hola",
    "adiós",
    "por",
    "favor",
    "mañana",
    "ayer",
    "somos",
    "usted",
    "estoy",
}

_LANGUAGE_ALIASES = {
    "en": "en",
    "eng": "en",
    "en-us": "en",
    "en_us": "en",
    "english": "en",
    "es": "es",
    "spa": "es",
    "es-es": "es",
    "es_es": "es",
    "spanish": "es",
    "espanol": "es",
}

_PIPER_BASE = [shutil.which("piper")] if shutil.which("piper") else [sys.executable, "-m", "piper"]
_ENGINE_LOCK = threading.Lock()

_CONFIG_LOCK = threading.Lock()


def _canonical_language(label: str | None) -> str:
    if not label:
        return DEFAULT_TTS_LANGUAGE
    normalized = label.strip().lower()
    if not normalized:
        return DEFAULT_TTS_LANGUAGE
    normalized = normalized.replace("#", "").replace(" ", "")
    if normalized in _LANGUAGE_ALIASES:
        return _LANGUAGE_ALIASES[normalized]
    root = normalized.split("-")[0].split("_")[0]
    return _LANGUAGE_ALIASES.get(root, root or DEFAULT_TTS_LANGUAGE)


def _infer_language_from_text(text: str) -> str:
    lowered = text.lower()
    if any(marker in lowered for marker in _SPANISH_MARKERS):
        return "es"

    tokens = {token.strip(".,!?;:") for token in lowered.split()}
    if tokens & _SPANISH_KEYWORDS:
        return "es"

    return DEFAULT_TTS_LANGUAGE


def _guess_config_path(model_path: Path, explicit: str | None) -> Path | None:
    if explicit:
        candidate = Path(explicit)
        if candidate.exists():
            return candidate
        raise FileNotFoundError(f"Configured Piper voice metadata not found: {candidate}")

    preferred = model_path.with_suffix(".onnx.json")
    if preferred.exists():
        return preferred

    fallback = model_path.with_suffix(".json")
    if fallback.exists():
        return fallback

    generic = model_path.parent / f"{model_path.stem}.json"
    if generic.exists():
        return generic

    return None


def _sanitize_piper_config_in_place(config_path: Path) -> None:
    """Sanitize Piper config JSON **in place** (creates a .bak backup once).

    The installed `piper` CLI currently ignores `--config` and always loads
    `<model>.onnx.json` (see `piper.__main__`). Therefore, if a voice package ships
    with legacy values like `"phoneme_type": "PhonemeType.ESPEAK"`, we must fix
    the file itself.
    """

    resolved = config_path.resolve()

    with _CONFIG_LOCK:
        try:
            raw = resolved.read_text(encoding="utf-8")
            payload = json.loads(raw)
        except Exception:
            return

        if not isinstance(payload, dict):
            return

        phoneme_type = payload.get("phoneme_type")
        if not isinstance(phoneme_type, str):
            return

        normalized = phoneme_type.strip()
        lowered = normalized.lower()
        if not lowered.startswith("phonemetype."):
            return

        tail = normalized.split(".", 1)[1].strip().lower()
        if tail.startswith("espeak"):
            rewritten = "espeak"
        elif tail.startswith("text"):
            rewritten = "text"
        else:
            # Unknown legacy value; leave as-is.
            return

        if rewritten == phoneme_type:
            return

        payload["phoneme_type"] = rewritten

        backup_path = resolved.with_suffix(resolved.suffix + ".bak")
        try:
            if not backup_path.exists():
                backup_path.write_text(raw, encoding="utf-8")
            resolved.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            raise ValueError(
                f"Piper voice config needs a one-time fix but could not be updated: {resolved}. "
                f"Please edit phoneme_type to '{rewritten}' (or make the file writable)."
            ) from exc


def _search_directory(base_dir: Path, language: str, config_override: str | None) -> tuple[Path, Path | None] | None:
    if not base_dir.exists():
        return None

    lang_dir = base_dir / language
    if lang_dir.is_dir():
        models = sorted(lang_dir.glob("*.onnx"))
        if models:
            model_path = models[0]
            return model_path, _guess_config_path(model_path, config_override)

    alt_dir = base_dir / language.replace("-", "_")
    if alt_dir.is_dir():
        models = sorted(alt_dir.glob("*.onnx"))
        if models:
            model_path = models[0]
            return model_path, _guess_config_path(model_path, config_override)

    candidates = sorted(base_dir.glob(f"*{language}*.onnx"))
    if candidates:
        model_path = candidates[0]
        return model_path, _guess_config_path(model_path, config_override)

    generic_candidates = sorted(base_dir.glob("*.onnx"))
    if generic_candidates:
        model_path = generic_candidates[0]
        return model_path, _guess_config_path(model_path, config_override)

    return None


def _resolve_voice_paths(language: str) -> tuple[Path, Path | None]:
    env_prefix = language.replace("-", "_").upper()
    model_override = os.getenv(f"PIPER_{env_prefix}_MODEL")
    config_override = os.getenv(f"PIPER_{env_prefix}_CONFIG")

    if model_override:
        model_path = Path(model_override)
        if not model_path.exists():
            raise FileNotFoundError(f"Configured Piper voice model not found: {model_path}")
        return model_path, _guess_config_path(model_path, config_override)

    visited: set[Path] = set()
    for base in PIPER_MODEL_DIRS:
        base_dir = Path(base)
        resolved = base_dir.resolve()
        if resolved in visited:
            continue
        visited.add(resolved)
        result = _search_directory(base_dir, language, config_override)
        if result:
            return result

    raise FileNotFoundError(
        f"Could not locate a Piper model for language '{language}'. Set PIPER_{env_prefix}_MODEL to the model path."
    )


def _build_command(model_path: Path, config_path: Path | None, output_path: Path, speaker: str | int | None) -> list[str]:
    if not _PIPER_BASE or not _PIPER_BASE[0]:
        raise FileNotFoundError("Piper CLI is not available. Install piper-tts to provide the 'piper' command.")

    command = list(_PIPER_BASE)
    command.extend(["--model", str(model_path), "--output_file", str(output_path)])
    if config_path:
        # Note: current Piper CLI ignores --config, but we keep it for forward compatibility
        # and still sanitize the default config file in-place.
        _sanitize_piper_config_in_place(config_path)
        command.extend(["--config", str(config_path)])
    if speaker is not None:
        command.extend(["--speaker", str(speaker)])
    return command


def synthesize_speech(
    text: str,
    *,
    language: str | None = None,
    speaker: str | int | None = None,
) -> Path:
    """Generate speech audio for the supplied text and return the output path."""

    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Cannot synthesize empty text.")

    target_language = _canonical_language(language) if language else _infer_language_from_text(cleaned)
    model_path, config_path = _resolve_voice_paths(target_language)

    output_path = TTS_OUTPUT_DIR / f"{uuid.uuid4().hex}.wav"

    command = _build_command(model_path, config_path, output_path, speaker)

    with _ENGINE_LOCK:
        try:
            result = subprocess.run(
                command,
                input=cleaned.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        except FileNotFoundError as exc:  # raised if python executable missing
            raise FileNotFoundError(
                "Piper CLI not found. Install piper-tts and ensure it is accessible on PATH."
            ) from exc

    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="ignore")
        message = stderr.strip() or f"Exit code {result.returncode}"
        hint = ""
        lowered = message.lower()
        if "onnxruntime" in lowered and ("dll load failed" in lowered or "pybind" in lowered):
            hint = (
                "\n\nHint: This looks like an ONNX Runtime DLL/provider issue on Windows. "
                "Use `onnxruntime-directml` (already in requirements) and reinstall your deps in the same venv."
            )
        raise RuntimeError(f"Piper synthesis failed: {message}{hint}")

    if not output_path.exists():
        raise RuntimeError("Piper synthesis completed without creating an output file.")

    return output_path


def list_supported_tts_languages(candidates: list[str] | None = None) -> list[str]:
    """Return language codes that can be synthesized with the current Piper setup.

    This is a best-effort probe intended for UI configuration.
    """

    probe = candidates or [
        "en",
        "es",
        "fr",
        "de",
        "it",
        "pt",
        "ru",
        "zh",
        "ja",
        "ko",
        "ar",
        "hi",
        "nl",
        "pl",
        "tr",
    ]

    supported: list[str] = []
    for code in probe:
        try:
            _resolve_voice_paths(_canonical_language(code))
        except FileNotFoundError:
            continue
        supported.append(code)
    return supported
