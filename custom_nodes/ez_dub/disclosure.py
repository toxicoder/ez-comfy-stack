"""Localized spoken disclosure bumper. Overlay never changes mix length."""

from __future__ import annotations

from typing import Any, Callable

from .align import fit_turn, resample_linear

DISCLOSURE_TEXT = (
    "This audio is an AI-translated dub. Voices are synthesized from the "
    "original speakers with the rights-holder's authorization."
)

DISCLOSURE_LOCALIZED: dict[str, str] = {
    "en": DISCLOSURE_TEXT,
    "es": (
        "Este audio es un doblaje traducido por IA. "
        "Las voces están sintetizadas a partir de los hablantes originales "
        "con la autorización del titular de los derechos."
    ),
    "pt": (
        "Este áudio é uma dublagem traduzida por IA. "
        "As vozes são sintetizadas a partir dos falantes originais "
        "com autorização do titular dos direitos."
    ),
    "fr": (
        "Cet audio est un doublage traduit par IA. "
        "Les voix sont synthétisées à partir des intervenants d'origine "
        "avec l'autorisation du titulaire des droits."
    ),
    "de": (
        "Dieses Audio ist eine KI-übersetzte Synchronfassung. "
        "Die Stimmen wurden aus den Originalstimmen mit Zustimmung "
        "der Rechteinhaber synthetisiert."
    ),
    "it": (
        "Questo audio è un doppiaggio tradotto dall'IA. "
        "Le voci sono sintetizzate dagli speaker originali "
        "con l'autorizzazione del titolare dei diritti."
    ),
}

SynthesizeFn = Callable[..., Any]


def _lang_key(language: str) -> str:
    raw = (language or "").strip().lower()
    if raw in DISCLOSURE_LOCALIZED:
        return raw
    if len(raw) >= 2 and raw[:2] in DISCLOSURE_LOCALIZED:
        return raw[:2]
    return raw


def disclosure_for(language: str) -> str:
    """Localized bumper text; English canonical when the language is unknown."""
    key = _lang_key(language)
    return DISCLOSURE_LOCALIZED.get(key, DISCLOSURE_TEXT)


def _first_sentence(text: str) -> str:
    if len(text) <= 220:
        return text
    for sep in (". ", "! ", "? "):
        idx = text.find(sep)
        if idx > 0:
            return text[: idx + 1].strip()
    return text[:220].strip()


def _synth_pcm(
    synthesize: SynthesizeFn,
    text: str,
    language: str,
    ref_wav: str,
    engine: str,
) -> tuple[list[float], int]:
    result = synthesize(text, language, ref_wav, engine)
    if not result:
        return [], 0
    pcm = result[0]
    rate = int(result[1] or 0)
    if not pcm:
        return [], rate
    return [float(x) for x in pcm], rate


def _overlay_region(
    mix: list[float], bumper: list[float], n: int, fade: int
) -> None:
    count = min(n, len(mix), len(bumper))
    if count <= 0:
        return
    fade_n = max(1, min(int(fade), count))
    for i in range(count):
        gain = 1.0
        if i < fade_n:
            gain = i / fade_n
        remain = count - 1 - i
        if remain < fade_n:
            gain = min(gain, remain / fade_n if fade_n else 1.0)
        mix[i] = mix[i] * (1.0 - gain) + bumper[i] * gain


def _first_t0(turns: list[dict[str, Any]] | None) -> float:
    if not turns:
        return 0.0
    starts: list[float] = []
    for turn in turns:
        try:
            starts.append(float(turn.get("t0") or 0.0))
        except (TypeError, ValueError):
            continue
    if not starts:
        return 0.0
    return min(starts)


def apply_spoken_disclosure(
    mix: list[float],
    rate: int,
    *,
    language: str,
    engine: str,
    ref_wav: str,
    turns: list[dict[str, Any]] | None,
    synthesize: SynthesizeFn,
) -> tuple[list[float], str]:
    """Overlay a short localized bumper onto leading non-speech.

    Must NOT change len(mix).
    Must NOT call fit_turn(bumper, 3.0) on a long paragraph.
    """
    out = [float(x) for x in mix]
    sr = int(rate) or 1
    text = _first_sentence(disclosure_for(language))
    lang = (language or "").strip().lower() or "en"
    bumper, in_rate = _synth_pcm(synthesize, text, lang, ref_wav, engine)
    if not bumper:
        return out, "disclosure skipped"
    if in_rate and in_rate != sr:
        bumper = resample_linear(
            bumper, int(round(len(bumper) * sr / max(in_rate, 1)))
        )
    dur_s = len(bumper) / float(sr)
    if dur_s > 4.0:
        bumper, _flags = fit_turn(bumper, sr, 4.0, spill_s=0.0)
    gap_s = _first_t0(turns)
    fade = max(1, int(round(sr * 0.03)))
    if gap_s >= 1.2:
        gap_n = min(int(round(gap_s * sr)), len(out), len(bumper))
        _overlay_region(out, bumper, gap_n, fade)
    else:
        n = min(len(bumper), int(2.5 * sr), len(out))
        _overlay_region(out, bumper, n, fade)
    return out, "spoken disclosure"
