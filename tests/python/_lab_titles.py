"""Fill in the node titles a lab graph ships without.

Not imported by pytest collection (leading underscore). Builders and
``_lab_paths.write_lab_graph`` import it; the gate is ``test_lab_titles.py``.

ComfyUI draws ``node.title`` on the canvas and falls back to the class name when
it is absent, so 880 samplers in the shipped tree read ``KSampler`` and 62
conditioning/decode nodes read their class verbatim. The title also feeds the
node search box and the properties panel, which is where an operator finds a
node once a graph has 18 samplers in it.

Rules, matching what the hand-written corpus already does:

- An existing human title is never replaced with another label. Only a missing
  title, a title equal to the class name, and an adjacent doubled word are
  rewritten; a title a same-class sibling already wears only gains the counting
  number that tells the two apart.
- ``CLASS_TITLES`` is mined from this corpus: the most common human title per
  class, kept only where that title covers at least 60% of the class's titled
  nodes and carries no digit (a digit in a title is that node's size, bitrate,
  or checkpoint, not a label for the class).
- Samplers follow the corpus rule: one sampler in a graph reads ``Sampler``,
  several read ``Sampler 1``..``Sampler N`` in node-id order.
- No two nodes of one class in one graph carry the same title, whatever wrote
  it: a label a sibling already wears is numbered clear of it in node-id order,
  so three untitled ``EZImageUpscale`` nodes read ``Upscale still`` /
  ``Upscale still 2`` / ``Upscale still 3``, and 18 ``SaveImage`` nodes all
  authored ``Save last frame`` read ``Save last frame`` .. ``Save last frame
  18``. A title that arrives already wearing the table's own label is numbered
  the same way, which is what makes a builder that stamps ``Upscale still`` on
  every node it inserts rebuild to the shipped graph. A title only counts as
  worn by its own class, so two different classes both reading ``Negative SHOT
  WIDE`` stay exactly as authored; a title already wearing a number this pass
  wrote is a distinct label and is never re-derived from its stem.
"""

from __future__ import annotations

import re
from typing import Iterator

MAX_TITLE_CHARS = 60

#: Classes the sampler numbering rule applies to.
SAMPLER_CLASSES = frozenset({"KSampler", "KSamplerAdvanced"})

_NEGATIVE_PREFIX = "Negative "
_UNTITLED = "Untitled node"

# One word repeated with nothing but whitespace between the two copies. The
# corpus defect is the doubled "Negative " prefix that
# _wire_prompt_enhance used to add on every pass.
_DOUBLED_RX = re.compile(r"(?i)\b([A-Za-z]{2,})([ \t]+)\1\b[ \t]*")
_WORD_RX = re.compile(r"[A-Za-z]{2,}")
_CAMEL_RX = re.compile(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+")

#: Fallback label per class, mined from the titles this corpus already uses.
CLASS_TITLES: dict[str, str] = {
    "EZAlbumPack": "Pack album zip",
    "EZAudioBeatJoin": "Beat-join passes",
    "EZAudioMetadata": "Album metadata",
    "EZBackgroundCast": "Background cast",
    "EZDCCLoadGuideStill": "Load guide still",
    "EZDCCOccupancyGate": "Occupancy gate",
    "EZFilmDisclosure": "LTX AI-media disclosure (end-card)",
    "EZImageDescribe": "Describe image",
    "EZImageFormat": "Format / platform",
    "EZImageUpscale": "Upscale still",
    "EZKleinPromptEnhance": "Klein Prompt Enhance",
    "EZKleinRefCanvas": "Optional Klein ref",
    "EZMatchImageSize": "Match source size",
    "EZModelCheck": "Check models",
    "EZNegativePromptEnhance": "Negative Prompt Enhance",
    "EZNvidiaLabCatalog": "Tier table",
    "EZNvidiaLabJob": "Run the row",
    "EZNvidiaLabPreflight": "Preflight",
    "EZNvidiaLabVerdict": "Verdict",
    "EZOptionalImage": "Example / reference (optional)",
    "EZPodcastDisclosure": "Disclosure bumper",
    "EZPromptBundle": "Shot prompt bundle",
    "EZQuality": "Detail",
    "EZRapLyrics": "Rap lyrics",
    "EZSamplePrompt": "Identity context",
    "EZSceneLayout": "Compose scene layout",
    "EZSnapImage": "Snap to Klein grid",
    "EZUnloadModels": "Unload models (pass IMAGE)",
    "EZVideoFormat": "Format / platform",
    "EZWanPromptEnhance": "Wan Prompt Enhance",
    "ImageFromBatch": "Last frame",
    "LTXVAudioVAEDecode": "Audio VAE Decode",
    "LTXVConcatAVLatent": "Concat AV latents",
    "LTXVConditioning": "LTX frame rate cond",
    "LTXVEmptyLatentAudio": "Empty LTX audio latent",
    "LTXVImgToVideo": "LTX Img->Video condition",
    "LTXVSeparateAVLatent": "Separate AV latents",
    "MeshToFile3D": "To GLB bytes",
    "ModelSamplingAuraFlow": "AuraFlow sampling",
    "ModelSamplingSD3": "Shift",
    "Note": "Operator note",
    "PaintMesh": "Paint mesh",
    "SaveAudio": "FLAC master",
    "SaveGLB": "Save GLB",
    "Trellis2ShapeStage": "Shape stage",
    "Trellis2TextureStage": "Texture stage",
    "VAEDecode": "VAE Decode",
    "VaeDecodeShapeTrellis": "Decode shape",
    "VaeDecodeTextureTrellis": "Decode texture",
}


def _iter_nodes(graph: dict[str, object]) -> Iterator[dict[str, object]]:
    """Yield every node dict in a graph, root nodes and subgraph nodes alike.

    The graph arrives from ``json.loads``, so every level is narrowed with
    ``isinstance`` before it is walked rather than trusted.

    Args:
        graph: Comfy workflow dict.

    Yields:
        Each node dict, in document order.
    """
    root_nodes = graph.get("nodes")
    if isinstance(root_nodes, list):
        for node in root_nodes:
            if isinstance(node, dict):
                yield node
    definitions = graph.get("definitions")
    if isinstance(definitions, dict):
        subgraphs = definitions.get("subgraphs")
        if isinstance(subgraphs, list):
            for sub in subgraphs:
                if not isinstance(sub, dict):
                    continue
                sub_nodes = sub.get("nodes")
                if not isinstance(sub_nodes, list):
                    continue
                for node in sub_nodes:
                    if isinstance(node, dict):
                        yield node


def _doubled_words(title: str) -> list[str]:
    """Return the words a title repeats back to back.

    Args:
        title: Candidate title text.

    Returns:
        The lowercased words repeated in adjacent position, in order.
    """
    lowered = [word.lower() for word in _WORD_RX.findall(title)]
    return [first for first, second in zip(lowered, lowered[1:]) if first == second]


def _collapse_doubled(title: str) -> str:
    """Halve every back-to-back word repetition in a title.

    Args:
        title: Candidate title text.

    Returns:
        The title with each adjacent duplicate removed; the original when the
        repeats are not whitespace-separated and so cannot be halved.
    """
    text = title
    for _ in range(4):
        if not _doubled_words(text):
            break
        collapsed = _DOUBLED_RX.sub(r"\1 ", text)
        if collapsed == text:
            break
        text = collapsed
    return text if not _doubled_words(text) else title


def _derived_title(node_type: str) -> str:
    """Build a neutral label for a class the corpus never titles.

    Arguments:
        node_type: Node ``type``.
    Returns:
        A spaced reading of the class name, capped at ``MAX_TITLE_CHARS``, that
        is never empty and never repeats the class name.
    """
    stem = node_type.split("(", 1)[0]
    words: list[str] = []
    for token in _CAMEL_RX.findall(stem):
        if words and words[-1].casefold() == token.casefold():
            continue
        words.append(token)
    title = " ".join(words).strip()
    while len(title) > MAX_TITLE_CHARS and len(words) > 1:
        words.pop()
        title = " ".join(words).strip()
    if len(title) > MAX_TITLE_CHARS:
        title = title[:MAX_TITLE_CHARS].rstrip()
    if not title or title == node_type or _doubled_words(title):
        return _UNTITLED
    return title


def title_for_class(node_type: str, index: int, total: int) -> str:
    """Return the label a node of this class should carry.

    Samplers are numbered: one sampler in a graph reads ``Sampler``, several
    read ``Sampler 1``..``Sampler N``, so ``index`` (0-based) and ``total``
    matter only for ``SAMPLER_CLASSES``.

    Arguments:
        node_type: Node ``type``.
        index: Position of this node among the samplers of its graph.
        total: Number of samplers in the graph.
    Returns:
        The title text, 60 characters or fewer.
    """
    if node_type in SAMPLER_CLASSES:
        if total <= 1:
            return "Sampler"
        return f"Sampler {index + 1}"
    seeded = CLASS_TITLES.get(node_type)
    if seeded:
        return seeded
    return _derived_title(node_type)


def ensure_node_titles(graph: dict[str, object]) -> int:
    """Title every untitled node in a graph in place.

    A title is set when it is missing, when it repeats the class name, and
    halved when it repeats a word back to back. Any other title is the
    operator-facing text the graph already shipped with and keeps its words.

    Samplers are numbered over the ones this pass titles, so a graph whose
    ``Sampler CLOSE`` / ``Sampler WIDE`` pair also carries two bare samplers
    reads ``Sampler 1`` / ``Sampler 2`` next to the hand-written pair instead
    of continuing a numbering the operator never started.

    Every title this pass writes is numbered clear of the titles the graph
    already carries, authored ones included, so no two nodes in one graph read
    the same label. A title the graph arrived wearing is numbered the same way
    when an earlier node of the same class carries it, whatever wrote that
    title, plus once more for a table label a node of another class wears;
    nodes are walked in ``_node_sort_key`` order so the numbering does not
    depend on where a node sits in the file.

    Arguments:
        graph: Comfy workflow dict (mutated).
    Returns:
        The number of nodes whose ``title`` changed.
    """
    nodes = list(_iter_nodes(graph))
    taken = {
        stripped
        for node in nodes
        for stripped in [str(node.get("title") or "").strip()]
        if stripped
    }
    samplers = sorted(
        (node for node in nodes if str(node.get("type") or "") in SAMPLER_CLASSES),
        key=_node_sort_key,
    )
    sampler_total = len(samplers)
    changed = 0
    position = 0
    for node in samplers:
        if _title_needs_setting(node):
            title = _unique_title(
                title_for_class(str(node.get("type") or ""), position, sampler_total),
                taken,
            )
            node["title"] = title
            taken.add(title)
            position += 1
            changed += 1
            continue
        repaired = _repaired_title(node)
        if repaired is not None:
            node["title"] = repaired
            taken.add(repaired)
            changed += 1
    for node in nodes:
        if str(node.get("type") or "") in SAMPLER_CLASSES:
            continue
        if _title_needs_setting(node):
            title = _unique_title(
                title_for_class(str(node.get("type") or ""), 0, 1), taken
            )
            node["title"] = title
            taken.add(title)
            changed += 1
            continue
        repaired = _repaired_title(node)
        if repaired is not None:
            node["title"] = repaired
            taken.add(repaired)
            changed += 1
    bases = set(CLASS_TITLES.values())
    bases.update(title_for_class(str(node.get("type") or ""), 0, 1) for node in nodes)
    worn: set[tuple[str, str]] = set()
    worn_titles: set[str] = set()
    for node in sorted(nodes, key=_node_sort_key):
        node_type = str(node.get("type") or "")
        title = str(node.get("title") or "").strip()
        if title and (
            (node_type, title) in worn
            or (title in worn_titles and _is_table_sourced(title, bases))
        ):
            title = _unique_title(title, taken)
            node["title"] = title
            taken.add(title)
            changed += 1
        if title:
            worn.add((node_type, title))
            worn_titles.add(title)
    return changed


def _is_table_sourced(title: str, bases: set[str]) -> bool:
    """Whether a title is a label the title pass writes, not an operator's prose.

    ``test_lab_titles._is_table_sourced`` is this predicate verbatim: what this
    pass is willing to renumber has to be exactly what that gate may call a
    duplicate, or a rebuild and the shipped graph disagree forever. The pass
    also numbers a repeat inside one class, table-sourced or not; this
    predicate is the cross-class half of that rule, the one that numbers a
    table label two nodes of different classes both wear.

    Arguments:
        title: Title text.
        bases: Every label the pass can generate in this graph.
    Returns:
        ``True`` for a label in the table and for that label with a plain ASCII
        counting number on the end. A leading zero is the operator's own
        numbering, so it is not table-sourced.
    """
    if title in bases:
        return True
    stem, sep, tail = title.rpartition(" ")
    if not sep or stem not in bases:
        return False
    return _is_pass_number(tail)


def _title_needs_setting(node: dict[str, object]) -> bool:
    """Whether a node carries no title or only its class name.

    Arguments:
        node: Node dict.
    Returns:
        ``True`` when the node needs a generated title.
    """
    raw = node.get("title")
    if not isinstance(raw, str) or not raw.strip():
        return True
    return raw.strip() == str(node.get("type") or "")


def _repaired_title(node: dict[str, object]) -> str | None:
    """Return the halved form of a doubled title, or ``None`` to leave it be.

    Arguments:
        node: Node dict.
    Returns:
        The repaired title text, or ``None`` when the title reads clean or the
        repeat cannot be halved.
    """
    raw = node.get("title")
    if not isinstance(raw, str) or not raw.strip():
        return None
    title = raw.strip()
    if not _doubled_words(title):
        return None
    collapsed = _collapse_doubled(title)
    if collapsed == title or collapsed == str(node.get("type") or ""):
        return None
    return collapsed


def _node_sort_key(node: dict[str, object]) -> tuple[int, int]:
    """Order nodes by numeric id, non-numeric ids keeping document order.

    Arguments:
        node: Node dict.
    Returns:
        A sort key for ``(numeric id, id)``.
    """
    raw = node.get("id")
    try:
        return (0, int(str(raw)))
    except (TypeError, ValueError):
        return (1, 0)


def _unique_title(title: str, taken: set[str]) -> str:
    """Number a generated title clear of every title the graph already carries.

    Both the sampler path and the plain path take their label from the table,
    so both have to clear the same set: ``taken`` starts as every title the
    graph shipped with and grows with every title this pass sets.

    Arguments:
        title: The label the pass wants for the node.
        taken: Every other title in the graph.
    Returns:
        ``title`` when it is free, else ``title 2``, ``title 3``, ... the first
        numbered variant nobody else in the graph wears.
    """
    unique = title
    while unique in taken:
        stem, sep, tail = unique.rpartition(" ")
        if sep and _is_pass_number(tail):
            unique = f"{stem} {_next_number(unique)}"
        else:
            unique = f"{unique} {_next_number(unique)}"
    return unique


def _is_pass_number(tail: str) -> bool:
    """Whether a trailing token is a number this pass wrote, not an operator.

    The pass numbers with ``str(int)``, so a leading zero can only be the
    operator's own numbering (the corpus ships ``Sampler 01``..``Sampler 06``)
    and is left as authored.

    Arguments:
        tail: The last whitespace-separated token of a title.
    Returns:
        ``True`` for a plain ASCII counting number with no leading zero.
    """
    return tail.isdigit() and tail.isascii() and not tail.startswith("0")


def _next_number(title: str) -> int:
    """Return the number one past the trailing number of a generated title.

    Arguments:
        title: A ``Sampler N`` or ``Upscale still 2`` style title.
    Returns:
        The next integer in the sequence, or ``2`` when there is none.
    """
    tail = title.rsplit(" ", 1)[-1]
    try:
        return int(tail) + 1
    except ValueError:
        return 2
