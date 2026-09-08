"""Hermetic tests for ez_film.jobstore (no Comfy, no network, no GPU)."""

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

from ez_film import jobstore as js  # noqa: E402
from ez_film.shots import SHOT_COUNT  # noqa: E402

SHORTS = ROOT / "workflows" / "shorts"


def test_shot_id_and_new_state() -> None:
    assert js.shot_id(1, 1) == "01"
    assert js.shot_id(6, 3) == "18"
    with pytest.raises(ValueError):
        js.shot_id(7, 1)
    state = js.new_state("go-see", "gosee")
    assert len(state["shots"]) == SHOT_COUNT
    assert state["shots"][0]["status"] == "pending"
    assert state["shots"][11]["id"] == "12"


def test_compile_go_see(tmp_path: Path) -> None:
    yaml_text = (SHORTS / "go-see.shots.yaml").read_text(encoding="utf-8")
    dest = tmp_path / "films" / "gosee"
    state = js.compile_film(yaml_text, dest)
    assert state["slug"] == "gosee"
    assert state["audio_policy"] == "world-only"
    assert state["score"] == "none"
    assert (dest / "film.yaml").is_file()
    assert (dest / "stems").is_dir()
    assert (dest / "state.json").is_file()
    ids = [row["id"] for row in state["shots"]]
    assert ids == [f"{i:02d}" for i in range(1, 19)]
    stub = json.loads((dest / "shots" / "01.json").read_text(encoding="utf-8"))
    assert stub["template"] == "ltx-i2v-5s-lab-example.json"
    assert "sun-washed teal" in stub["identity"]
    assert "olive windbreaker" not in stub["identity"]
    assert stub["identity_enhance"] is True
    assert stub["identity_seed"] == 42
    assert stub["print"] == "ltx"
    assert stub["card"]["id"] == "01"
    assert stub["card"]["status"] == "pending"
    assert stub["card"]["camera"] == "dolly in"
    loaded = js.load_state(dest)
    assert js.get_shot(loaded, "12")["status"] == "pending"
    with pytest.raises(KeyError):
        js.get_shot(loaded, "99")
    with pytest.raises(ValueError, match="bad status"):
        js.mark_shot(loaded, "01", "nope")
    with pytest.raises(FileNotFoundError):
        js.load_state(tmp_path / "missing")


def test_compile_dfr_records_templates_path(tmp_path: Path) -> None:
    yaml_text = (SHORTS / "go-see.shots.yaml").read_text(encoding="utf-8")
    yaml_text = yaml_text.replace("print: ltx", "print: dfr", 1)
    dest = tmp_path / "films" / "gosee"
    js.compile_film(yaml_text, dest)
    stub = json.loads((dest / "shots" / "01.json").read_text(encoding="utf-8"))
    assert stub["print"] == "dfr"
    assert stub["template"] == "templates/ltx-2.5/t2v-i2v-two-stage-distilled"
    assert not (ROOT / "workflows" / stub["template"]).exists()


def test_mark_resume_and_skip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    yaml_text = (SHORTS / "go-see.shots.yaml").read_text(encoding="utf-8")
    dest = tmp_path / "gosee"
    state = js.compile_film(yaml_text, dest)
    js.mark_shot(state, "12", "running", backend="ltx")
    assert js.get_shot(state, "12")["take"] == 1
    js.mark_shot(state, "12", "ok", mp4="shots/12.mp4")
    js.save_state(dest, state)
    mp4 = dest / "shots" / "12.mp4"
    mp4.parent.mkdir(parents=True, exist_ok=True)
    mp4.write_bytes(b"x")
    monkeypatch.setattr(js, "probe_duration_s", lambda path: 5.00)
    assert js.should_skip_shot(dest, js.load_state(dest), "12") is True
    assert js.resume_ids(dest, js.load_state(dest)) == [
        f"{i:02d}" for i in range(1, 19) if i != 12
    ]
    crashed = js.load_state(dest)
    js.mark_shot(crashed, "11", "running")
    js.save_state(dest, crashed)
    assert "11" in js.resume_ids(dest, crashed)


def test_record_and_promote_take(tmp_path: Path) -> None:
    yaml_text = (SHORTS / "go-see.shots.yaml").read_text(encoding="utf-8")
    dest = tmp_path / "gosee"
    state = js.compile_film(yaml_text, dest)
    js.mark_shot(state, "12", "running")
    src = tmp_path / "raw.mp4"
    src.write_bytes(b"take-one")
    recorded = js.record_take(dest, state, "12", src)
    assert recorded.name == "t001.mp4"
    js.save_state(dest, state)
    promoted = js.promote_take(dest, "12", 1)
    assert promoted == dest / "shots" / "12.mp4"
    assert promoted.read_bytes() == b"take-one"
    row = js.get_shot(js.load_state(dest), "12")
    assert row["status"] == "ok"
    assert row["take"] == 1
    assert row["sha"]
    with pytest.raises(FileNotFoundError, match="missing take"):
        js.promote_take(dest, "12", 99)
    for i in range(2, 12):
        js.mark_shot(state, "12", "running")
        extra = tmp_path / f"t{i}.mp4"
        extra.write_bytes(bytes([i]))
        js.record_take(dest, state, "12", extra)
    nums = js.list_takes(dest, "12")
    assert len(nums) == js.TAKE_KEEP
    assert min(nums) == 4


def test_require_pins(tmp_path: Path) -> None:
    models = tmp_path / "models"
    js.require_pins(models)
    comfy = models / "comfy"
    comfy.mkdir(parents=True)
    pin = comfy / ".lab-model-pins.json"
    pin.write_text("{}", encoding="utf-8")
    js.require_pins(models)
    pin.write_text('{"ltx": "missing-weight.safetensors"}\n', encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="pin missing"):
        js.require_pins(models)
    (comfy / "diffusion_models").mkdir()
    (comfy / "diffusion_models" / "missing-weight.safetensors").write_bytes(b"x")
    js.require_pins(models)


def test_duration_ok_and_probe(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    p = tmp_path / "a.mp4"
    p.write_bytes(b"x")
    monkeypatch.setattr(js.shutil, "which", lambda n: None)
    assert js.probe_duration_s(p) is None
    monkeypatch.setattr(js.shutil, "which", lambda n: "/usr/bin/ffprobe")

    def fake_run(argv, **_k):
        return SimpleNamespace(returncode=0, stdout="5.00\n", stderr="")

    monkeypatch.setattr(js.subprocess, "run", fake_run)
    assert js.duration_ok(p) is True

    def bad_run(argv, **_k):
        return SimpleNamespace(returncode=0, stdout="nope\n", stderr="")

    monkeypatch.setattr(js.subprocess, "run", bad_run)
    assert js.probe_duration_s(p) is None

    def boom(*a, **k):
        raise OSError("x")

    monkeypatch.setattr(js.subprocess, "run", boom)
    assert js.probe_duration_s(p) is None


def test_cli_init_mark_resume(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    yaml_path = SHORTS / "go-see.shots.yaml"
    dest = tmp_path / "gosee"
    assert js._cli(["init", "--yaml", str(yaml_path), "--dest", str(dest)]) == 0  # noqa: SLF001
    assert js._cli(  # noqa: SLF001
        ["mark", "--dest", str(dest), "--id", "07", "--status", "ok", "--mp4", "shots/07.mp4"]
    ) == 0
    (dest / "shots" / "07.mp4").write_bytes(b"x")
    monkeypatch.setattr(js, "probe_duration_s", lambda path: 5.00)
    assert js._cli(["should-skip", "--dest", str(dest), "--id", "07"]) == 0  # noqa: SLF001
    assert js._cli(["should-skip", "--dest", str(dest), "--id", "08"]) == 1  # noqa: SLF001
    rc = js._cli(["resume-ids", "--dest", str(dest)])  # noqa: SLF001
    assert rc == 0
    assert js._cli(["get", "--dest", str(dest), "--id", "07"]) == 0  # noqa: SLF001
    assert js._cli(["get", "--dest", str(dest), "--id", "99"]) == 1  # noqa: SLF001
    models = tmp_path / "models"
    models.mkdir()
    assert js._cli(["require-pins", "--models-dir", str(models)]) == 0  # noqa: SLF001


def test_cli_missing_store() -> None:
    assert js._cli(["get", "--dest", "/nope", "--id", "01"]) == 1  # noqa: SLF001
    assert js._cli(["mark", "--dest", "/nope", "--id", "01", "--status", "ok"]) == 1  # noqa: SLF001
