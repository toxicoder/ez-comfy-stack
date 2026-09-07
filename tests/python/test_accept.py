"""Wave 4.7 accept-gate (fail closed before concat)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_film import accept as acc  # noqa: E402
from ez_film import jobstore as js  # noqa: E402

SHORTS = ROOT / "workflows" / "shorts"


def _compile(tmp_path: Path) -> Path:
    dest = tmp_path / "films" / "gosee"
    text = (SHORTS / "go-see.shots.yaml").read_text(encoding="utf-8")
    js.compile_film(text, dest)
    return dest


def test_accept_fails_when_shots_pending(tmp_path: Path) -> None:
    dest = _compile(tmp_path)
    report = acc.accept_film(dest)
    assert report["ok"] is False
    assert any("status" in d for d in report["defects"])
    saved = json.loads((dest / "publish" / "accept.json").read_text(encoding="utf-8"))
    assert saved["ok"] is False


def test_accept_passes_with_injected_probes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dest = _compile(tmp_path)
    state = js.load_state(dest)
    for row in state["shots"]:
        sid = row["id"]
        mp4 = dest / "shots" / f"{sid}.mp4"
        mp4.parent.mkdir(parents=True, exist_ok=True)
        mp4.write_bytes(b"x")
        js.mark_shot(state, sid, "ok", mp4=f"shots/{sid}.mp4", backend="ltx")
    js.save_state(dest, state)
    monkeypatch.setattr(acc, "probe_duration_s", lambda *a, **k: 5.00)
    monkeypatch.setattr(acc, "probe_wh", lambda *a, **k: (1280, 704))
    monkeypatch.setattr(acc, "probe_has_audio", lambda *a, **k: True)
    report = acc.accept_film(dest)
    assert report["ok"] is True
    assert report["defects"] == []


def test_accept_cli_and_probes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dest = _compile(tmp_path)
    assert acc._cli(["--dest", str(dest)]) == 1  # noqa: SLF001
    monkeypatch.setattr(acc, "find_ffprobe", lambda: None)
    p = dest / "missing.mp4"
    assert acc.probe_duration_s(p) is None
    assert acc.probe_wh(p) is None
    assert acc.probe_has_audio(p) is False

    def fake_run(argv, **_kwargs):
        joined = " ".join(argv)
        if "format=duration" in joined:
            return SimpleNamespace(returncode=0, stdout="5.00\n", stderr="")
        if "width,height" in joined:
            return SimpleNamespace(returncode=0, stdout="1280,704\n", stderr="")
        if "codec_type" in joined:
            return SimpleNamespace(returncode=0, stdout="audio\n", stderr="")
        return SimpleNamespace(returncode=1, stdout="", stderr="")

    shot = dest / "shots" / "01.mp4"
    shot.parent.mkdir(parents=True, exist_ok=True)
    shot.write_bytes(b"x")
    monkeypatch.setattr(acc, "find_ffprobe", lambda: "/usr/bin/ffprobe")
    assert acc.probe_duration_s(shot, run=fake_run) == 5.00
    assert acc.probe_wh(shot, run=fake_run) == (1280, 704)
    assert acc.probe_has_audio(shot, run=fake_run) is True
    assert acc.film_dest(tmp_path, "go-see") == tmp_path / "films" / "gosee"
