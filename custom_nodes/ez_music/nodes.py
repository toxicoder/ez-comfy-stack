"""ComfyUI node for US-safe original rap lyrics (ACE-Step encoder companion)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypedDict, cast

if TYPE_CHECKING:
    from ez_common import ComfyInputTypes

    from .metadata import AudioMeta

from .fs import AUDIO_SUFFIXES, output_dir
from .song_plan import demo_draft_lyrics, demo_full_lyrics

# Prompt path, flavor id, and canned lyrics widgets.
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
FLAVOR_RAP = "rap_lyrics"

# Demo lyrics come from the song plan (cold open, then a pre-chorus full take).
DRAFT_LYRICS = demo_draft_lyrics()
FULL_LYRICS = demo_full_lyrics()


def _log(message: str) -> None:
    """Write an ez_music status line to stderr.

    Args:
        message: Human status without a trailing newline.
    """
    try:
        from ez_common import node_log

        node_log("ez_music", message)
    except Exception:  # noqa: BLE001 - pytest / missing sibling pack
        print(f"[ez_music] {message}", file=sys.stderr)


def _sample_combo() -> tuple:
    """Rap-draft sample combo widget for EZRapLyrics.

    Returns:
        Comfy combo spec ``(labels, {default})``.
    """
    _ensure_lab_custom_nodes_path()
    from ez_prompt_enhance.samples import CUSTOM, sample_combo_labels

    return (sample_combo_labels("rap_draft"), {"default": CUSTOM})


def _ensure_lab_custom_nodes_path() -> None:
    """Make sibling ez_* packs importable under ComfyUI 0.34+ load_custom_node.

    Comfy registers directory packs as the filesystem path, not the folder
    name, and does not put custom_nodes on sys.path.
    """
    root = Path(__file__).resolve().parent.parent
    try:
        from ez_common import ensure_custom_nodes_path

        ensure_custom_nodes_path(anchor=root)
    except Exception:  # noqa: BLE001 - ez_common is itself a sibling
        text = str(root)
        if text not in sys.path:
            sys.path.insert(0, text)


def _as_bool(value: object) -> bool:
    """Coerce a widget value to bool.

    Args:
        value: Boolean, number, or truthy string.

    Returns:
        True for ``1`` / ``true`` / ``yes`` / ``on`` and numeric non-zero.
    """
    if isinstance(value, bool):
        return bool(value)
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def load_writer_prompt(name: str = FLAVOR_RAP) -> str:
    """Load the rap-lyrics system prompt from this pack.

    Args:
        name: stem without .txt (default ``rap_lyrics``).
    Returns:
        File contents stripped of trailing whitespace.
    Raises:
        FileNotFoundError if the prompt file is missing.
    """
    stem = name if name else FLAVOR_RAP
    path = PROMPTS_DIR / f"{stem}.txt"
    return path.read_text(encoding="utf-8").strip()


def _pack_text(
    text: str,
    status: str | None = None,
    *,
    result: tuple[object, ...] | None = None,
) -> dict[str, Any]:
    """Build an output-node payload with a UI line and a result pin.

    Args:
        text: UI status text.
        status: Passthrough text; omit for a text-only ``ui``.
        result: Result pin tuple; defaults to ``(text,)``.

    Returns:
        Comfy ``ui`` plus ``result`` dict.
    """
    ui: dict[str, Any] = {"text": (text,)}
    if status is not None:
        ui["passthrough"] = (status,)
    return {
        "ui": ui,
        "result": result if result is not None else (text,),
    }


class EZRapLyrics:
    """Draft original rap lyrics via the on-box GGUF. Enhance defaults off."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Declare Comfy widgets for this node.

        Returns:
            Required and optional input specs.
        """
        return {
            "required": {
                "sample": _sample_combo(),
                "lyrics": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": DRAFT_LYRICS,
                        "dynamicPrompts": False,
                    },
                ),
                "enhance": (
                    "BOOLEAN",
                    {"default": True, "label_on": "On", "label_off": "Off"},
                ),
                "catalog": ("STRING", {"default": "", "multiline": False}),
            },
            "optional": {
                "context": (
                    "STRING",
                    {"forceInput": True, "dynamicPrompts": False},
                ),
            },
        }

    # Comfy node contract.
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("lyrics",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/music"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Rewrites lab-original rap lyrics with the on-box Qwen3-4B-Instruct "
        "GGUF. Enhance defaults on. Missing GGUF passes the widget text "
        "through. Forbids living-MC names and famous hooks. ACE-Step still "
        "invents the vocal timbre from tags plus lyrics."
    )

    def run(
        self,
        lyrics: str,
        enhance: bool = False,
        context: str = "",
        sample: str = "custom",
        catalog: str = "",
    ) -> dict[str, Any]:
        """Rewrite widget lyrics via the on-box GGUF when enhance is on.

        Args:
            lyrics: Widget or resolved sample lyrics.
            enhance: When false, pass the text through.
            context: Optional extra system context.
            sample: Sample combo label.
            catalog: Catalog override for sample lookup.

        Returns:
            Output-node dict with lyrics on ``result``.
        """
        _ensure_lab_custom_nodes_path()
        from ez_prompt_enhance.samples import resolve_prompt

        original = resolve_prompt(
            catalog,
            sample,
            lyrics,
            node_type="EZRapLyrics",
        )
        ctx = context if isinstance(context, str) else str(context or "")
        if not _as_bool(enhance):
            return _pack_text(original, "enhance off")
        return _rewrite_via_gguf(original, ctx)


def _rewrite_via_gguf(original: str, ctx: str) -> dict[str, Any]:
    """Rewrite lyrics with the on-box GGUF, passing text through on failure.

    Args:
        original: Resolved widget or sample lyrics.
        ctx: Extra system context already coerced to str.

    Returns:
        Output-node dict with the rewritten or passed-through lyrics.
    """
    try:
        _ensure_lab_custom_nodes_path()
        from ez_prompt_enhance.client import _close_llm
        from ez_prompt_enhance.client import complete
        from ez_prompt_enhance.client import compose_context_user
        from ez_prompt_enhance.client import with_context_system
    except Exception as exc:  # noqa: BLE001 - fail-soft
        _log(f"prompt enhance client unavailable: {exc}")
        return _pack_text(original, "llama.cpp unavailable")
    try:
        system = with_context_system(load_writer_prompt(FLAVOR_RAP), ctx)
    except FileNotFoundError as exc:
        _log(f"rap lyrics prompt missing: {exc}")
        return _pack_text(original, "passthrough")
    _log("rewriting rap lyrics via on-box GGUF...")
    try:
        rewritten, reason = complete(system, compose_context_user(original, ctx))
    finally:
        try:
            _close_llm()
        except Exception as exc:  # noqa: BLE001 - unload is best-effort
            _log(f"writer unload failed: {exc}")
    if not (rewritten or "").strip():
        return _pack_text(original, reason or "passthrough")
    return _pack_text(rewritten, "")


class EZAudioMetadata:
    """Stamp artist/album/title tags and optional cover on saved audio."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Declare Comfy widgets for this node.

        Returns:
            Required and optional input specs.
        """
        return {
            "required": {
                "audio": ("AUDIO",),
                "artist": ("STRING", {"default": "", "multiline": False}),
                "album": ("STRING", {"default": "", "multiline": False}),
                "title": ("STRING", {"default": "", "multiline": False}),
                "track": ("INT", {"default": 1, "min": 1, "max": 99}),
                "tracktotal": ("INT", {"default": 1, "min": 1, "max": 99}),
                "year": ("INT", {"default": 2026, "min": 1900, "max": 2100}),
                "art_mode": (["skip", "upload", "generate"], {"default": "skip"}),
                "prefix": ("STRING", {"default": "", "multiline": False}),
            },
            "optional": {
                "cover": ("IMAGE",),
            },
        }

    # Comfy node contract.
    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/music"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Copies ACE SaveAudio masters into albums/<Artist>/<Album>/ and "
        "writes artist/album/title tags. Album art: skip, upload (IMAGE), "
        "or generate (use cover.jpg from the album folder)."
    )

    def run(
        self,
        audio: object,
        artist: str = "",
        album: str = "",
        title: str = "",
        track: int = 1,
        tracktotal: int = 1,
        year: int = 2026,
        art_mode: str = "skip",
        prefix: str = "",
        cover: object | None = None,
    ) -> dict[str, Any]:
        """Copy SaveAudio masters into the album folder and stamp tags.

        Args:
            audio: ACE AUDIO payload (passed through).
            artist: Act name.
            album: Album title.
            title: Track title.
            track: One-based track number.
            tracktotal: Album track count.
            year: Release year.
            art_mode: ``skip``, ``upload``, or ``generate``.
            prefix: SaveAudio stem to match; derived from title when empty.
            cover: Optional Comfy IMAGE tensor.

        Returns:
            Output-node dict with the original AUDIO on ``result``.
        """
        from .metadata import AudioMeta, album_dir_from_env

        meta = AudioMeta(
            artist=str(artist or "").strip(),
            album=str(album or "").strip(),
            title=str(title or "").strip(),
            track=int(track),
            tracktotal=int(tracktotal),
            year=int(year),
            art_mode=str(art_mode or "skip"),
        )
        dest = album_dir_from_env(meta.artist or "Unknown", meta.album or "Untitled")
        art = _resolve_album_art(meta, dest, cover)
        if art["error"] is not None and meta.art_mode != "skip":
            return _pack_text(art["error"], result=(audio,))
        status = _stamp_masters(meta, dest, art["cover_path"], prefix)
        _log(status)
        return _pack_text(status, result=(audio,))


class _AlbumArt(TypedDict):
    """Cover-art resolution result for the metadata node.

    Attributes:
        cover_path: Art to stamp, copied into the album folder, or None.
        error: Reason art could not be resolved, or None on success.
    """

    cover_path: Path | None
    error: str | None


def _resolve_album_art(meta: AudioMeta, dest: Path, cover: object | None) -> _AlbumArt:
    """Pick cover art for one album folder and normalise it into that folder.

    Args:
        meta: ``AudioMeta`` instance; only its ``art_mode`` is read.
        dest: ``albums/<Artist>/<Album>`` folder.
        cover: Optional Comfy IMAGE tensor used as the upload.

    Returns:
        Cover path plus the fail-soft reason when art is unavailable.
    """
    from .metadata import resolve_cover

    art_mode = str(meta.art_mode or "skip")
    upload_path: Path | None = None
    if cover is not None:
        candidate = dest / "cover.png"
        try:
            _save_cover_tensor(cover, candidate)
        except Exception as exc:  # noqa: BLE001 - optional art
            _log(f"cover tensor save failed: {exc}")
        else:
            upload_path = candidate
    try:
        cover_path = resolve_cover(
            art_mode=art_mode,
            upload=upload_path,
            album_dir=dest,
        )
    except ValueError as exc:
        _log(str(exc))
        return {"cover_path": None, "error": str(exc)}
    if cover_path is not None and cover_path.parent != dest:
        copied = dest / "cover.jpg"
        copied.write_bytes(cover_path.read_bytes())
        cover_path = copied
    return {"cover_path": cover_path, "error": None}


def _stamp_masters(meta: AudioMeta, dest: Path, cover_path: Path | None, prefix: str) -> str:
    """Copy matching SaveAudio masters into the album folder and tag them.

    Args:
        meta: ``AudioMeta`` instance; the stem derives from title/track.
        dest: Destination album folder.
        cover_path: Cover art to embed, or None.
        prefix: SaveAudio stem to match; derived from title when empty.

    Returns:
        Operator status line describing what was tagged.
    """
    from .naming import music_output_prefix

    title = str(meta.title or "")
    track = int(meta.track)
    stem = str(prefix or "").strip()
    if not stem and title:
        stem = music_output_prefix(title, track)
    stamped = _stamp_output_masters(stem, dest, meta, cover_path)
    return f"tagged {len(stamped)} file(s)" if stamped else "no SaveAudio masters yet"


class EZAlbumPack:
    """Zip albums/<Artist>/<Album>/ for one-shot download."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Declare Comfy widgets for this node.

        Returns:
            Required and optional input specs.
        """
        return {
            "required": {
                "artist": ("STRING", {"default": "", "multiline": False}),
                "album": ("STRING", {"default": "", "multiline": False}),
            }
        }

    # Comfy node contract.
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("zip_path",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/music"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Writes <Album>.m3u and <Album>.zip under albums/<Artist>/<Album>/. "
        "Queue tracks first (or album-render). CPU only."
    )

    def run(self, artist: str = "", album: str = "") -> dict[str, Any]:
        """Zip the album output folder.

        Args:
            artist: Act name.
            album: Album title.

        Returns:
            Output-node dict with the zip path on ``result``.
        """
        from .metadata import album_dir_from_env
        from .pack import pack_album

        artist_s = str(artist or "").strip() or "Unknown"
        album_s = str(album or "").strip() or "Untitled"
        dest = album_dir_from_env(artist_s, album_s)
        try:
            zip_path = pack_album(dest, album=album_s)
        except FileNotFoundError as exc:
            _log(str(exc))
            return _pack_text(str(exc), result=("",))
        _log(f"packed {zip_path}")
        return _pack_text(str(zip_path))


def _save_cover_tensor(image: object, dest: Path) -> Path:
    """Write a Comfy IMAGE tensor as PNG. Best-effort.

    Args:
        image: Comfy IMAGE tensor or array-like.
        dest: PNG path.

    Returns:
        ``dest``.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    array: Any = image
    cpu = getattr(image, "cpu", None)
    if callable(cpu):
        array = cast(Any, cpu()).numpy()
    import numpy as np
    from PIL import Image

    data = np.asarray(array)
    if data.ndim == 4:
        data = data[0]
    if data.max() <= 1.0:
        data = data * 255.0
    Image.fromarray(data.clip(0, 255).astype("uint8")).save(dest)
    return dest


def _output_root(album_dir: Path) -> Path:
    """Comfy output dir, else the album folder (tests).

    Args:
        album_dir: Fallback when Comfy and env are unset.

    Returns:
        Directory that contains SaveAudio masters.
    """
    return output_dir(default=album_dir)


def _stamp_output_masters(
    prefix: str,
    album_dir: Path,
    meta: object,
    cover: Path | None,
) -> list[Path]:
    """Copy SaveAudio files matching prefix into the album folder and tag them.

    Args:
        prefix: SaveAudio filename stem to glob.
        album_dir: Destination album folder.
        meta: ``AudioMeta`` instance; other types skip stamping.
        cover: Optional cover image.

    Returns:
        Paths of tagged copies.
    """
    import shutil

    from .metadata import AudioMeta, stamp_audio_file

    if not isinstance(meta, AudioMeta) or not prefix:
        return []
    output_root = _output_root(album_dir)
    hits: list[Path] = []
    for suffix in AUDIO_SUFFIXES:
        hits.extend(sorted(output_root.glob(f"{prefix}*{suffix}")))
    stamped: list[Path] = []
    for src in hits:
        dest = album_dir / src.name
        if src.resolve() != dest.resolve():
            shutil.copy2(src, dest)
        stamp_audio_file(dest, meta, cover)
        stamped.append(dest)
    return stamped


class EZAudioBeatJoin:
    """Join multi-pass ACE masters into one beat-aligned take."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Declare Comfy widgets and the audio_XX segment sockets.

        Returns:
            Required and optional input specs.
        """
        from .join import MAX_JOIN_SEGMENTS

        optional = {
            f"audio_{index:02d}": ("AUDIO",)
            for index in range(2, MAX_JOIN_SEGMENTS + 1)
        }
        return {
            "required": {
                "audio_01": ("AUDIO",),
                "bpm": ("INT", {"default": 172, "min": 40, "max": 300}),
                "overlap_bars": (
                    "STRING",
                    {
                        "default": "2",
                        "multiline": False,
                        "tooltip": "Whole bars per seam: one number for "
                        "all seams, or comma-separated per seam.",
                    },
                ),
                "crossover_hz": (
                    "FLOAT",
                    {"default": 120.0, "min": 40.0, "max": 500.0, "step": 5.0},
                ),
            },
            "optional": optional,
        }

    # Comfy node contract.
    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/music"
    DESCRIPTION = (
        "Stitches the ACE passes of one Drive-through pass into a single "
        "master on the bar grid: each seam overlaps whole bars, the 808 "
        "hand-off never stacks or nulls, and the crossfade never clicks. "
        "Wire audio_01, then audio_02..audio_08 in render order."
    )

    def run(
        self,
        bpm: float,
        overlap_bars: str | int,
        crossover_hz: float,
        **segments: object,
    ) -> tuple[object]:
        """Join the wired AUDIO passes in render order.

        Args:
            bpm: Tempo that defines the bar grid and the seams.
            overlap_bars: Whole bars overlapped at each seam; one number
                or a comma-separated list, one entry per seam.
            crossover_hz: Sub/mid split for the hand-off.
            segments: ``audio_01`` .. ``audio_08`` AUDIO payloads; a
                hole ahead of a later pass is a graph error.

        Returns:
            One-element tuple with the master AUDIO.

        Raises:
            ValueError: audio_01 is unwired, a hole sits before a wired
                socket, or the join parameters are invalid.
        """
        from .join import MAX_JOIN_SEGMENTS, join_audio

        wired: list[dict[str, Any]] = []
        for index in range(1, MAX_JOIN_SEGMENTS + 1):
            name = f"audio_{index:02d}"
            value = segments.get(name)
            if value is None:
                break
            wired.append(cast("dict[str, Any]", value))
        for name in segments:
            if name.startswith("audio_") and segments[name] is not None:
                position = int(name.removeprefix("audio_"))
                if position > len(wired) + 1:
                    raise ValueError(
                        f"audio_{position - 1:02d} is unwired ahead of "
                        f"{name}; wire the passes in render order"
                    )
        if not wired:
            raise ValueError("audio_01 needs an ACE pass")
        return (join_audio(wired, bpm=float(bpm),
                           overlap_bars=_parse_overlap(overlap_bars),
                           crossover_hz=float(crossover_hz)),)


def _parse_overlap(value: str | int | list[int]) -> int | list[int]:
    """Read the overlap widget as one number or a per-seam list.

    Args:
        value: The raw ``overlap_bars`` widget value.

    Returns:
        An int or a list of ints for ``join_audio``.

    Raises:
        ValueError: an entry is not a whole number of bars.
    """
    if isinstance(value, int):
        return value
    if isinstance(value, (list, tuple)):
        parts = [str(piece).strip() for piece in value]
    else:
        parts = [piece.strip() for piece in str(value).split(",") if piece.strip()]
    if not parts:
        raise ValueError("overlap_bars needs a number of bars")
    try:
        numbers = [int(piece) for piece in parts]
    except ValueError as exc:
        raise ValueError(f"overlap_bars needs whole bars: {value!r}") from exc
    if len(numbers) == 1:
        return numbers[0]
    return numbers


# Comfy registry.
NODE_CLASS_MAPPINGS = {
    "EZRapLyrics": EZRapLyrics,
    "EZAudioMetadata": EZAudioMetadata,
    "EZAlbumPack": EZAlbumPack,
    "EZAudioBeatJoin": EZAudioBeatJoin,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EZRapLyrics": "Rap Lyrics",
    "EZAudioMetadata": "Album metadata",
    "EZAlbumPack": "Pack album zip",
    "EZAudioBeatJoin": "Beat-join passes",
}
