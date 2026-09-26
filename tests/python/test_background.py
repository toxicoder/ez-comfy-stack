"""Klein background-swap / background-edit wrap and Enhance modes."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_prompt_enhance.background import (  # noqa: E402
    CROWD_OFF,
    CROWD_ON,
    EDIT_BARE,
    ENTIRE_ENV_VERB,
    OTHER_OFF,
    OTHER_ON,
    REASON_PRECISE_BACKGROUND,
    RECONSTRUCT_BARE,
    SWAP_BARE,
    VOXEL_TRAILER,
    format_background_cast,
    is_background_instruction,
    is_reconstruction,
    parse_background_cast,
    splice_source_caption,
    strengthen_swap_instruction,
    wrap_background_prompt,
)
from ez_prompt_enhance.cinema import addendum_kind  # noqa: E402
from ez_prompt_enhance.client import (  # noqa: E402
    REASON_STYLE_IGNORED_BG_SWAP,
    STYLE_IGNORED_MODES,
)
from ez_prompt_enhance import client  # noqa: E402
from ez_prompt_enhance.nodes import (  # noqa: E402
    EZBackgroundCast,
    EZKleinPromptEnhance,
    KLEIN_MODE_COMBO,
)
from ez_prompt_enhance.samples import load_catalog  # noqa: E402


def test_parse_and_format_background_cast() -> None:
    assert parse_background_cast("") == (True, True)
    assert parse_background_cast(None) == (True, True)
    assert parse_background_cast("other=0,crowd=1") == (False, True)
    assert parse_background_cast("other=false;crowd=no") == (False, False)
    assert parse_background_cast("other_characters=on,background_characters=off") == (
        True,
        False,
    )
    assert parse_background_cast("foo=bar,crowd=0") == (True, False)
    assert parse_background_cast("not-a-token") == (True, True)
    assert format_background_cast() == "other=1,crowd=1"
    assert format_background_cast(
        other_characters=False, background_characters="yes"
    ) == "other=0,crowd=1"
    assert format_background_cast(other_characters=0, background_characters=None) == (
        "other=0,crowd=1"
    )
    assert format_background_cast(other_characters="off", background_characters="no") == (
        "other=0,crowd=0"
    )
    assert format_background_cast(other_characters=object()) == "other=0,crowd=1"


def test_wrap_bare_place_and_passthrough_instructions() -> None:
    wrapped = wrap_background_prompt("fog harbor pier", "background_swap")
    assert wrapped.startswith(
        SWAP_BARE.format(place="fog harbor pier")
    )
    assert OTHER_ON in wrapped
    assert CROWD_ON in wrapped
    edit = wrap_background_prompt("cel-shaded ink alley", "background_edit", "other=0,crowd=0")
    assert edit.startswith(EDIT_BARE.format(place="cel-shaded ink alley"))
    assert OTHER_OFF in edit
    assert CROWD_OFF in edit
    targeted = (
        "Keep the subject from the reference. Replace only the background with a "
        "fog harbor pier at blue hour."
    )
    spliced = wrap_background_prompt(targeted, "background_swap", "other=1,crowd=0")
    assert ENTIRE_ENV_VERB in spliced
    assert "fog harbor pier" in spliced
    assert "replace only the background" not in spliced.casefold()
    assert CROWD_OFF in spliced
    already = f"{targeted} {OTHER_ON} {CROWD_ON}"
    locked = wrap_background_prompt(already, "background_swap", "other=0,crowd=0")
    assert ENTIRE_ENV_VERB in locked
    assert OTHER_ON in locked
    assert locked.count(OTHER_ON) == 1
    assert wrap_background_prompt("", "background_swap") == ""
    assert wrap_background_prompt(None, "background_edit") == ""
    assert wrap_background_prompt(42, "background_swap").startswith(
        SWAP_BARE.format(place="42")
    )
    bare_rebuild = RECONSTRUCT_BARE.format(place="voxel cubes")
    assert "with its people removed" in bare_rebuild
    assert "no figures, no humanoid shapes, no silhouettes, no person-shaped blocks" in (
        bare_rebuild
    )
    assert "cube tiles under every sole" not in bare_rebuild
    assert "person-shaped regions" not in bare_rebuild
    cubic = next(
        item
        for item in load_catalog("klein_background_swap")
        if item.id == "voxel-block-world"
    )
    assert not is_background_instruction(cubic.prompt)
    assert is_reconstruction(cubic.prompt)
    assert "with its people removed" in cubic.prompt
    assert "no figures, no humanoid shapes, no silhouettes, no person-shaped blocks" in (
        cubic.prompt
    )
    assert "cube tiles under every sole" not in cubic.prompt
    assert "person-shaped regions" not in cubic.prompt
    cubic_wrap = wrap_background_prompt(cubic.prompt, "background_swap")
    assert cubic_wrap.startswith(cubic.prompt)
    assert VOXEL_TRAILER in cubic_wrap
    assert OTHER_ON not in cubic_wrap
    assert CROWD_ON not in cubic_wrap
    assert "with: Keep the subject" not in cubic_wrap
    assert SWAP_BARE.format(place=cubic.prompt) not in cubic_wrap
    assert RECONSTRUCT_BARE.format(place=cubic.prompt) not in cubic_wrap
    cubes = wrap_background_prompt("voxel cubes", "background_swap")
    assert cubes.startswith(RECONSTRUCT_BARE.format(place="voxel cubes"))
    assert "with its people removed" in cubes
    assert OTHER_ON not in cubes
    assert CROWD_ON not in cubes
    assert "minecraft" not in cubes.casefold()
    branded = wrap_background_prompt("minecraft harbor", "background_swap")
    assert "minecraft" not in branded.casefold()
    assert "mojang" not in wrap_background_prompt("Mojang plaza", "background_swap").casefold()
    assert "cubic" in branded.casefold()
    assert VOXEL_TRAILER in wrap_background_prompt(
        "Keep the subject from the reference. Rebuild this place as a block world.",
        "background_swap",
    )
    already = wrap_background_prompt(
        "Rebuild this photographed place with cubic voxels already named.",
        "background_swap",
    )
    assert already.count("cubic voxels") == 1
    assert strengthen_swap_instruction("") == ""
    assert strengthen_swap_instruction("fog harbor") == "fog harbor"
    assert is_reconstruction("") is False
    assert splice_source_caption("keep subject", "") == "keep subject"
    assert splice_source_caption("", "a dock") == ""
    spliced_cap = splice_source_caption("keep subject", "a red coat on a dock")
    assert spliced_cap.endswith("Source still: a red coat on a dock")
    assert splice_source_caption(spliced_cap, "ignored") == spliced_cap
    assert is_background_instruction(targeted)
    assert is_background_instruction(
        "Edit only the environment as prompted: add lanterns."
    )
    assert is_background_instruction("Replace the entire environment with a meadow.")
    assert not is_background_instruction("fog harbor pier")
    assert is_background_instruction("") is False


def test_klein_background_modes_wrap_when_enhance_is_off() -> None:
    klein = EZKleinPromptEnhance()
    off = klein.run(
        "fog harbor",
        False,
        "background_swap",
        "match the source still",
        background_cast="other=0,crowd=1",
    )
    text = off["result"][0]
    assert "Replace the entire environment" in text
    assert "fog harbor" in text
    assert OTHER_OFF in text
    assert CROWD_ON in text
    styled_swap = klein.run(
        "fog harbor",
        False,
        "background_swap",
        "match the source still",
        "photorealistic",
    )
    assert "Photoreal photograph" not in styled_swap["result"][0]
    styled_edit = klein.run(
        "cel alley",
        False,
        "background_edit",
        "match the source still",
        "photorealistic",
    )
    assert "Photoreal photograph" in styled_edit["result"][0]
    assert "Edit only the environment" in styled_edit["result"][0]


def test_klein_background_modes_wrap_before_enhance() -> None:
    klein = EZKleinPromptEnhance()
    with patch.object(client, "complete", return_value=("rewritten-bg", None)) as mock:
        klein.run(
            "OPEN TERRACE",
            True,
            "background_edit",
            "match the source still",
            "none",
            background_cast="other=1,crowd=0",
        )
    user = mock.call_args[0][1]
    assert "Edit only the environment as prompted: OPEN TERRACE." in user
    assert CROWD_OFF in user
    with patch.object(client, "complete", return_value=("rewritten-swap", None)) as mock:
        klein.run("pier", True, "background_swap", "match the source still", "none")
    system = mock.call_args[0][0]
    assert "background-swap" in system.lower() or "new environment" in system.lower()
    cubic = next(
        item
        for item in load_catalog("klein_background_swap")
        if item.id == "voxel-block-world"
    )
    with patch.object(client, "complete", return_value=("rewritten-cubic", None)) as mock:
        packed = klein.run(
            cubic.prompt,
            True,
            "background_swap",
            "match the source still",
            "none",
            image_desc="wet dock, red coat, unmarked hull",
        )
    mock.assert_not_called()
    text = packed["result"][0]
    assert cubic.prompt in text
    assert "Source still:" not in text
    assert packed["ui"]["passthrough"][0] == REASON_PRECISE_BACKGROUND
    with patch.object(client, "complete", return_value=("rewritten-cubes", None)) as mock:
        bare = klein.run("voxel cubes", True, "background_swap", "match the source still", "none")
    mock.assert_not_called()
    assert bare["result"][0].startswith(RECONSTRUCT_BARE.format(place="voxel cubes"))
    assert bare["ui"]["passthrough"][0] == REASON_PRECISE_BACKGROUND
    with patch.object(client, "complete", return_value=("rewritten-brand", None)) as mock:
        brand = klein.run("minecraft", True, "background_swap", "match the source still", "none")
    mock.assert_not_called()
    assert "minecraft" not in brand["result"][0].casefold()
    off = klein.run(
        cubic.prompt,
        False,
        "background_swap",
        "match the source still",
        image_desc="a red coat on a dock",
    )
    assert off["ui"]["passthrough"][0] == "enhance off"
    assert "Source still:" not in off["result"][0]
    normal_off = klein.run(
        "fog harbor",
        False,
        "background_swap",
        "match the source still",
        image_desc="a red coat on a dock",
    )
    assert normal_off["ui"]["passthrough"][0] == "enhance off"
    assert "Source still: a red coat on a dock" in normal_off["result"][0]
    normal_precise_off = klein.run(
        "Keep the subject from the reference. Replace the entire environment "
        "with a fog harbor.",
        False,
        "background_swap",
        "match the source still",
        image_desc="a red coat on a dock",
    )
    assert "Source still: a red coat on a dock" in normal_precise_off["result"][0]
    edit_cubic = klein.run(
        "cubes over the pier",
        False,
        "background_edit",
        "match the source still",
        image_desc="a red coat on a dock",
    )
    assert "Source still: a red coat on a dock" in edit_cubic["result"][0]


def test_background_cast_node_and_mode_combo() -> None:
    node = EZBackgroundCast()
    assert node.run() == ("other=1,crowd=1",)
    assert node.run(False, True) == ("other=0,crowd=1",)
    types = EZBackgroundCast.INPUT_TYPES()["required"]
    assert types["other_characters"][1]["default"] is True
    assert types["background_characters"][1]["label_off"] == "Off"
    klein = EZKleinPromptEnhance.INPUT_TYPES()
    assert klein["required"]["mode"][0] == KLEIN_MODE_COMBO
    assert "background_cast" in klein["optional"]
    assert STYLE_IGNORED_MODES["background_swap"] == REASON_STYLE_IGNORED_BG_SWAP
    assert "background_edit" not in STYLE_IGNORED_MODES
    swap = client.load_system_prompt("klein_background_swap")
    assert "ground" in swap.lower()
    assert "cast" in swap.lower()
    assert "cinema rack" not in swap.lower()
    swap_l = swap.lower()
    assert "photographed place" in swap_l
    assert "block study" in swap_l
    assert "texel" in swap_l or "texture-pack" in swap_l
    assert "generic cube biome" in swap_l
    assert "no figures, no humanoid shapes, no silhouettes, no person-shaped blocks" in (
        swap_l
    )
    assert "cube tiles under every sole" not in swap_l
    assert "person-shaped regions" not in swap_l
    assert "minecraft" not in swap_l
    edit = client.load_system_prompt("klein_background_edit")
    assert "cartoon" in edit.lower()
    assert "environment" in edit.lower()
    assert addendum_kind("klein_background_swap") == "skip"
    assert addendum_kind("klein_t2i", "background_edit") == "skip"
    assert addendum_kind("klein_background_edit") == "skip"
