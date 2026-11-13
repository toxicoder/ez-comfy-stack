"""ez-comfy generated Android tone pack (ringtones, notifications, alarms).

No nodes: this is a library and an operator CLI, so nothing here touches
Comfy. Import is hermetic - stdlib only, no torch, no numpy - and the
audio work is own-code synthesis plus ffmpeg subprocesses.

Add a tone by editing catalog JSON, not Python: the export verb writes a
template with :func:`write_catalog_template` and merges an operator file
back in with :func:`load_catalog`. The exporter itself stays a submodule
(:mod:`ez_tones.pack`) so running it as a module needs no package import.
"""

from __future__ import annotations

from .catalog import (
    KINDS,
    TONE_CATALOG,
    ToneKind,
    ToneSpec,
    by_slug,
    categories,
    load_catalog,
    tones_for,
    validate,
    write_catalog_template,
)
from .synth import (
    PEAK_CEILING,
    TIMBRES,
    Timbre,
    hz_to_midi,
    midi_to_hz,
    render_motif,
)

__all__ = [
    "PEAK_CEILING",
    "TIMBRES",
    "TONE_CATALOG",
    "KINDS",
    "Timbre",
    "ToneKind",
    "ToneSpec",
    "by_slug",
    "categories",
    "hz_to_midi",
    "load_catalog",
    "midi_to_hz",
    "render_motif",
    "tones_for",
    "validate",
    "write_catalog_template",
]
