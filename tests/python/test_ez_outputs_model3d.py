"""3D mesh rows in the Outputs catalog: listing, filtering, and the input refuse."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ez_outputs.catalog import (
    AUDIO_SUFFIXES,
    IMAGE_SUFFIXES,
    MEDIA_SUFFIXES,
    MODEL3D_SUFFIXES,
    VIDEO_SUFFIXES,
    CatalogError,
    copy_many_to_input,
    copy_to_input,
    delete_output,
    kind_of,
    list_outputs,
    resolve_under,
)
from ez_outputs.routes import CopyPayload, handle_list, handle_to_input

MESH_REASON = "LoadImage"
MEDIA_TAGS = ("img", "video", "audio")


def _body(response: tuple[int, CopyPayload]) -> tuple[int, dict[str, Any]]:
    """Split one route response into its status and a plain body mapping.

    ``CopyPayload`` is ``total=False``, so every key is optional. Widening it
    here names what the test reads instead of pretending the TypedDict requires
    it.

    Args:
        response: The ``(status, payload)`` pair the route returns.

    Returns:
        The status, and the payload as a plain mapping.
    """
    status, payload = response
    return status, dict(payload)


def _touch(path: Path, data: bytes = b"x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _pack_js_path(name: str) -> Path:
    """Return one file from the pack's web directory.

    Args:
        name: File name under ``custom_nodes/ez_outputs/js``.

    Returns:
        Path to that file.
    """
    root = Path(__file__).resolve().parents[2]
    return root / "custom_nodes" / "ez_outputs" / "js" / name


def _js_slice(body: str, start: str, end: str) -> str:
    """Return the source between two markers, in order.

    Args:
        body: Panel frontend source.
        start: Marker the slice opens at.
        end: Marker the slice ends at.

    Returns:
        The text from ``start`` up to the first ``end`` after it.

    Raises:
        AssertionError: when a marker is missing or out of order.
    """
    assert start in body, start
    at = body.index(start)
    after = body.index(end, at)
    assert after > at, (start, end)
    return body[at:after]


def test_kind_of_mesh_suffixes() -> None:
    assert MODEL3D_SUFFIXES == frozenset({".glb", ".gltf"})
    assert MEDIA_SUFFIXES == (
        IMAGE_SUFFIXES | VIDEO_SUFFIXES | AUDIO_SUFFIXES | MODEL3D_SUFFIXES
    )
    assert kind_of(".glb") == "model3d"
    assert kind_of(".GLB") == "model3d"
    assert kind_of(".gltf") == "model3d"
    assert kind_of(".glb1") is None
    assert kind_of(".glb.zip") is None
    assert kind_of("") is None


def test_kind_of_existing_kinds_unchanged() -> None:
    for suffix in sorted(IMAGE_SUFFIXES):
        assert kind_of(suffix) == "image", suffix
    for suffix in sorted(VIDEO_SUFFIXES):
        assert kind_of(suffix) == "video", suffix
    for suffix in sorted(AUDIO_SUFFIXES):
        assert kind_of(suffix) == "audio", suffix
    for suffix in (".json", ".txt", ".obj", ".fbx", ".zip"):
        assert kind_of(suffix) is None, suffix


def test_list_outputs_surfaces_meshes(tmp_path: Path) -> None:
    _touch(tmp_path / "trellis" / "mug_00001_.glb", b"glTF")
    _touch(tmp_path / "rig.gltf", b"glTF-json")
    _touch(tmp_path / "ez_still_draft_00001_.png", b"aa")
    _touch(tmp_path / "clip.mp4", b"bbbb")
    _touch(tmp_path / "song.flac", b"c")
    rows = {row["rel"]: row for row in list_outputs(tmp_path)}
    assert "trellis/mug_00001_.glb" in rows
    assert "rig.gltf" in rows
    mesh = rows["trellis/mug_00001_.glb"]
    assert mesh["kind"] == "model3d"
    assert mesh["name"] == "mug_00001_.glb"
    assert mesh["suffix"] == ".glb"
    assert mesh["parent"] == "trellis"
    assert mesh["size"] == 4
    # The older lanes list beside the meshes exactly as before.
    assert rows["ez_still_draft_00001_.png"]["kind"] == "image"
    assert rows["clip.mp4"]["kind"] == "video"
    assert rows["song.flac"]["kind"] == "audio"


def test_list_outputs_honours_the_mesh_filter(tmp_path: Path) -> None:
    _touch(tmp_path / "mug.glb", b"glTF")
    _touch(tmp_path / "shots" / "handle.gltf", b"glTF")
    _touch(tmp_path / "still.png", b"aa")
    _touch(tmp_path / "clip.mp4", b"bbbb")
    _touch(tmp_path / "song.flac", b"c")
    _touch(tmp_path / "notes.txt", b"nope")
    for hidden in ("input/hidden.glb", "comfy-user/default/hidden.glb", ".cache/x.glb"):
        _touch(tmp_path / hidden, b"glTF")

    meshes = list_outputs(tmp_path, kind="model3d")
    assert sorted(row["rel"] for row in meshes) == ["mug.glb", "shots/handle.gltf"]
    assert {row["kind"] for row in meshes} == {"model3d"}
    # The filter is the same compare it always was, so every other lane answers
    # exactly as it did before meshes existed.
    for wanted in ("image", "video", "audio"):
        assert {row["kind"] for row in list_outputs(tmp_path, kind=wanted)} == {wanted}
    assert [row["rel"] for row in list_outputs(tmp_path, kind="model3d", query="handle")] == [
        "shots/handle.gltf"
    ]
    assert [row["rel"] for row in list_outputs(tmp_path, kind="model3d", limit=1)] == [
        meshes[0]["rel"]
    ]
    status, payload = handle_list({"kind": "model3d"}, root=tmp_path)
    assert status == 200
    assert sorted(row["rel"] for row in payload["items"]) == [
        "mug.glb",
        "shots/handle.gltf",
    ]
    status, payload = handle_list({"kind": "all", "q": ".glb"}, root=tmp_path)
    assert status == 200
    assert [row["rel"] for row in payload["items"]] == ["mug.glb"]


def test_mesh_resolves_and_deletes(tmp_path: Path) -> None:
    root = tmp_path / "out"
    src = root / "trellis" / "mug.glb"
    _touch(src, b"glTF")
    assert resolve_under(root, "trellis/mug.glb") == src.resolve()
    assert delete_output(root, "trellis/mug.glb") == src.resolve()
    assert not src.exists()


def test_copy_to_input_refuses_mesh(tmp_path: Path) -> None:
    root = tmp_path / "out"
    _touch(root / "mug.glb", b"glTF")
    dest_dir = tmp_path / "inputs"
    with pytest.raises(CatalogError, match=MESH_REASON):
        copy_to_input(root, "mug.glb", input_dir=dest_dir)
    assert not (dest_dir / "mug.glb").exists()
    assert not dest_dir.exists() or list(dest_dir.iterdir()) == []


def test_copy_to_input_still_copies_other_lanes(tmp_path: Path) -> None:
    root = tmp_path / "out"
    _touch(root / "still.png", b"aa")
    _touch(root / "clip.mp4", b"bbbb")
    _touch(root / "song.flac", b"c")
    dest_dir = tmp_path / "inputs"
    for rel in ("still.png", "clip.mp4", "song.flac"):
        copied = copy_to_input(root, rel, input_dir=dest_dir)
        assert copied == dest_dir / rel
        assert copied.is_file()


def test_bulk_copy_refuses_only_the_mesh(tmp_path: Path) -> None:
    root = tmp_path / "out"
    _touch(root / "still.png", b"aa")
    _touch(root / "mug.glb", b"glTF")
    dest = tmp_path / "in"
    copied, errors = copy_many_to_input(root, ["still.png", "mug.glb"], input_dir=dest)
    assert [row["name"] for row in copied] == ["still.png"]
    assert [row["rel"] for row in errors] == ["mug.glb"]
    assert MESH_REASON in errors[0]["error"]
    assert (dest / "still.png").is_file()
    assert not (dest / "mug.glb").exists()


def test_handle_to_input_refuses_mesh(tmp_path: Path) -> None:
    root = tmp_path / "out"
    inputs = tmp_path / "in"
    _touch(root / "mug.glb", b"glTF")
    _touch(root / "still.png", b"aa")

    status, single = _body(handle_to_input({"rel": "mug.glb"}, root=root, input_dir=inputs))
    assert status == 400
    assert MESH_REASON in single["error"]

    status, all_mesh = _body(handle_to_input({"rels": ["mug.glb"]}, root=root, input_dir=inputs))
    assert status == 400
    assert MESH_REASON in all_mesh["error"]

    status, mixed = _body(
        handle_to_input({"rels": ["still.png", "mug.glb"]}, root=root, input_dir=inputs)
    )
    assert status == 200
    assert [row["name"] for row in mixed["copied"]] == ["still.png"]
    assert [row["rel"] for row in mixed["errors"]] == ["mug.glb"]
    assert (inputs / "still.png").is_file()
    assert not (inputs / "mug.glb").exists()


def test_outputs_js_renders_mesh_rows_without_a_media_tag() -> None:
    """A mesh row gets a placeholder card, never an img/video/audio element."""
    body = _pack_js_path("ez_outputs.js").read_text(encoding="utf-8")
    assert 'model3d: "3D",' in body
    assert '["model3d", "3D"],' in body
    assert 'storedKind === "model3d"' in body
    card = _js_slice(
        body, 'if (row.kind === "model3d") {', 'if (row.kind === "audio") {'
    )
    assert "ez-out-mesh-ph" in card
    for tag in MEDIA_TAGS:
        assert f'createElement("{tag}")' not in card, tag
    lightbox = _js_slice(
        body,
        'media.className = "ez-out-lightbox-media";',
        '} else if (row.kind === "image") {',
    )
    assert "ez-out-mesh-note" in lightbox
    for tag in MEDIA_TAGS:
        assert f'createElement("{tag}")' not in lightbox, tag


def test_outputs_js_offers_download_instead_of_loadimage_for_meshes() -> None:
    """Mesh rows download; they are never staged for a LoadImage widget."""
    body = _pack_js_path("ez_outputs.js").read_text(encoding="utf-8")
    row_actions = _js_slice(
        body, "const isMesh = row.kind ===", 'makeButton("Delete"'
    )
    assert 'isMesh\n        ? "Download"' in row_actions
    assert "downloadRels([row.rel]);" in row_actions
    assert "copyRels([row.rel]);" in row_actions
    # The lightbox keeps its Download button and drops the staging one.
    assert 'if (row.kind !== "model3d") {' in body
    use_button = _js_slice(body, 'if (row.kind !== "model3d") {', 'makeButton("Delete"')
    assert "copyRels([row.rel]);" in use_button
    assert 'makeButton("Download", "ez-out-btn"' in body
    assert "link.download =" in body


def test_outputs_css_skins_the_mesh_rows() -> None:
    """The placeholder, the lightbox note, and the badge have rules."""
    sheet = _pack_js_path("ez_outputs.css").read_text(encoding="utf-8")
    for selector in (
        ".ez-out-mesh-ph {",
        ".ez-out-mesh-note {",
        ".ez-out-badge-model3d {",
    ):
        assert selector in sheet, selector
