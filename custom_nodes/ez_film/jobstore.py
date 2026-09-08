"""Host film jobstore: films/<slug>/state.json (hermetic at import)."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from .prompt_enums import shot_card
from .shots import FILM_SLUGS, SHOT_COUNT, parse_shots_yaml, print_template

STATUSES = ("pending", "running", "ok", "failed", "skipped")
DURATION_S = 5.00
DURATION_TOL = 0.05
TAKE_KEEP = 8
PINS_REL = Path("comfy") / ".lab-model-pins.json"


def shot_id(beat: int, shot: int) -> str:
    """Map YAML beat/shot (1-based) to ``01``…``18``."""
    n = (beat - 1) * 3 + shot
    if n < 1 or n > SHOT_COUNT:
        raise ValueError(f"shot index {n} out of range")
    return f"{n:02d}"


def film_dir(output_dir: Path, slug: str) -> Path:
    """``${COMFY_OUTPUT_DIR}/films/<slug>``."""
    return Path(output_dir) / "films" / slug


def state_path(dest: Path) -> Path:
    """Path to state.json."""
    return dest / "state.json"


def empty_shot(sid: str) -> dict[str, Any]:
    """One pending shot row."""
    return {
        "id": sid,
        "status": "pending",
        "mp4": None,
        "last_frame": None,
        "audio": None,
        "take": 0,
        "error": None,
        "sha": None,
        "backend": None,
    }


def new_state(
    film: str,
    slug: str,
    *,
    audio_policy: str = "world-only",
    score: str = "none",
) -> dict[str, Any]:
    """Fresh 18-shot pending state."""
    shots = [empty_shot(f"{i:02d}") for i in range(1, SHOT_COUNT + 1)]
    return {
        "film": film,
        "slug": slug,
        "audio_policy": audio_policy,
        "score": score,
        "shots": shots,
    }


def load_state(dest: Path) -> dict[str, Any]:
    """Read state.json."""
    path = state_path(dest)
    if not path.is_file():
        raise FileNotFoundError(f"missing jobstore {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "shots" not in data:
        raise ValueError(f"invalid jobstore {path}")
    return data


def save_state(dest: Path, state: dict[str, Any]) -> None:
    """Write state.json atomically enough for a single operator."""
    dest.mkdir(parents=True, exist_ok=True)
    path = state_path(dest)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def get_shot(state: dict[str, Any], sid: str) -> dict[str, Any]:
    """Return the shot row or raise."""
    for row in state["shots"]:
        if row.get("id") == sid:
            return row
    raise KeyError(f"unknown shot id {sid}")


def probe_duration_s(path: Path) -> float | None:
    """ffprobe format duration, or None."""
    exe = shutil.which("ffprobe")
    if not exe or not path.is_file():
        return None
    try:
        proc = subprocess.run(
            [
                exe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "csv=p=0",
                str(path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    text = (proc.stdout or "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def duration_ok(path: Path, expected: float = DURATION_S, tol: float = DURATION_TOL) -> bool:
    """True when the MP4 exists and duration is expected ± tol."""
    dur = probe_duration_s(path)
    if dur is None:
        return False
    return abs(dur - expected) <= tol


def shot_mp4(dest: Path, sid: str) -> Path:
    """``shots/NN.mp4`` under the film dir."""
    return dest / "shots" / f"{sid}.mp4"


def take_dir(dest: Path, sid: str) -> Path:
    """``takes/<id>/`` under the film dir."""
    return dest / "takes" / sid


def take_path(dest: Path, sid: str, take: int) -> Path:
    """``takes/<id>/tNNN.mp4``."""
    return take_dir(dest, sid) / f"t{int(take):03d}.mp4"


def file_sha(path: Path) -> str:
    """Short sha256 of a file (empty if missing)."""
    if not path.is_file():
        return ""
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest[:16]


def list_takes(dest: Path, sid: str) -> list[int]:
    """Take numbers present on disk, newest last."""
    folder = take_dir(dest, sid)
    if not folder.is_dir():
        return []
    found: list[int] = []
    for path in folder.glob("t*.mp4"):
        stem = path.stem
        if stem.startswith("t") and stem[1:].isdigit():
            found.append(int(stem[1:]))
    return sorted(found)


def prune_takes(dest: Path, sid: str, keep: int = TAKE_KEEP) -> None:
    """Keep the last ``keep`` takes."""
    nums = list_takes(dest, sid)
    extra = nums[:-keep] if keep >= 0 else nums
    for num in extra:
        take_path(dest, sid, num).unlink(missing_ok=True)


def record_take(dest: Path, state: dict[str, Any], sid: str, src: Path) -> Path:
    """Copy ``src`` into the take strip for this shot (current take number)."""
    if not src.is_file():
        raise FileNotFoundError(f"missing take source {src}")
    row = get_shot(state, sid)
    take = int(row.get("take") or 1)
    dest_mp4 = take_path(dest, sid, take)
    dest_mp4.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest_mp4)
    row["sha"] = file_sha(dest_mp4)
    prune_takes(dest, sid)
    return dest_mp4


def promote_take(dest: Path, sid: str, take: int) -> Path:
    """Copy take N to ``shots/NN.mp4`` and mark the shot ok."""
    src = take_path(dest, sid, take)
    if not src.is_file():
        raise FileNotFoundError(f"missing take {sid}/t{int(take):03d}")
    dest_mp4 = shot_mp4(dest, sid)
    dest_mp4.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest_mp4)
    state = load_state(dest)
    mark_shot(
        state,
        sid,
        "ok",
        mp4=f"shots/{sid}.mp4",
        take=int(take),
    )
    get_shot(state, sid)["sha"] = file_sha(dest_mp4)
    save_state(dest, state)
    return dest_mp4


def should_skip_shot(dest: Path, state: dict[str, Any], sid: str) -> bool:
    """Idempotent skip: status ok and duration 5.00±0.05."""
    row = get_shot(state, sid)
    mp4 = dest / row["mp4"] if row.get("mp4") else shot_mp4(dest, sid)
    if row.get("status") != "ok":
        return False
    return duration_ok(mp4)


def resume_ids(dest: Path, state: dict[str, Any]) -> list[str]:
    """Shot ids that still need a print (not ok-with-valid-mp4)."""
    needed: list[str] = []
    for row in state["shots"]:
        sid = str(row["id"])
        if should_skip_shot(dest, state, sid):
            continue
        if row.get("status") == "skipped":
            continue
        needed.append(sid)
    return needed


def mark_shot(
    state: dict[str, Any],
    sid: str,
    status: str,
    *,
    mp4: str | None = None,
    error: str | None = None,
    backend: str | None = None,
    take: int | None = None,
) -> dict[str, Any]:
    """Update one shot row. Increments take when status becomes running."""
    if status not in STATUSES:
        raise ValueError(f"bad status {status}")
    row = get_shot(state, sid)
    row["status"] = status
    if mp4 is not None:
        row["mp4"] = mp4
    if error is not None or status != "failed":
        row["error"] = error
    if backend is not None:
        row["backend"] = backend
    if status == "running":
        row["take"] = int(row.get("take") or 0) + 1
        row["error"] = None
    elif take is not None:
        row["take"] = take
    return row


def load_pins(models_dir: Path) -> dict[str, str] | None:
    """Load optional pin file. None if missing."""
    path = Path(models_dir) / PINS_REL
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"invalid pins file {path}")
    return {str(k): str(v) for k, v in data.items()}


def require_pins(models_dir: Path) -> None:
    """Fail if a pins file lists basenames that are not under comfy/.

    Missing pins file is OK (Wave 0). Empty object is OK.
    """
    pins = load_pins(models_dir)
    if not pins:
        return
    comfy = Path(models_dir) / "comfy"
    missing: list[str] = []
    for _key, basename in pins.items():
        if not basename:
            continue
        hits = list(comfy.rglob(basename)) if comfy.is_dir() else []
        if not hits:
            missing.append(basename)
    if missing:
        raise FileNotFoundError(
            "model pin missing (refuse resume): " + ", ".join(missing)
        )


def compile_film(
    yaml_text: str,
    dest: Path,
    *,
    template: str | None = None,
) -> dict[str, Any]:
    """Write film.yaml, per-shot JSON stubs, and state.json (pending)."""
    parsed = parse_shots_yaml(yaml_text)
    meta = parsed["meta"]
    film = str(meta["film"])
    slug = str(meta["slug"])
    if FILM_SLUGS.get(film) != slug:
        raise ValueError(f"slug mismatch for {film}: {slug}")
    chosen = template or print_template(meta["print"])
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "shots").mkdir(exist_ok=True)
    (dest / "takes").mkdir(exist_ok=True)
    (dest / "stems").mkdir(exist_ok=True)
    (dest / "film.yaml").write_text(yaml_text, encoding="utf-8")
    state = new_state(
        film,
        slug,
        audio_policy=str(meta.get("audio_policy") or "world-only"),
        score=str(meta.get("score") or "none"),
    )
    for yaml_shot in parsed["shots"]:
        beat = int(yaml_shot["beat"])
        shot = int(yaml_shot["shot"])
        sid = shot_id(beat, shot)
        payload = {
            "id": sid,
            "template": chosen,
            "prefix": yaml_shot["prefix"],
            "load_from": yaml_shot["load_from"],
            "ltx_i2v": yaml_shot["ltx_i2v"],
            "wan_i2v": yaml_shot["wan_i2v"],
            "identity": parsed["identity"],
            "print": meta["print"],
            "identity_seed": int(meta["identity_seed"]),
            "identity_enhance": meta["identity_enhance"].lower()
            in ("true", "1", "on", "yes"),
            "card": shot_card(
                sid,
                status="pending",
                camera=str(yaml_shot.get("camera") or "dolly in"),
            ),
            "clay": yaml_shot.get("clay") or "skip",
            "dialogue": yaml_shot.get("dialogue") or "",
            "audio_lock": yaml_shot.get("audio_lock") or "none",
            "camera": yaml_shot.get("camera") or "",
            "script": yaml_shot.get("script") or "",
        }
        (dest / "shots" / f"{sid}.json").write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8"
        )
    save_state(dest, state)
    return state


def _cli(argv: list[str] | None = None) -> int:
    """Jobstore CLI used by compile-film.sh / print-shot.sh."""
    parser = argparse.ArgumentParser(prog="ez_film.jobstore")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init")
    p_init.add_argument("--yaml", required=True)
    p_init.add_argument("--dest", required=True)
    p_init.add_argument("--template", default=None)

    p_mark = sub.add_parser("mark")
    p_mark.add_argument("--dest", required=True)
    p_mark.add_argument("--id", required=True)
    p_mark.add_argument("--status", required=True, choices=STATUSES)
    p_mark.add_argument("--mp4")
    p_mark.add_argument("--error")
    p_mark.add_argument("--backend")

    p_skip = sub.add_parser("should-skip")
    p_skip.add_argument("--dest", required=True)
    p_skip.add_argument("--id", required=True)

    p_resume = sub.add_parser("resume-ids")
    p_resume.add_argument("--dest", required=True)

    p_pins = sub.add_parser("require-pins")
    p_pins.add_argument("--models-dir", required=True)

    p_get = sub.add_parser("get")
    p_get.add_argument("--dest", required=True)
    p_get.add_argument("--id", required=True)

    p_promote = sub.add_parser("promote")
    p_promote.add_argument("--dest", required=True)
    p_promote.add_argument("--id", required=True)
    p_promote.add_argument("--take", required=True, type=int)

    p_record = sub.add_parser("record-take")
    p_record.add_argument("--dest", required=True)
    p_record.add_argument("--id", required=True)
    p_record.add_argument("--src", required=True)

    args = parser.parse_args(argv)
    try:
        if args.cmd == "init":
            text = Path(args.yaml).read_text(encoding="utf-8")
            compile_film(text, Path(args.dest), template=args.template)
            return 0
        if args.cmd == "mark":
            dest = Path(args.dest)
            state = load_state(dest)
            mark_shot(
                state,
                args.id,
                args.status,
                mp4=args.mp4,
                error=args.error,
                backend=args.backend,
            )
            save_state(dest, state)
            return 0
        if args.cmd == "should-skip":
            dest = Path(args.dest)
            state = load_state(dest)
            return 0 if should_skip_shot(dest, state, args.id) else 1
        if args.cmd == "resume-ids":
            dest = Path(args.dest)
            state = load_state(dest)
            for sid in resume_ids(dest, state):
                print(sid)
            return 0
        if args.cmd == "require-pins":
            require_pins(Path(args.models_dir))
            return 0
        if args.cmd == "get":
            dest = Path(args.dest)
            state = load_state(dest)
            print(json.dumps(get_shot(state, args.id)))
            return 0
        if args.cmd == "promote":
            path = promote_take(Path(args.dest), args.id, args.take)
            print(path)
            return 0
        if args.cmd == "record-take":
            dest = Path(args.dest)
            state = load_state(dest)
            path = record_take(dest, state, args.id, Path(args.src))
            save_state(dest, state)
            print(path)
            return 0
    except (FileNotFoundError, KeyError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(_cli())
