"""Build no-UNET inspire Apps: Prompt Forge, Beat Sheet, Research Chat.

Not imported by pytest (leading underscore). Run from repo root:

  python3 tests/python/_build_inspire_apps.py
"""

from __future__ import annotations

import json
from pathlib import Path

from _lab_layout import (
    GROUP_TITLE_INSET,
    LAB_GROUP_Y0,
    LAB_NODE_Y0,
    finalize_layout,
    group as _group,
)
from _lab_theme import LAZY_FORGE
from _lab_paths import apply_lab_identity, lab_dest, lab_json, lab_rel_of
from _stamp_app_mode import stamp_suite_graph
from _wire_prompt_enhance import enable_lab_graph

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "workflows"

LAZY = LAZY_FORGE

FORGE_NOTE = """## inspire/prompt-forge

Prompt Forge — rewrite a lazy sentence for every US-safe CLIP family. No UNET, no VAE, no KSampler.

Occupancy: llm — graph label (not a CLI mode). Prefer GPU 35B:

  ./scripts/manage.sh occupancy enter llm-desk --yes

Falls back to on-box Qwen3-4B if the sidecar is down. CPU 4B is required next to Wan/LTX/TRELLIS.

1. Type a lazy sentence once in **Prompt** (or leave the canned line).
2. Optional **Context**: paste a research brief or bible. Empty is fine.
3. Set family mode (t2i / i2v / t2v / s2v / iclora / vc), style, and aspect / duration hint on each enhance node.
4. Queue. Each Enhance node previews the rewritten STRING. Klein, Wan, LTX, Z-Image, LongCat, and DreamX read the same Prompt and Context.
5. Copy the family you need into **stills/still-draft** (Spark Still) or an opt-in graph.

Turn Enhance off to pin the widget text. Context is ignored when Enhance is off.
Z-Image Turbo ignores a separate negative — exclusions stay in the positive.
Wan S2V: wav owns lip-sync. DreamX: first frame owns look; paragraph is AV.
"""

BEAT_NOTE = """## inspire/beat-sheet

Script desk — 6 beats × enter / traverse / exit. Occupancy: none — stop nothing GPU.

This graph does not print video. Fill Logline, Script, Audio policy, Score — those desk
fields are packed into Context Join and condition every card rewrite. Then fill the 18 cards
(`action | camera | world SFX | dialogue`). Audio policy also feeds LTX audio notes.
Write YAML on the host:

  ./scripts/manage.sh shot-sheet run --film <slug>

That writes `${COMFY_OUTPUT_DIR}/films/<slug>/shots.yaml`. The entrypoint does **not**
copy YAML. Do not overwrite `workflows/shorts/*.shots.yaml` unless `--lab-example`.

Next: stills/identity-sheet, or export-guides if clay is required, then
dcc/clay-hero.

Shot-card keys (defaults fail-closed):

  audio_policy: world-only | stems | a2v-lock
  score: none | acestep-instrumental
  clay: skip | required
  audio_lock: none | a2v
  camera: dolly in | tracking | fixed camera | …

Shot 1 of beat 1 load_from: identity. Later shots load_from: <prev_prefix>_last.

Do not type a 30/60/90 s denoise. One LTX print is 5.00 s (121 frames = 1+8n @ 24 fps).
"""

RESEARCH_NOTE = """## inspire/research-chat

Creative research desk — chat LLM with web search and sequential research
subagents. No UNET, no VAE, no KSampler.

Occupancy: llm — graph label (not a CLI mode). Prefer GPU 35B:

  ./scripts/manage.sh occupancy enter llm-desk --yes

Falls back to on-box Qwen3-4B if the sidecar is down. CPU 4B is required next to Wan/LTX/TRELLIS.
Web search is SSRF-safe HTTPS (Wikipedia + DuckDuckGo HTML). Fail-soft if the
network or GGUF is missing.

1. Type a question (look, camera, lighting, world, reference).
2. Mode **research** (planner + search subagents) or **chat** (one turn).
3. Queue. Read **Reply** and **Sources**. Copy prompt ingredients into
   **inspire/prompt-forge**, then **stills/still-draft**.

Laptop agents: `./scripts/manage.sh research-mcp --stdio` (Path D). Same
pipeline as this App. Does not queue Comfy. Does not refuse a GPU session.
"""

APP_FORGE_NOTE = """## inspire/app-forge

App Forge — clone a shipped lab graph into live `_user/` as a new App.
No UNET, no VAE, no KSampler. Does not Queue the result.

Occupancy: llm — graph label (not a CLI mode). Prefer GPU 35B:

  ./scripts/manage.sh occupancy enter llm-desk --yes

Falls back to on-box Qwen3-4B if the sidecar is down, then a keyword
heuristic if the GGUF is missing. CPU 4B is required next to Wan/LTX/TRELLIS.

1. Type a **Brief** (or pick a sample). Leave **Template** on auto, or pin
   a lab id such as stills/instagram-square.
2. Set **Slug** (lowercase, hyphen). **As app** on writes `*.app.json`.
3. Queue. Read **Path**, **Picked template**, and **Result occupancy**.
4. Open `_user/<slug>` from the Apps sidebar. Queue that graph when GB10
   occupancy matches the result (klein / wan / ltx / …).

Laptop agents: `./scripts/manage.sh studio-mcp --stdio` (Path D). Same
pipeline as this App. Does not queue Comfy. Does not refuse a GPU session.
Does not write `workflows/_lab/`. Keepers: `promote-workflow`.
"""

CINEMA_NOTE = """## inspire/cinema-rack

Cinema Rack — pick one cinematography technique per axis and splice a Klein / Wan / LTX prompt. No UNET, no VAE, no KSampler.

Occupancy: llm — graph label (not a CLI mode). Prefer GPU 35B:

  ./scripts/manage.sh occupancy enter llm-desk --yes

Falls back to on-box Qwen3-4B if the sidecar is down. CPU 4B is required next to Wan/LTX/TRELLIS.

1. Type a **Subject** (who/what). Leave empty to splice techniques only.
2. Optional **Recipe** fills empty axes. Explicit dropdowns win.
3. Pick at most one technique per axis (shot size, angle, move, lens, …).
4. Set **Family** (klein, wan_t2v, ltx_t2v, or the i2v / identity flavors).
5. Queue. Each Enhance node previews the rewritten STRING. Style stays **none** so cinema clauses are not stripped.
6. Copy the family you need into **stills/still-draft** or an I2V graph.

Wan emits **one** camera verb. I2V drops look axes (start image owns grade). Editing is omitted on stills.
Cinema Rack is deterministic (no LLM). Enhance is optional downstream.
"""

AUDIO_NOTE = """## inspire/audio-rack

Audio Rack — pick one audio/music technique per axis and splice ACE-Step tags and lyrics form. No UNET, no VAE, no KSampler.

Occupancy: llm — graph label (not a CLI mode). Prefer GPU 35B:

  ./scripts/manage.sh occupancy enter llm-desk --yes

Falls back to on-box Qwen3-4B if the sidecar is down. CPU 4B is required next to Wan/LTX/TRELLIS.

Do **not** load ACE-Step on this canvas. Copy tags/lyrics into audio/music/rap-draft or a podcast bed.

1. Optional **Brief** (what the track is about). Ignored on instrumental / podcast-bed.
2. Optional **Recipe** fills empty axes. Explicit dropdowns win.
3. Pick at most one technique per axis (genre, tempo, drums, bass, …).
4. Set **Family** (ace_vocal, ace_instrumental, or podcast_bed).
5. Queue. Vocal / instrumental Enhance nodes preview rewritten tags and lyrics.
6. Copy tags into **audio/music/rap-draft**. Match encoder BPM to the notes line.

Instrumental forces no-vocals tags and [inst] / [drop] form. ACE sings any free-text under a section marker.
Audio Rack is deterministic (no LLM). Enhance is optional downstream.
"""

RESEARCH_MESSAGE = (
    "What lighting and camera language fits a night rooftop still of a techno "
    "wizard in a tropical city?"
)

APP_FORGE_BRIEF = (
    "1:1 IG still of a chipped cobalt mug on pale stone, unmarked surfaces."
)

SHOT_ROLES = ("enter", "traverse", "exit")


def _assert_no_overlap(graph: dict, pad: float = 20) -> None:
    del pad
    finalize_layout(graph)


def _dump(path: Path, graph: dict) -> None:
    apply_lab_identity(graph, lab_rel_of(path))
    enable_lab_graph(graph)
    stamp_suite_graph(graph)
    finalize_layout(graph)
    path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")


def _node(
    nid: int,
    ntype: str,
    pos: list[float],
    size: list[float],
    title: str,
    widgets: list,
    order: int,
    outputs: list | None = None,
) -> dict:
    return {
        "id": nid,
        "type": ntype,
        "pos": pos,
        "size": size,
        "flags": {},
        "order": order,
        "mode": 0,
        "inputs": [],
        "outputs": outputs or [],
        "properties": {"Node name for S&R": ntype},
        "widgets_values": widgets,
        "title": title,
    }


def _str_out(name: str = "prompt") -> list[dict]:
    return [{"name": name, "type": "STRING", "links": [], "slot_index": 0}]


def _prim_out(links: list[int] | None = None) -> list[dict]:
    return [
        {
            "name": "STRING",
            "type": "STRING",
            "links": links if links is not None else [],
            "widget": {"name": "value"},
            "slot_index": 0,
        }
    ]


def _linked_named(name: str, lid: int) -> dict:
    return {
        "name": name,
        "type": "STRING",
        "link": lid,
        "widget": {"name": name},
    }


def _linked_prompt(lid: int) -> dict:
    return {
        "name": "prompt",
        "type": "STRING",
        "link": lid,
        "widget": {"name": "prompt"},
    }


def _linked_context(lid: int) -> dict:
    return {"name": "context", "type": "STRING", "link": lid}


def build_prompt_forge() -> dict:
    note_h = 360.0
    note_group_h = note_h + GROUP_TITLE_INSET
    desk_h = 200.0
    row1_h = 380.0
    desk_group_top = LAB_GROUP_Y0 + note_group_h
    desk_y = desk_group_top + GROUP_TITLE_INSET
    enh_group_top = desk_group_top + desk_h + GROUP_TITLE_INSET + 20.0
    enh_y = enh_group_top + GROUP_TITLE_INSET
    row2_group_top = enh_group_top + row1_h + GROUP_TITLE_INSET + 20.0
    row2_y = row2_group_top + GROUP_TITLE_INSET
    prompt_links = [1, 2, 3, 7, 8, 9]
    ctx_links = [4, 5, 6, 10, 11, 12]
    cat = "inspire/prompt-forge"
    note = _node(
        1,
        "Note",
        [40, LAB_NODE_Y0],
        [1340, note_h],
        "Operator note",
        [FORGE_NOTE],
        0,
    )
    prompt = _node(
        5,
        "EZSamplePrompt",
        [40, desk_y],
        [420, desk_h],
        "Prompt",
        ["custom", LAZY, cat],
        1,
        _str_out("prompt"),
    )
    prompt["outputs"][0]["links"] = prompt_links
    context = _node(
        6,
        "PrimitiveNode",
        [500, desk_y],
        [420, desk_h],
        "Context",
        ["", "fixed"],
        2,
        _prim_out(ctx_links),
    )
    klein = _node(
        2,
        "EZKleinPromptEnhance",
        [40, enh_y],
        [420, 300],
        "Klein family",
        ["custom", LAZY, True, "t2i", "YouTube 16:9 still", "none", cat],
        3,
        _str_out(),
    )
    klein["inputs"] = [_linked_prompt(1), _linked_context(4)]
    wan = _node(
        3,
        "EZWanPromptEnhance",
        [500, enh_y],
        [420, 300],
        "Wan family",
        ["custom", LAZY, True, "i2v", "5 seconds, 24 fps", "none", cat],
        4,
        _str_out(),
    )
    wan["inputs"] = [_linked_prompt(2), _linked_context(5)]
    ltx = _node(
        4,
        "EZLTXPromptEnhance",
        [960, enh_y],
        [420, 380],
        "LTX family",
        ["custom", LAZY, True, "i2v", "5 seconds, 24 fps", "rooftop wind, no score", "none", cat],
        5,
        _str_out(),
    )
    ltx["inputs"] = [_linked_prompt(3), _linked_context(6)]
    zimage = _node(
        7,
        "EZZimagePromptEnhance",
        [40, row2_y],
        [420, 280],
        "Z-Image family",
        ["custom", LAZY, True, "YouTube 16:9 still", "none", cat],
        6,
        _str_out(),
    )
    zimage["inputs"] = [_linked_prompt(7), _linked_context(10)]
    longcat = _node(
        8,
        "EZLongCatPromptEnhance",
        [500, row2_y],
        [420, 300],
        "LongCat family",
        ["custom", LAZY, True, "t2v", "5 seconds, 30 fps", "none", cat],
        7,
        _str_out(),
    )
    longcat["inputs"] = [_linked_prompt(8), _linked_context(11)]
    dreamx = _node(
        9,
        "EZDreamXPromptEnhance",
        [960, row2_y],
        [420, 380],
        "DreamX family",
        ["custom", LAZY, True, "5 seconds, 24 fps", "world SFX, no score", "none", cat],
        8,
        _str_out(),
    )
    dreamx["inputs"] = [_linked_prompt(9), _linked_context(12)]
    links = [
        [1, 5, 0, 2, 0, "STRING"],
        [2, 5, 0, 3, 0, "STRING"],
        [3, 5, 0, 4, 0, "STRING"],
        [4, 6, 0, 2, 1, "STRING"],
        [5, 6, 0, 3, 1, "STRING"],
        [6, 6, 0, 4, 1, "STRING"],
        [7, 5, 0, 7, 0, "STRING"],
        [8, 5, 0, 8, 0, "STRING"],
        [9, 5, 0, 9, 0, "STRING"],
        [10, 6, 0, 7, 1, "STRING"],
        [11, 6, 0, 8, 1, "STRING"],
        [12, 6, 0, 9, 1, "STRING"],
    ]
    graph = {
        "id": "inspire/prompt-forge",
        "revision": 1,
        "last_node_id": 9,
        "last_link_id": 12,
        "nodes": [note, prompt, context, klein, wan, ltx, zimage, longcat, dreamx],
        "links": links,
        "groups": [
            _group(1, "NOTE", 20, LAB_GROUP_Y0, 1380, note_group_h, "#3f789e"),
            _group(
                2,
                "DESK",
                20,
                desk_group_top,
                1380,
                desk_h + GROUP_TITLE_INSET,
                "#3f789e",
            ),
            _group(3, "KLEIN", 20, enh_group_top, 460, 300 + GROUP_TITLE_INSET, "#3f789e"),
            _group(4, "WAN", 480, enh_group_top, 460, 300 + GROUP_TITLE_INSET, "#3f789e"),
            _group(5, "LTX", 940, enh_group_top, 460, 380 + GROUP_TITLE_INSET, "#3f789e"),
            _group(6, "Z-IMAGE", 20, row2_group_top, 460, 280 + GROUP_TITLE_INSET, "#3f789e"),
            _group(7, "LONGCAT", 480, row2_group_top, 460, 300 + GROUP_TITLE_INSET, "#3f789e"),
            _group(8, "DREAMX", 940, row2_group_top, 460, 380 + GROUP_TITLE_INSET, "#3f789e"),
        ],
        "config": {},
        "extra": {
            "lab_profile": "inspire/prompt-forge",
            "lab_note": FORGE_NOTE,
            "lab_description": (
                "No-UNET Prompt Forge: shared prompt + Klein / Wan / LTX / "
                "Z-Image / LongCat / DreamX enhance preview"
            ),
            "ds": {"scale": 1, "offset": [0, 0]},
        },
        "version": 0.4,
    }
    return graph


def build_beat_sheet() -> dict:
    note_h = 460.0
    card_w, card_h = 420.0, 160.0
    desk_h = 200.0
    enh_h = 280.0
    gap = 40.0
    desk_y = LAB_NODE_Y0 + note_h + GROUP_TITLE_INSET + 20.0
    join_h = 160.0
    join_y = desk_y + desk_h + 48.0
    row_stride = card_h + enh_h + GROUP_TITLE_INSET + gap + 50.0
    cards_y0 = join_y + join_h + GROUP_TITLE_INSET + 20.0
    nodes = [
        _node(
            1,
            "Note",
            [40, LAB_NODE_Y0],
            [1340, note_h],
            "Operator note",
            [BEAT_NOTE],
            0,
        )
    ]
    groups = [
        _group(
            1,
            "NOTE",
            20,
            LAB_GROUP_Y0,
            1380,
            note_h + GROUP_TITLE_INSET,
            "#3f789e",
        ),
        _group(
            2,
            "DESK",
            20,
            desk_y - GROUP_TITLE_INSET,
            1380,
            desk_h + 48.0 + join_h + GROUP_TITLE_INSET,
            "#3f789e",
        ),
    ]
    nid = 2
    desk_cards = (
        ("Logline", "One-line premise. Approve before any UNET."),
        ("Script", "Spoken and visual beats. Words are cheap; prints are not."),
        ("Audio policy", "world-only"),
        ("Score", "none"),
    )
    for col, (title, placeholder) in enumerate(desk_cards):
        x = 40 + col * (card_w + gap)
        if title == "Logline":
            nodes.append(
                _node(
                    nid,
                    "EZSamplePrompt",
                    [x, desk_y],
                    [card_w, desk_h],
                    title,
                    ["custom", placeholder, "inspire/beat-sheet"],
                    nid - 1,
                    _str_out("prompt"),
                )
            )
        else:
            nodes.append(
                _node(
                    nid,
                    "PrimitiveNode",
                    [x, desk_y],
                    [card_w, desk_h],
                    title,
                    [placeholder, "fixed"],
                    nid - 1,
                    [
                        {
                            "name": "STRING",
                            "type": "STRING",
                            "links": None,
                            "widget": {"name": "value"},
                            "slot_index": 0,
                        }
                    ],
                )
            )
        nid += 1
    links: list[list] = []
    lid = 1
    join_id = nid
    logline_lid, script_lid, policy_lid, score_lid = lid, lid + 1, lid + 2, lid + 3
    lid = score_lid + 1
    nodes.append(
        _node(
            join_id,
            "EZContextJoin",
            [40.0, join_y],
            [card_w, join_h],
            "Desk context",
            ["Logline", "Script", "Audio policy", "Score"],
            join_id - 1,
            _str_out("context"),
        )
    )
    nodes[-1]["inputs"] = [
        {"name": "a", "type": "STRING", "link": logline_lid},
        {"name": "b", "type": "STRING", "link": script_lid},
        {"name": "c", "type": "STRING", "link": policy_lid},
        {"name": "d", "type": "STRING", "link": score_lid},
    ]
    for src_id, src_lid in ((2, logline_lid), (3, script_lid), (4, policy_lid), (5, score_lid)):
        src = next(n for n in nodes if n["id"] == src_id)
        src["outputs"][0]["links"] = [src_lid]
        dest_slot = src_id - 2
        links.append([src_lid, src_id, 0, join_id, dest_slot, "STRING"])
    nid += 1
    join_ctx_links: list[int] = []
    policy_audio_links: list[int] = []
    for beat in range(1, 7):
        row_y = cards_y0 + (beat - 1) * row_stride
        group_top = row_y - GROUP_TITLE_INSET
        groups.append(
            _group(
                beat + 2,
                f"BEAT {beat}",
                20,
                group_top,
                1380,
                card_h + enh_h + 70 + GROUP_TITLE_INSET,
                "#3f789e",
            )
        )
        for col, role in enumerate(SHOT_ROLES):
            x = 40 + col * (card_w + gap)
            title = f"Beat {beat} {role}"
            placeholder = (
                f"{role} beat {beat} — action | camera | world SFX | dialogue"
            )
            prim_id = nid
            nodes.append(
                _node(
                    prim_id,
                    "PrimitiveNode",
                    [x, row_y],
                    [card_w, card_h],
                    title,
                    [placeholder, "fixed"],
                    nid - 1,
                    [
                        {
                            "name": "STRING",
                            "type": "STRING",
                            "links": [lid],
                            "widget": {"name": "value"},
                            "slot_index": 0,
                        }
                    ],
                )
            )
            nid += 1
            enh_id = nid
            nodes.append(
                _node(
                    enh_id,
                    "EZLTXPromptEnhance",
                    [x, row_y + card_h + 50],
                    [card_w, enh_h],
                    f"{title} LTX enhance",
                    [placeholder, True, "i2v", "5 seconds, 24 fps", "", "none"],
                    nid - 1,
                    _str_out(),
                )
            )
            ctx_lid = lid + 1
            audio_lid = lid + 2
            nodes[-1]["inputs"] = [
                {
                    "name": "prompt",
                    "type": "STRING",
                    "link": lid,
                    "widget": {"name": "prompt"},
                },
                _linked_context(ctx_lid),
                {
                    "name": "audio_notes",
                    "type": "STRING",
                    "link": audio_lid,
                    "widget": {"name": "audio_notes"},
                },
            ]
            links.append([lid, prim_id, 0, enh_id, 0, "STRING"])
            links.append([ctx_lid, join_id, 0, enh_id, 1, "STRING"])
            links.append([audio_lid, 4, 0, enh_id, 2, "STRING"])
            join_ctx_links.append(ctx_lid)
            policy_audio_links.append(audio_lid)
            lid += 3
            nid += 1
    join_node = next(n for n in nodes if n["id"] == join_id)
    join_node["outputs"][0]["links"] = join_ctx_links
    policy = next(n for n in nodes if n["id"] == 4)
    policy["outputs"][0]["links"] = [policy_lid, *policy_audio_links]
    graph = {
        "id": "inspire/beat-sheet",
        "revision": 1,
        "last_node_id": nid - 1,
        "last_link_id": lid - 1,
        "nodes": nodes,
        "links": links,
        "groups": groups,
        "config": {},
        "extra": {
            "lab_profile": "inspire/beat-sheet",
            "lab_note": BEAT_NOTE,
            "lab_description": "Script desk: logline, audio policy, 18 shot cards → shot-sheet YAML",
            "ds": {"scale": 1, "offset": [0, 0]},
        },
        "version": 0.4,
    }
    return graph


def build_research_chat() -> dict:
    note_h = 340.0
    note_group_h = note_h + GROUP_TITLE_INSET
    desk_group_top = LAB_GROUP_Y0 + note_group_h
    desk_y = desk_group_top + GROUP_TITLE_INSET
    desk_h = 420.0
    note = _node(
        1,
        "Note",
        [40, LAB_NODE_Y0],
        [720, note_h],
        "Operator note",
        [RESEARCH_NOTE],
        0,
    )
    desk = _node(
        2,
        "EZCreativeResearch",
        [40, desk_y],
        [720, desk_h],
        "Creative research",
        ["custom", RESEARCH_MESSAGE, "research", True, 2, "", "inspire/research-chat"],
        1,
        [{"name": "reply", "type": "STRING", "links": None, "slot_index": 0}],
    )
    graph = {
        "id": "inspire/research-chat",
        "revision": 1,
        "last_node_id": 2,
        "last_link_id": 0,
        "nodes": [note, desk],
        "links": [],
        "groups": [
            _group(1, "NOTE", 20, LAB_GROUP_Y0, 760, note_group_h, "#3f789e"),
            _group(
                2,
                "RESEARCH",
                20,
                desk_group_top,
                760,
                desk_h + GROUP_TITLE_INSET,
                "#3f789e",
            ),
        ],
        "config": {},
        "extra": {
            "lab_profile": "inspire/research-chat",
            "lab_note": RESEARCH_NOTE,
            "lab_description": (
                "No-UNET creative research chat: web search + sequential subagents"
            ),
            "lab_mcp": {
                "server": "research-mcp",
                "tools": ["chat", "web_search", "research"],
                "workflow": (
                    "workflows/_lab/inspire/research-chat.json"
                ),
            },
            "ds": {"scale": 1, "offset": [0, 0]},
        },
        "version": 0.4,
    }
    return graph


def build_app_forge() -> dict:
    note_h = 380.0
    note_group_h = note_h + GROUP_TITLE_INSET
    desk_group_top = LAB_GROUP_Y0 + note_group_h
    desk_y = desk_group_top + GROUP_TITLE_INSET
    desk_h = 460.0
    note = _node(
        1,
        "Note",
        [40, LAB_NODE_Y0],
        [720, note_h],
        "Operator note",
        [APP_FORGE_NOTE],
        0,
    )
    desk = _node(
        2,
        "EZAppForge",
        [40, desk_y],
        [720, desk_h],
        "App Forge",
        ["custom", APP_FORGE_BRIEF, "auto", "mug-ig", True, False, "inspire/app-forge"],
        1,
        [{"name": "path", "type": "STRING", "links": None, "slot_index": 0}],
    )
    graph = {
        "id": "inspire/app-forge",
        "revision": 1,
        "last_node_id": 2,
        "last_link_id": 0,
        "nodes": [note, desk],
        "links": [],
        "groups": [
            _group(1, "NOTE", 20, LAB_GROUP_Y0, 760, note_group_h, "#3f789e"),
            _group(
                2,
                "FORGE",
                20,
                desk_group_top,
                760,
                desk_h + GROUP_TITLE_INSET,
                "#3f789e",
            ),
        ],
        "config": {},
        "extra": {
            "lab_profile": "inspire/app-forge",
            "lab_note": APP_FORGE_NOTE,
            "lab_description": (
                "No-UNET App Forge: clone a lab graph into live _user/"
            ),
            "lab_mcp": {
                "server": "studio-mcp",
                "tools": [
                    "search_templates",
                    "get_template",
                    "apply_slots",
                    "validate_workflow",
                    "save_workflow",
                    "create_app",
                    "generate_app",
                ],
                "workflow": "workflows/_lab/inspire/app-forge.json",
            },
            "ds": {"scale": 1, "offset": [0, 0]},
        },
        "version": 0.4,
    }
    return graph


def build_cinema_rack() -> dict:
    note_h = 360.0
    note_group_h = note_h + GROUP_TITLE_INSET
    rack_h = 420.0
    desk_group_top = LAB_GROUP_Y0 + note_group_h
    desk_y = desk_group_top + GROUP_TITLE_INSET
    enh_group_top = desk_group_top + rack_h + GROUP_TITLE_INSET + 20.0
    enh_y = enh_group_top + GROUP_TITLE_INSET
    prompt_links = [1, 2, 3]
    none = "none"
    axis_nones = [none] * 13
    note = _node(
        1,
        "Note",
        [40, LAB_NODE_Y0],
        [1340, note_h],
        "Operator note",
        [CINEMA_NOTE],
        0,
    )
    rack = _node(
        5,
        "EZCinemaRack",
        [40, desk_y],
        [1340, rack_h],
        "Cinema Rack",
        ["A techno wizard on a sunny tropical city rooftop.", "klein", none, *axis_nones],
        1,
        [
            {"name": "prompt", "type": "STRING", "links": prompt_links, "slot_index": 0},
            {"name": "notes", "type": "STRING", "links": [], "slot_index": 1},
        ],
    )
    klein = _node(
        2,
        "EZKleinPromptEnhance",
        [40, enh_y],
        [420, 300],
        "Klein family",
        ["custom", LAZY, True, "t2i", "YouTube 16:9 still", "none", "inspire/cinema-rack"],
        2,
        _str_out(),
    )
    klein["inputs"] = [_linked_prompt(1)]
    wan = _node(
        3,
        "EZWanPromptEnhance",
        [500, enh_y],
        [420, 300],
        "Wan family",
        ["custom", LAZY, True, "t2v", "5 seconds, 24 fps", "none", "inspire/cinema-rack"],
        3,
        _str_out(),
    )
    wan["inputs"] = [_linked_prompt(2)]
    ltx = _node(
        4,
        "EZLTXPromptEnhance",
        [960, enh_y],
        [420, 380],
        "LTX family",
        [
            "custom",
            LAZY,
            True,
            "t2v",
            "5 seconds, 24 fps",
            "world SFX, no score",
            "none",
            "inspire/cinema-rack",
        ],
        4,
        _str_out(),
    )
    ltx["inputs"] = [_linked_prompt(3)]
    links = [
        [1, 5, 0, 2, 0, "STRING"],
        [2, 5, 0, 3, 0, "STRING"],
        [3, 5, 0, 4, 0, "STRING"],
    ]
    graph = {
        "id": "inspire/cinema-rack",
        "revision": 1,
        "last_node_id": 5,
        "last_link_id": 3,
        "nodes": [note, rack, klein, wan, ltx],
        "links": links,
        "groups": [
            _group(1, "NOTE", 20, LAB_GROUP_Y0, 1380, note_group_h, "#3f789e"),
            _group(
                2,
                "RACK",
                20,
                desk_group_top,
                1380,
                rack_h + GROUP_TITLE_INSET,
                "#3f789e",
            ),
            _group(3, "KLEIN", 20, enh_group_top, 460, 300 + GROUP_TITLE_INSET, "#3f789e"),
            _group(4, "WAN", 480, enh_group_top, 460, 300 + GROUP_TITLE_INSET, "#3f789e"),
            _group(5, "LTX", 940, enh_group_top, 460, 380 + GROUP_TITLE_INSET, "#3f789e"),
        ],
        "config": {},
        "extra": {
            "lab_profile": "inspire/cinema-rack",
            "lab_note": CINEMA_NOTE,
            "lab_description": (
                "No-UNET Cinema Rack: splice cinematography axes into Klein / Wan / LTX"
            ),
            "ds": {"scale": 1, "offset": [0, 0]},
        },
        "version": 0.4,
    }
    return graph


def build_audio_rack() -> dict:
    note_h = 400.0
    note_group_h = note_h + GROUP_TITLE_INSET
    rack_h = 460.0
    desk_group_top = LAB_GROUP_Y0 + note_group_h
    desk_y = desk_group_top + GROUP_TITLE_INSET
    enh_group_top = desk_group_top + rack_h + GROUP_TITLE_INSET + 20.0
    enh_y = enh_group_top + GROUP_TITLE_INSET
    none = "none"
    axis_nones = [none] * 13
    note = _node(
        1,
        "Note",
        [40, LAB_NODE_Y0],
        [1340, note_h],
        "Operator note",
        [AUDIO_NOTE],
        0,
    )
    rack = _node(
        5,
        "EZAudioRack",
        [40, desk_y],
        [1340, rack_h],
        "Audio Rack",
        ["local booth bars on a dusty pocket", "ace_vocal", none, *axis_nones],
        1,
        [
            {"name": "tags", "type": "STRING", "links": [1, 3], "slot_index": 0},
            {"name": "lyrics", "type": "STRING", "links": [2, 4], "slot_index": 1},
            {"name": "notes", "type": "STRING", "links": [], "slot_index": 2},
        ],
    )
    vocal = _node(
        2,
        "EZAceStepPromptEnhance",
        [40, enh_y],
        [640, 360],
        "Vocal family",
        ["custom", "", "", True, "vocal", "inspire/audio-rack"],
        2,
        [
            {"name": "tags", "type": "STRING", "links": [], "slot_index": 0},
            {"name": "lyrics", "type": "STRING", "links": [], "slot_index": 1},
        ],
    )
    vocal["inputs"] = [_linked_named("tags", 1), _linked_named("lyrics", 2)]
    instrumental = _node(
        3,
        "EZAceStepPromptEnhance",
        [720, enh_y],
        [640, 360],
        "Instrumental family",
        ["custom", "", "", True, "instrumental", "inspire/audio-rack"],
        3,
        [
            {"name": "tags", "type": "STRING", "links": [], "slot_index": 0},
            {"name": "lyrics", "type": "STRING", "links": [], "slot_index": 1},
        ],
    )
    instrumental["inputs"] = [_linked_named("tags", 3), _linked_named("lyrics", 4)]
    links = [
        [1, 5, 0, 2, 0, "STRING"],
        [2, 5, 1, 2, 1, "STRING"],
        [3, 5, 0, 3, 0, "STRING"],
        [4, 5, 1, 3, 1, "STRING"],
    ]
    graph = {
        "id": "inspire/audio-rack",
        "revision": 1,
        "last_node_id": 5,
        "last_link_id": 4,
        "nodes": [note, rack, vocal, instrumental],
        "links": links,
        "groups": [
            _group(1, "NOTE", 20, LAB_GROUP_Y0, 1380, note_group_h, "#3f789e"),
            _group(
                2,
                "RACK",
                20,
                desk_group_top,
                1380,
                rack_h + GROUP_TITLE_INSET,
                "#3f789e",
            ),
            _group(3, "VOCAL", 20, enh_group_top, 680, 360 + GROUP_TITLE_INSET, "#3f789e"),
            _group(
                4, "INST", 720, enh_group_top, 680, 360 + GROUP_TITLE_INSET, "#3f789e"
            ),
        ],
        "config": {},
        "extra": {
            "lab_profile": "inspire/audio-rack",
            "lab_note": AUDIO_NOTE,
            "lab_description": (
                "No-UNET Audio Rack: splice music axes into ACE-Step tags / lyrics"
            ),
            "ds": {"scale": 1, "offset": [0, 0]},
        },
        "version": 0.4,
    }
    return graph


LONGCAT_NOTE = """## optional/longcat-video

Opt-in LongCat-Video (MIT) prompt preview. Not download-models. No UNET on this canvas.

Download: ./scripts/manage.sh download-longcat --tier video
Context-parallel two-Spark only with LAB_ALLOW_CONTEXT_PARALLEL=1. NCCL is out of this sample — tensor-parallel LLMs belong in nvidia-dgx-spark-lab.
Unload LTX first. Occupancy: one heavy job when you Queue a real LongCat printer.

This canvas rewrites a lazy sentence with LongCat Prompt Enhance (T2V / I2V / continuation). Copy the CLIP box into your LongCat graph. Distilled LongCat is CFG 1 (negatives ignored); standard CFG is about 4.

Prompt enhance is on by default (on-box Qwen3-4B-Instruct-2507). Turn Enhance off to pin the widget text.
"""


def build_longcat_stub() -> dict:
    note_h = 360.0
    cat = "optional/longcat-video"
    note = _node(
        1,
        "Note",
        [40, LAB_NODE_Y0],
        [1340, note_h],
        "Operator note",
        [LONGCAT_NOTE],
        0,
    )
    prompt = _node(
        2,
        "EZSamplePrompt",
        [40, LAB_NODE_Y0 + note_h + 40],
        [420, 200],
        "Prompt",
        ["custom", LAZY, cat],
        1,
        _str_out("prompt"),
    )
    prompt["outputs"][0]["links"] = [1]
    enhance = _node(
        3,
        "EZLongCatPromptEnhance",
        [500, LAB_NODE_Y0 + note_h + 40],
        [420, 300],
        "LongCat Prompt Enhance",
        ["custom", LAZY, True, "t2v", "5 seconds, 30 fps", "none", cat],
        2,
        _str_out(),
    )
    enhance["inputs"] = [_linked_prompt(1)]
    neg = _node(
        4,
        "EZNegativePromptEnhance",
        [960, LAB_NODE_Y0 + note_h + 40],
        [420, 280],
        "Negative Prompt Enhance",
        [
            "overexposed, static, subtitles, extra fingers, still picture, watermark",
            True,
            "longcat",
        ],
        3,
        _str_out(),
    )
    neg["inputs"] = [{"name": "positive", "type": "STRING", "link": 2}]
    enhance["outputs"][0]["links"] = [2]
    links = [
        [1, 2, 0, 3, 0, "STRING"],
        [2, 3, 0, 4, 0, "STRING"],
    ]
    graph = {
        "id": "longcat-video",
        "revision": 1,
        "last_node_id": 4,
        "last_link_id": 2,
        "nodes": [note, prompt, enhance, neg],
        "links": links,
        "groups": [],
        "config": {},
        "extra": {
            "lab_note": LONGCAT_NOTE,
            "lab_profile": "optional/longcat-video",
            "lab_description": "LongCat-Video MIT opt-in prompt preview. No NCCL. Not a 90s default.",
            "lab_longcat": {
                "enabled": True,
                "nccl": False,
                "context_parallel": "LAB_ALLOW_CONTEXT_PARALLEL=1",
            },
            "lab_stub": True,
            "lab_rel": "optional/longcat-video",
            "ds": {"scale": 1, "offset": [0, 0]},
        },
        "version": 0.4,
    }
    return graph


def main() -> None:
    _dump(lab_json("inspire/prompt-forge.json"), build_prompt_forge())
    _dump(lab_json("inspire/beat-sheet.json"), build_beat_sheet())
    _dump(lab_dest("inspire/research-chat.json"), build_research_chat())
    _dump(lab_dest("inspire/cinema-rack.json"), build_cinema_rack())
    _dump(lab_dest("inspire/audio-rack.json"), build_audio_rack())
    _dump(lab_dest("inspire/app-forge.json"), build_app_forge())
    _dump(lab_json("optional/longcat-video.json"), build_longcat_stub())


if __name__ == "__main__":
    main()
