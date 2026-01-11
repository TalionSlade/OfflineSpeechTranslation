"""Offline text translation helpers.

This module provides a small abstraction for translating recognized text into
another language before passing it to TTS.

Current implementation uses Argos Translate (OpenNMT-based) when translation is
requested. Models must be installed locally (offline-first).
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path

from ..config import ARGOS_MODEL_DIRS, DEFAULT_SOURCE_LANGUAGE


_LANGUAGE_ALIASES: dict[str, str] = {
    "auto": "auto",
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
    "fr": "fr",
    "fra": "fr",
    "french": "fr",
    "de": "de",
    "deu": "de",
    "german": "de",
    "it": "it",
    "ita": "it",
    "italian": "it",
    "pt": "pt",
    "por": "pt",
    "pt-br": "pt",
    "pt_br": "pt",
    "portuguese": "pt",
    "ru": "ru",
    "rus": "ru",
    "russian": "ru",
    "zh": "zh",
    "zho": "zh",
    "zh-cn": "zh",
    "zh_cn": "zh",
    "chinese": "zh",
    "ja": "ja",
    "jpn": "ja",
    "japanese": "ja",
    "ko": "ko",
    "kor": "ko",
    "korean": "ko",
    "ar": "ar",
    "ara": "ar",
    "arabic": "ar",
    "hi": "hi",
    "hin": "hi",
    "hindi": "hi",
    "nl": "nl",
    "nld": "nl",
    "dutch": "nl",
    "pl": "pl",
    "pol": "pl",
    "polish": "pl",
    "tr": "tr",
    "tur": "tr",
    "turkish": "tr",
}


def _canonical_language(label: str | None) -> str:
    if not label:
        return "auto"
    normalized = label.strip().lower()
    if not normalized:
        return "auto"
    normalized = normalized.replace("#", "").replace(" ", "")
    if normalized in _LANGUAGE_ALIASES:
        return _LANGUAGE_ALIASES[normalized]
    root = normalized.split("-")[0].split("_")[0]
    return _LANGUAGE_ALIASES.get(root, root)


@dataclass(frozen=True)
class TranslationResult:
    source_language: str
    target_language: str
    translated_text: str


_ARGOS_INIT_LOCK = threading.Lock()
_ARGOS_INITIALIZED = False


def _ensure_argos_ready() -> None:
    """Ensure Argos Translate is available and any local packages are installed."""

    global _ARGOS_INITIALIZED

    with _ARGOS_INIT_LOCK:
        if _ARGOS_INITIALIZED:
            return

        try:
            import argostranslate.package  # type: ignore
        except Exception as exc:
            raise RuntimeError(
                "Translation requested but Argos Translate is not installed. "
                "Install the 'argostranslate' Python package."
            ) from exc

        # Offline-first: install any .argosmodel packages present in configured dirs.
        # This is safe to run repeatedly; Argos will manage duplicates.
        for base_dir in ARGOS_MODEL_DIRS:
            folder = Path(base_dir)
            if not folder.exists() or not folder.is_dir():
                continue
            for package_path in sorted(folder.glob("*.argosmodel")):
                try:
                    argostranslate.package.install_from_path(str(package_path))
                except Exception:
                    # If a package is invalid/duplicate we just skip; the runtime
                    # translation will still fail with a clear message if missing.
                    continue

        _ARGOS_INITIALIZED = True


def translate_text(
    text: str,
    *,
    source_language: str | None,
    target_language: str | None,
) -> TranslationResult:
    """Translate `text` from `source_language` to `target_language`.

    - `source_language` may be "auto" (treated as DEFAULT_SOURCE_LANGUAGE).
    - If source and target are the same, the original text is returned.

    Raises ValueError when a required translation model is not installed.
    """

    cleaned = (text or "").strip()
    src = _canonical_language(source_language)
    tgt = _canonical_language(target_language)

    if src == "auto":
        src = _canonical_language(DEFAULT_SOURCE_LANGUAGE)

    if not tgt or tgt == "auto":
        raise ValueError("Missing target_language.")

    if not cleaned:
        return TranslationResult(source_language=src, target_language=tgt, translated_text="")

    if src == tgt:
        return TranslationResult(source_language=src, target_language=tgt, translated_text=cleaned)

    _ensure_argos_ready()

    import argostranslate.translate  # type: ignore

    try:
        translated = argostranslate.translate.translate(cleaned, src, tgt)
    except Exception as exc:
        raise ValueError(
            f"No offline translation model installed for '{src}' -> '{tgt}'. "
            "Install the appropriate Argos .argosmodel package into your environment "
            "or drop it into the configured ARGOS_MODEL_DIRS folder."
        ) from exc

    translated = (translated or "").strip()
    if not translated:
        # Conservatively fall back to original if model returns empty output.
        translated = cleaned

    return TranslationResult(source_language=src, target_language=tgt, translated_text=translated)


def list_installed_translation_pairs() -> list[dict[str, str]]:
    """List installed translation pairs available to Argos Translate.

    Returns a list of objects: {"from": "en", "to": "es"}.
    If Argos isn't installed or no packages are installed, returns an empty list.
    """

    try:
        _ensure_argos_ready()
    except Exception:
        return []

    try:
        import argostranslate.translate  # type: ignore
    except Exception:
        return []

    pairs: set[tuple[str, str]] = set()
    try:
        languages = argostranslate.translate.get_installed_languages()
    except Exception:
        return []

    for lang in languages or []:
        for translation in getattr(lang, "translations", []) or []:
            from_code = getattr(translation, "from_code", None)
            to_code = getattr(translation, "to_code", None)
            if not from_code or not to_code:
                continue
            pairs.add((str(from_code), str(to_code)))

    return [{"from": src, "to": tgt} for (src, tgt) in sorted(pairs)]
