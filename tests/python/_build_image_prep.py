#!/usr/bin/env python3
"""Build the photos-lane image-prep Apps that feed the image-to-3D chain.

Run from repo root:
  python3 tests/python/_build_image_prep.py

Two Apps, both front doors to the 3d lane. ``photos/cutout`` is a light CPU
pre-pass: one ``EZCutout`` (BiRefNet loaded inside the node) on one
``LoadImage``, so the graph carries no loader at all. A UNETLoader here would
make it a two-stack App and ``_lab_families.stack_violations`` fails that.
``photos/multi-view`` is a Klein still desk: one snapped plate is VAEEncoded
once, and four samplers read that same latent through ``ReferenceLatent`` so
the identity holds while only the camera moves.

Every graph here is generated. Never hand-edit the JSON it writes.
"""

from __future__ import annotations

from typing import Any

from _build_trellis_workflow import _in
from _build_trellis_workflow import _node
from _build_trellis_workflow import _out
from _build_trellis_workflow import _Wires
from _lab_layout import finalize_layout
from _lab_paths import lab_dest
from _lab_paths import write_lab_graph
from _stamp_app_mode import apply_lab_completeness_flags
from _stamp_app_mode import ensure_occupancy_note
from _stamp_app_mode import stamp_app_mode
from _wire_prompt_enhance import repair_negative_sources
from _wire_upscale import wire_upscale

# Copied verbatim from the shipped photos graphs (photos/identity-sheet).
UNET = "flux-2-klein-4b-fp8.safetensors"
CLIP_WEIGHT = "qwen_3_4b.safetensors"
CLIP_TYPE = "flux2"
VAE = "flux2-vae.safetensors"

# Distilled Klein ladder: four steps at CFG 1.0, one fixed seed so the four
# views differ by camera only.
SEED = 42
STEPS = 4
CFG = 1.0
SAMPLER = "euler"
SCHEDULER = "simple"
DENOISE = 1.0

# EZCutout sockets, read out of custom_nodes/ez_image/cutout.py: image,
# backdrop, dilate, feather in; image (cut still over the backdrop), matte
# (grey IMAGE, made for SaveImage), and mask (HW MASK) out.
BACKDROP = "white"
DILATE = 6
FEATHER = 4
# The node clamps both edge knobs to 0..32; a cutout feeding a mesh printer
# wants a slightly generous rim so hair and fur survive the matte.
UPSCALE_REF = "@upscale"
DEFAULT_UPSCALE = "none"

MODEL_LINES = (
    "Models: flux-2-klein-4b-fp8.safetensors + qwen_3_4b.safetensors (CLIP type flux2) "
    "+ flux2-vae.safetensors. Apache-2.0."
)

NEGATIVE = (
    "game-engine cutscene, Pixar rounded cartoon, illustration, muddy textures, "
    "melted geometry, duplicate limbs, watermarks, oversharpen halos, muddy blacks"
)

# One camera-free identity bible. The four SHOT cards below add a camera and
# nothing else, which is what keeps costume, material, and silhouette pinned.
IDENTITY = (
    "A photoreal studio still of one original character: a deep-space salvage diver in a "
    "scuffed matte-charcoal EVA suit, one mustard-yellow harness strap, a chipped crimson "
    "helmet stripe, and one unmarked brass-core pendant. Height, build, face, hairstyle, "
    "suit panels, stitching, hardware, scuffing, and every color are fixed. The subject "
    "alone stands centered on a seamless neutral grey cyclorama, full body with clear "
    "space above the helmet, under one soft key light and one fill. Nothing else is in "
    "frame: no second figure, no set dressing, no props beyond the pendant, no lettering."
)

# (slug, title suffix, shot card). ``lock=view`` front-loads the camera line so
# Klein reads a new station in the same world rather than a new subject.
VIEWS: tuple[tuple[str, str, str], ...] = (
    (
        "front",
        "FRONT",
        "Front camera, eye-level, 50mm, subject squared on to the lens. Same identity, "
        "same light, same ground. Camera is the only change.",
    ),
    (
        "side",
        "SIDE",
        "Right side camera, 90 degrees around the subject, 50mm, full profile. Same "
        "identity, same light, same ground. Camera is the only change.",
    ),
    (
        "back",
        "BACK",
        "Rear camera, 180 degrees behind the subject, 50mm, back of the suit to the lens. "
        "Same identity, same light, same ground. Camera is the only change.",
    ),
    (
        "topdown",
        "TOP-DOWN",
        "Overhead camera straight down from above the subject, 35mm, helmet top and "
        "shoulders to the lens. Same identity, same light, same ground. Camera is the "
        "only change.",
    ),
)


def _widget_in(name: str, typ: str) -> dict[str, Any]:
    """One unwired widget-backed input slot, the way the frontend serializes it.

    Args:
        name: Socket name the node class declares.
        typ: Socket type the node class declares.

    Returns:
        An input-slot dict carrying the widget back-reference and no link.
    """
    return {"name": name, "type": typ, "link": None, "widget": {"name": name}}


class _Canvas:
    """Node and link builder that allocates ids, so chrome nodes never collide.

    ``EZQuality`` and ``EZModelCheck`` are appended by
    ``apply_lab_completeness_flags`` after the chain is built; taking ids from
    one counter is what keeps them off an id a chain node already holds.
    """

    def __init__(self) -> None:
        self.nodes: list[dict[str, Any]] = []
        self.wires = _Wires()

    def add(
        self,
        ntype: str,
        *,
        title: str,
        inputs: list[dict[str, Any]] | None = None,
        outputs: list[dict[str, Any]] | None = None,
        widgets: list[Any] | None = None,
        size: tuple[float, float] = (280.0, 90.0),
        pos: tuple[float, float] = (40.0, 440.0),
    ) -> dict[str, Any]:
        """Append one node and return it.

        Args:
            ntype: Comfy class name.
            title: Canvas title, also the App Mode resolver key.
            inputs: Input slot dicts.
            outputs: Output slot dicts.
            widgets: Positional ``widgets_values``.
            size: Canvas size before ``finalize_layout`` refits it.
            pos: Seed position; staging rewrites it.

        Returns:
            The node dict, also appended to ``self.nodes``.
        """
        node = _node(
            len(self.nodes) + 1,
            ntype,
            pos=pos,
            size=size,
            inputs=inputs or [],
            outputs=outputs or [],
            widgets=widgets,
            title=title,
            order=len(self.nodes),
        )
        self.nodes.append(node)
        return node

    def note(self, text: str) -> dict[str, Any]:
        """Append the operator note every lab graph must carry.

        Args:
            text: Note body, opening with ``## photos/<stem>``.

        Returns:
            The ``Note`` node.
        """
        return self.add(
            "Note",
            title="Operator note",
            widgets=[text],
            size=(720.0, 360.0),
            pos=(40.0, 40.0),
        )

    def wire(self, frm: dict[str, Any], fslot: int, to: dict[str, Any], tslot: int, ltype: str) -> int:
        """Link one output slot to one input slot.

        Args:
            frm: Origin node.
            fslot: Origin output index.
            to: Target node.
            tslot: Target input index.
            ltype: Link type, which must match both sockets.

        Returns:
            The new link id.
        """
        return self.wires.wire(frm, fslot, to, tslot, ltype)

    def load_image(self, title: str) -> dict[str, Any]:
        """Append the one source picker these Apps share.

        Args:
            title: Canvas title for the picker.

        Returns:
            The ``LoadImage`` node.
        """
        return self.add(
            "LoadImage",
            title=title,
            outputs=[_out("IMAGE", "IMAGE"), _out("MASK", "MASK", slot=1)],
            widgets=["example.png", "image"],
            size=(320.0, 314.0),
        )

    def klein_stack(self) -> dict[str, dict[str, Any]]:
        """Append the Klein 4B loaders the photos lane pins.

        Returns:
            ``{"unet": ..., "clip": ..., "vae": ...}`` node handles.
        """
        return {
            "unet": self.add(
                "UNETLoader",
                title="Klein 4B distilled FP8",
                outputs=[_out("MODEL", "MODEL")],
                widgets=[UNET, "default"],
                size=(360.0, 82.0),
            ),
            "clip": self.add(
                "CLIPLoader",
                title="Qwen3-4B TE",
                outputs=[_out("CLIP", "CLIP")],
                widgets=[CLIP_WEIGHT, CLIP_TYPE, "default"],
                size=(360.0, 106.0),
            ),
            "vae": self.add(
                "VAELoader",
                title="Flux2 VAE",
                outputs=[_out("VAE", "VAE")],
                widgets=[VAE],
                size=(360.0, 58.0),
            ),
        }

    def reference_plate(
        self, source: dict[str, Any], vae: dict[str, Any]
    ) -> dict[str, dict[str, Any]]:
        """Snap the source still once and encode it into the shared latent.

        Args:
            source: The ``LoadImage`` node.
            vae: The ``VAELoader`` node.

        Returns:
            ``{"snap": ..., "encode": ...}`` node handles.
        """
        snap = self.add(
            "EZSnapImage",
            title="Snap to Klein grid",
            inputs=[_in("image", "IMAGE")],
            outputs=[_out("IMAGE", "IMAGE")],
            size=(240.0, 60.0),
        )
        self.wire(source, 0, snap, 0, "IMAGE")
        encode = self.add(
            "VAEEncode",
            title="Encode snapped source",
            inputs=[_in("pixels", "IMAGE"), _in("vae", "VAE")],
            outputs=[_out("LATENT", "LATENT")],
            size=(240.0, 80.0),
        )
        self.wire(snap, 0, encode, 0, "IMAGE")
        self.wire(vae, 0, encode, 1, "VAE")
        return {"snap": snap, "encode": encode}

    def identity_enhancer(self, rel: str) -> dict[str, Any]:
        """Append the camera-free bible writer every view reads.

        Args:
            rel: ``_lab``-relative id, written into the catalog widget.

        Returns:
            The ``EZKleinPromptEnhance`` node.
        """
        return self.add(
            "EZKleinPromptEnhance",
            title="IDENTITY",
            inputs=[_widget_in("duration_hint", "STRING")],
            outputs=[_out("prompt", "STRING")],
            widgets=["custom", IDENTITY, True, "identity", "match the source still", "none", rel],
            size=(420.0, 420.0),
        )

    def view(
        self,
        *,
        slug: str,
        suffix: str,
        shot: str,
        identity: dict[str, Any],
        clip: dict[str, Any],
        negative: dict[str, Any],
        unet: dict[str, Any],
        encode: dict[str, Any],
        vae: dict[str, Any],
    ) -> dict[str, Any]:
        """Append one view: shot card, positive, reference, sampler, decode, print.

        Args:
            slug: Lowercase view name used in the save prefix.
            suffix: Uppercase view name used in the node titles.
            shot: Camera-only shot card for the ``EZPromptJoin`` widget.
            identity: The identity enhance node feeding every shot card.
            clip: The ``CLIPLoader`` node.
            negative: The shared negative ``CLIPTextEncode`` node.
            unet: The ``UNETLoader`` node.
            encode: The shared ``VAEEncode`` node.
            vae: The ``VAELoader`` node.

        Returns:
            The ``SaveImage`` node for this view.
        """
        join = self.add(
            "EZPromptJoin",
            title=f"SHOT {suffix}",
            inputs=[_in("identity", "STRING")],
            outputs=[_out("prompt", "STRING")],
            widgets=[shot, "", "view"],
            size=(420.0, 180.0),
        )
        self.wire(identity, 0, join, 0, "STRING")
        positive = self.add(
            "CLIPTextEncode",
            title=f"Positive {suffix}",
            inputs=[_in("clip", "CLIP"), _in("text", "STRING")],
            outputs=[_out("CONDITIONING", "CONDITIONING")],
            widgets=[f"{shot} {IDENTITY}"],
            size=(360.0, 140.0),
        )
        self.wire(clip, 0, positive, 0, "CLIP")
        self.wire(join, 0, positive, 1, "STRING")
        reference = self.add(
            "ReferenceLatent",
            title=f"Reference {suffix}",
            inputs=[_in("conditioning", "CONDITIONING"), _in("latent", "LATENT")],
            outputs=[_out("CONDITIONING", "CONDITIONING")],
            size=(280.0, 80.0),
        )
        self.wire(positive, 0, reference, 0, "CONDITIONING")
        self.wire(encode, 0, reference, 1, "LATENT")
        sampler = self.add(
            "KSampler",
            title=f"Sampler {suffix}",
            inputs=[
                _in("model", "MODEL"),
                _in("positive", "CONDITIONING"),
                _in("negative", "CONDITIONING"),
                _in("latent_image", "LATENT"),
            ],
            outputs=[_out("LATENT", "LATENT")],
            widgets=[SEED, "fixed", STEPS, CFG, SAMPLER, SCHEDULER, DENOISE],
            size=(320.0, 262.0),
        )
        self.wire(unet, 0, sampler, 0, "MODEL")
        self.wire(reference, 0, sampler, 1, "CONDITIONING")
        self.wire(negative, 0, sampler, 2, "CONDITIONING")
        self.wire(encode, 0, sampler, 3, "LATENT")
        decode = self.add(
            "VAEDecode",
            title=f"Decode {suffix}",
            inputs=[_in("samples", "LATENT"), _in("vae", "VAE")],
            outputs=[_out("IMAGE", "IMAGE")],
            size=(240.0, 46.0),
        )
        self.wire(sampler, 0, decode, 0, "LATENT")
        self.wire(vae, 0, decode, 1, "VAE")
        save = self.add(
            "SaveImage",
            title=f"Save {suffix}",
            inputs=[_in("images", "IMAGE")],
            widgets=[f"ez_multiview_{slug}"],
            size=(280.0, 270.0),
        )
        self.wire(decode, 0, save, 0, "IMAGE")
        return save

    def root(self, *, rel: str, note: str, description: str) -> dict[str, Any]:
        """Wrap the built nodes in a serialized graph shell.

        Args:
            rel: ``_lab``-relative id used for ``extra.lab_profile``.
            note: Operator note, mirrored into ``extra.lab_note``.
            description: One-line ``extra.lab_description``.

        Returns:
            A graph dict ready for ``_finish``.
        """
        return {
            "id": rel.rsplit("/", 1)[-1],
            "revision": 1,
            "last_node_id": max(int(node["id"]) for node in self.nodes),
            "last_link_id": self.wires.last_link_id,
            "nodes": self.nodes,
            "links": self.wires.links,
            "groups": [],
            "config": {},
            "extra": {
                "lab_note": note,
                "lab_profile": rel,
                "lab_description": description,
            },
            "version": 0.4,
        }


CUTOUT_NOTE = """## photos/cutout

Background removal for image-to-3D. Load a photo of **one** character or object and
this graph cuts it out of its backdrop, so the mesh printer downstream is handed a
clean subject instead of a subject welded to a living room.

EZCutout (first-party, `custom_nodes/ez_image/cutout.py`) runs BiRefNet with its weight
loaded inside the node and fails soft: no weight, a missing dependency, or EZ_CUTOUT=0
passes the photo through untouched and says so on the node. Queue writes
`ez_cutout_NNNNN_.png` (the subject over the Backdrop you picked, white by default) and
`ez_cutout_matte_NNNNN_.png` (the grey matte that produced it), so a matte you distrust
can be repainted by hand and fed back in. The node's MASK slot is there when you want to
send the raw alpha somewhere else.

Backdrop is white, black, or keep original. Dilate grows the keep edge outward and
feather softens it; the node clamps both to 0-32. This graph ships dilate 6 and feather
4 so hair, fur, and fur trim survive the cut - drop toward 2 for a hard-edged product.

There is no UNETLoader, CLIPLoader, or VAELoader in this graph on purpose. The node owns
its own weight, this is a light pre-pass, and a loader here would make it a two-stack
App.

One subject per Queue. A busy scene, a mirror, a window full of glass, or a subject the
same tone as its backdrop is where a matte goes wrong; crop or reshoot first.

Handoff: `photos/multi-view` for the other cameras on this same subject, then
`3d/hero-from-photos` for the mesh.
"""

MULTI_VIEW_NOTE = """## photos/multi-view

Alternate views of ONE subject for image-to-3D. Load a clean photo of a single
character or object and Queue prints it four times: front, right side, back, and
top-down, all four holding the same face, costume, material, and silhouette.

One `EZSnapImage` squares the source to the Klein grid, one `VAEEncode` turns it into
the latent canvas, and four `ReferenceLatent` nodes pin all four samplers to that one
plate. Seed 42 is fixed and shared, Klein 4B distilled runs 4 steps at CFG 1.0, and the
four SHOT cards differ only in where the camera stands. Type the subject once in
IDENTITY; the shot cards are graph chrome and stay put.

Prints `ez_multiview_front`, `ez_multiview_side`, `ez_multiview_back`, and
`ez_multiview_topdown`.

This is a subject turntable, not a room tour. `photos/identity-sheet` and
`photos/dream-house` walk a camera through a place and its furniture; here the world is
a bare cyclorama and the thing that must not change is one character or object. Do not
describe rooms, walls, or furniture in IDENTITY.

""" + MODEL_LINES + """

Chain: LoadImage -> EZSnapImage -> VAEEncode -> ReferenceLatent -> KSampler ->
VAEDecode -> SaveImage, four times over the one shared plate. Do not Queue without a
start image. Handoff: `3d/multi-image-asset` and `3d/hero-from-photos`.
"""


def build_cutout() -> dict[str, Any]:
    """Background-removal cutout and its matte, with no model stack at all.

    Returns:
        A serialized graph for ``photos/cutout``.
    """
    canvas = _Canvas()
    canvas.note(CUTOUT_NOTE)
    source = canvas.load_image("Source photo")
    cutout = canvas.add(
        "EZCutout",
        title="BiRefNet cutout",
        inputs=[
            _in("image", "IMAGE"),
            _widget_in("backdrop", "COMBO"),
            _widget_in("dilate", "INT"),
            _widget_in("feather", "INT"),
        ],
        outputs=[
            _out("image", "IMAGE"),
            _out("matte", "IMAGE", slot=1),
            _out("mask", "MASK", slot=2),
        ],
        widgets=[BACKDROP, DILATE, FEATHER],
        size=(300.0, 150.0),
    )
    canvas.wire(source, 0, cutout, 0, "IMAGE")
    save_cut = canvas.add(
        "SaveImage",
        title="Save cutout",
        inputs=[_in("images", "IMAGE")],
        widgets=["ez_cutout"],
        size=(280.0, 270.0),
    )
    canvas.wire(cutout, 0, save_cut, 0, "IMAGE")
    save_matte = canvas.add(
        "SaveImage",
        title="Save matte",
        inputs=[_in("images", "IMAGE")],
        widgets=["ez_cutout_matte"],
        size=(280.0, 270.0),
    )
    canvas.wire(cutout, 1, save_matte, 0, "IMAGE")
    graph = canvas.root(
        rel="photos/cutout",
        note=CUTOUT_NOTE,
        description=(
            "Cut one character or object out of its backdrop for image-to-3D. "
            "EZCutout writes the cut still and the grey matte. No model stack."
        ),
    )
    return _finish(
        graph,
        rel="photos/cutout",
        inputs=[
            ("Source photo", "image"),
            ("BiRefNet cutout", "backdrop"),
            ("BiRefNet cutout", "dilate"),
            ("BiRefNet cutout", "feather"),
            (UPSCALE_REF, "upscale"),
        ],
        outputs=["Save cutout", "Save matte"],
        occupancy="none",
        handoff=("photos/multi-view", "3d/hero-from-photos"),
    )


def build_multi_view() -> dict[str, Any]:
    """Four identity-pinned views of one subject on the Klein stack.

    Returns:
        A serialized graph for ``photos/multi-view``.
    """
    canvas = _Canvas()
    canvas.note(MULTI_VIEW_NOTE)
    source = canvas.load_image("Character or object photo")
    stack = canvas.klein_stack()
    plate = canvas.reference_plate(source, stack["vae"])
    identity = canvas.identity_enhancer("photos/multi-view")
    negative_enhance = canvas.add(
        "EZNegativePromptEnhance",
        title="Negative Prompt Enhance",
        inputs=[_in("positive", "STRING")],
        outputs=[_out("prompt", "STRING")],
        widgets=[NEGATIVE, True, "klein"],
        size=(420.0, 280.0),
    )
    negative = canvas.add(
        "CLIPTextEncode",
        title="Negative",
        inputs=[_in("clip", "CLIP"), _in("text", "STRING")],
        outputs=[_out("CONDITIONING", "CONDITIONING")],
        widgets=[NEGATIVE],
        size=(420.0, 120.0),
    )
    canvas.wire(stack["clip"], 0, negative, 0, "CLIP")
    canvas.wire(negative_enhance, 0, negative, 1, "STRING")
    saves: list[dict[str, Any]] = []
    for slug, suffix, shot in VIEWS:
        saves.append(
            canvas.view(
                slug=slug,
                suffix=suffix,
                shot=shot,
                identity=identity,
                clip=stack["clip"],
                negative=negative,
                unet=stack["unet"],
                encode=plate["encode"],
                vae=stack["vae"],
            )
        )
    # The negative is rewritten against the front view only: the four shot cards
    # differ by camera, so one rewrite is enough for all four samplers.
    canvas.wire(_find_join(canvas, "FRONT"), 0, negative_enhance, 0, "STRING")
    graph = canvas.root(
        rel="photos/multi-view",
        note=MULTI_VIEW_NOTE,
        description=(
            "Klein 4B four-view plate of one subject: front, side, back, top-down. "
            "Shared seed, shared ReferenceLatent, camera moves only. Prefix ez_multiview."
        ),
    )
    return _finish(
        graph,
        rel="photos/multi-view",
        inputs=[
            ("Character or object photo", "image"),
            ("IDENTITY", "sample"),
            ("IDENTITY", "prompt"),
            (UPSCALE_REF, "upscale"),
            ("IDENTITY", "style"),
            ("IDENTITY", "enhance"),
            ("Negative Prompt Enhance", "enhance"),
            ("Sampler FRONT", "seed"),
        ],
        outputs=[str(node["title"]) for node in saves],
        occupancy="klein",
        handoff=("3d/multi-image-asset", "3d/hero-from-photos"),
    )


def _find_join(canvas: _Canvas, suffix: str) -> dict[str, Any]:
    """Return the SHOT node whose title carries one view suffix.

    Args:
        canvas: The canvas being built.
        suffix: Uppercase view name.

    Returns:
        The matching ``EZPromptJoin`` node.
    """
    return next(
        node
        for node in canvas.nodes
        if node.get("type") == "EZPromptJoin" and node.get("title") == f"SHOT {suffix}"
    )


def _upscale_master(graph: dict[str, Any]) -> dict[str, Any] | None:
    """Return the ``EZImageUpscale`` whose combo still belongs to the App.

    ``wire_upscale`` leaves the first node's combo free and links every later
    one to it, so one App dropdown drives every save.

    Args:
        graph: Serialized graph.

    Returns:
        The master upscale node, or None when the graph carries none.
    """
    nodes: list[dict[str, Any]] = graph.get("nodes") or []
    for node in nodes:
        if node.get("type") != "EZImageUpscale":
            continue
        slots: list[dict[str, Any]] = node.get("inputs") or []
        linked = any(
            slot.get("name") == "upscale" and slot.get("link") is not None
            for slot in slots
        )
        if not linked:
            return node
    return None


def _finish(
    graph: dict[str, Any],
    *,
    rel: str,
    inputs: list[tuple[int | str, str]],
    outputs: list[str],
    occupancy: str,
    handoff: tuple[str, ...],
) -> dict[str, Any]:
    """Stamp the lab chrome every shipped App carries.

    Upscale is inserted before the stamp so the App row can name the node the
    dropdown actually belongs to: every ``photos/`` save must arrive at its
    ``SaveImage`` through ``EZImageUpscale``.

    Args:
        graph: Graph shell from :meth:`_Canvas.root`.
        rel: ``_lab``-relative id, used for the upscale scope check.
        inputs: (node title or id, widget name) rows for the App sidebar.
            :data:`UPSCALE_REF` resolves to the master upscale node.
        outputs: Node titles that write a file.
        occupancy: ``none`` for the cutout, ``klein`` for the view plate.
        handoff: Downstream app ids.

    Returns:
        The stamped graph.

    Raises:
        ValueError: an App row asked for the upscale dropdown and the graph
            carries no upscale node to hang it on.
    """
    ensure_occupancy_note(graph, occupancy)
    wire_upscale(graph, rel)
    master = _upscale_master(graph)
    rows: list[tuple[int | str, str]] = []
    for ref, widget in inputs:
        if ref == UPSCALE_REF:
            if master is None:
                raise ValueError(f"{rel}: no EZImageUpscale node for the App row")
            rows.append((int(master["id"]), widget))
            continue
        rows.append((ref, widget))
    stamp_app_mode(
        graph,
        inputs=rows,
        outputs=outputs,
        lane="photos",
        occupancy=occupancy,
        handoff=handoff,
        default_view="app",
    )
    # Each view owns its negative rewrite, fed by that view's own shot card, so
    # the shared negative built above is split per EZPromptJoin by the patcher.
    repair_negative_sources(graph)
    return apply_lab_completeness_flags(graph)


BUILDERS = {
    "photos/cutout": build_cutout,
    "photos/multi-view": build_multi_view,
}


def main() -> None:
    """Regenerate both image-prep Apps and print what was written."""
    for rel, builder in BUILDERS.items():
        dest = lab_dest(rel, lane="photos")
        graph = builder()
        finalize_layout(graph)
        write_lab_graph(dest, graph)
        print(dest)


if __name__ == "__main__":
    main()
