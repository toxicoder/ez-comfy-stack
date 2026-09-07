"""Wave 2 contracts: no H3 Director, no Wav2Lip, no Postgres, studio-ui empty page."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_phase_nodes_director_is_opt_in() -> None:
    text = (ROOT / "docker" / "install-comfy" / "phase-nodes.sh").read_text(encoding="utf-8")
    assert "LAB_ENABLE_LTX_DIRECTOR" in text
    assert "WhatDreamsCost-ComfyUI" in text
    assert "MiniMaxH3-Director" not in text
    assert "jtydhr88/ComfyUI-OpenCut" in text
    assert "WhatDreamsCost-ComfyUI" in text


def test_compose_studio_ui_is_optional_no_gpu() -> None:
    text = (ROOT / "docker" / "docker-compose.yml").read_text(encoding="utf-8")
    assert "profiles: [\"studio-ui\"]" in text or "profiles: ['studio-ui']" in text
    assert "ez-comfy-studio-ui" in text
    assert "mem_limit: 512m" in text
    assert "8190" in text
    studio = text.split("studio-ui:")[1].split("volumes:")[0]
    assert "gpus:" not in studio
    assert 'restart: "no"' in studio
    assert "postgres" not in text.lower()
    assert "redis" not in text.lower()


def test_no_wav2lip_in_tree() -> None:
    hits: list[str] = []
    for path in (ROOT / "workflows").rglob("*"):
        if path.suffix.lower() in {".json", ".md", ".yaml"}:
            blob = path.read_text(encoding="utf-8", errors="ignore")
            if "Wav2Lip" in blob or "wav2lip" in blob:
                hits.append(str(path.relative_to(ROOT)))
    for path in (ROOT / "custom_nodes").rglob("*.py"):
        if "Wav2Lip" in path.read_text(encoding="utf-8", errors="ignore"):
            hits.append(str(path.relative_to(ROOT)))
    assert hits == [], hits


def test_film_graphs_carry_ltx_disclosure() -> None:
    for name in (
        "film-go-see-90s-run-lab-example.json",
        "film-still-here-90s-lab-example.json",
        "film-switchyard-90s-lab-example.json",
    ):
        extra = json.loads((ROOT / "workflows" / "shorts" / name).read_text(encoding="utf-8"))["extra"]
        assert "LTX Community License" in extra["lab_disclosure"]


def test_studio_ui_empty_state(tmp_path: Path, monkeypatch: object) -> None:
    import sys

    sys.path.insert(0, str(ROOT / "studio-ui"))
    import server as studio_server  # type: ignore[import-not-found]

    monkeypatch.setattr(studio_server, "FILMS", tmp_path / "missing")
    html = studio_server._page().decode("utf-8")
    assert "No films yet" in html
    dest = tmp_path / "gosee"
    dest.mkdir()
    (dest / "state.json").write_text(
        json.dumps({"film": "go-see", "slug": "gosee", "shots": [{"status": "ok"}, {"status": "pending"}]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(studio_server, "FILMS", tmp_path)
    html = studio_server._page().decode("utf-8")
    assert "gosee" in html
    assert "1/2" in html
