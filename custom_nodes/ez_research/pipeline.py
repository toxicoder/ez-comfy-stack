"""Chat and bounded research subagents for ez_research.

Subagents are sequential in-process roles (planner → searchers → synthesizer).
One llama.cpp instance; CPU only via ez_prompt_enhance.client.complete.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from .search import SearchHit, format_sources, search_web

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
MIN_SUBAGENTS = 1
MAX_SUBAGENTS = 3
_SLUG_RE = re.compile(r"[^a-z0-9]+")


@dataclass
class ResearchResult:
    """Reply plus sources list and a passthrough status."""

    text: str
    sources: str
    status: str
    queries: list[str]


def _log(message: str) -> None:
    print(f"[ez_research] {message}", file=sys.stderr)


def _ensure_lab_custom_nodes_path() -> None:
    """Make sibling ez_* packs importable under ComfyUI 0.34+ load_custom_node.

    Comfy registers directory packs as the filesystem path, not the folder
    name, and does not put custom_nodes on sys.path.
    """
    root = str(Path(__file__).resolve().parent.parent)
    if root not in sys.path:
        sys.path.insert(0, root)


def load_prompt(name: str) -> str:
    """Load a system prompt from ``prompts/<name>.txt``."""
    path = PROMPTS_DIR / f"{name}.txt"
    return path.read_text(encoding="utf-8").strip()


def clamp_subagents(value: object) -> int:
    """Clamp the subagent count to 1–3."""
    count = 2
    if isinstance(value, bool):
        count = int(value)
    elif isinstance(value, int):
        count = value
    elif isinstance(value, float):
        count = int(value)
    elif isinstance(value, str):
        try:
            count = int(value.strip())
        except ValueError:
            count = 2
    if count < MIN_SUBAGENTS:
        return MIN_SUBAGENTS
    if count > MAX_SUBAGENTS:
        return MAX_SUBAGENTS
    return count


def parse_planner_queries(text: str, fallback: str, limit: int) -> list[str]:
    """Parse planner JSON ``{"queries":[...]}``. Fallback is the user message."""
    cap = clamp_subagents(limit)
    blob = (text or "").strip()
    queries: list[str] = []
    start = blob.find("{")
    end = blob.rfind("}")
    if start >= 0 and end > start:
        try:
            data = json.loads(blob[start : end + 1])
        except json.JSONDecodeError:
            data = None
        if isinstance(data, dict):
            raw = data.get("queries")
            if isinstance(raw, list):
                queries = [str(item).strip() for item in raw if str(item).strip()]
    if not queries:
        fb = (fallback or "").strip()
        return [fb] if fb else []
    unique: list[str] = []
    seen: set[str] = set()
    for query in queries:
        key = query.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(query)
        if len(unique) >= cap:
            break
    return unique


def _complete(system: str, user: str) -> tuple[str, str]:
    """Run the on-box GGUF. Fail-soft if the sibling pack cannot import."""
    try:
        _ensure_lab_custom_nodes_path()
        from ez_prompt_enhance.client import complete as llama_complete
    except Exception as exc:  # noqa: BLE001 — fail-soft
        _log(f"prompt enhance client unavailable: {exc}")
        return "", "llama.cpp unavailable"
    text, reason = llama_complete(system, user, max_tokens=700, temperature=0.2)
    return (text or "").strip(), (reason or "")


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def _compose_user(message: str, history: str, extra: str = "") -> str:
    parts = [message.strip()]
    hist = (history or "").strip()
    if hist:
        parts.append("Prior turns:\n" + hist)
    extra_s = extra.strip()
    if extra_s:
        parts.append(extra_s)
    return "\n\n".join(parts)


def _fallback_brief(message: str, hits: list[SearchHit]) -> str:
    lines = [
        "## Brief",
        message.strip() or "(empty)",
        "",
        "## Sources",
    ]
    if hits:
        lines.append(format_sources(hits) or "(none)")
    else:
        lines.append("(none — search empty or web search off)")
    lines.extend(
        [
            "",
            "## Prompt ingredients",
            "- subject and wardrobe from the question",
            "- one light logic",
            "- one camera / lens note",
            "",
            "## Next App",
            "prompt-forge-lab-example, then klein-still-draft-lab-example",
        ]
    )
    return "\n".join(lines).strip()


def _hits_block(hits: list[SearchHit]) -> str:
    if not hits:
        return "Sources: (none)"
    chunks: list[str] = []
    for i, hit in enumerate(hits, start=1):
        body = (hit.body or hit.snippet or "").strip()
        chunks.append(f"[{i}] {hit.title}\nURL: {hit.url}\n{body}")
    return "Sources:\n" + "\n\n".join(chunks)


def run_chat(
    message: str,
    *,
    history: str = "",
    web_search: bool = False,
) -> ResearchResult:
    """One-turn chat. Optional search snippets prepended to the user message."""
    text = (message or "").strip()
    if not text:
        return ResearchResult("", "", "empty message", [])
    hits: list[SearchHit] = []
    if web_search:
        hits = search_web(text, limit=3, fetch_bodies=True)
    extra = _hits_block(hits) if hits else ""
    reply, reason = _complete(load_prompt("chat"), _compose_user(text, history, extra))
    status = reason or "ok"
    if not reply:
        reply = _fallback_brief(text, hits)
        if not reason:
            status = "llm passthrough"
    return ResearchResult(
        text=reply,
        sources=format_sources(hits),
        status=status,
        queries=[text] if web_search else [],
    )


def run_research(
    message: str,
    *,
    history: str = "",
    web_search: bool = True,
    subagents: object = 2,
) -> ResearchResult:
    """Planner → N searchers → synthesizer. Sequential; one GGUF."""
    text = (message or "").strip()
    if not text:
        return ResearchResult("", "", "empty message", [])
    n = clamp_subagents(subagents)
    planner_user = _compose_user(
        text,
        history,
        extra=f"Subagent count: {n}. JSON only.",
    )
    planner_out, planner_reason = _complete(load_prompt("planner"), planner_user)
    queries = parse_planner_queries(planner_out, text, n)
    hits: list[SearchHit] = []
    if web_search:
        for query in queries:
            hits.extend(search_web(query, limit=3, fetch_bodies=True))
    synth_extra = (
        f"Planner queries: {json.dumps(queries)}\n\n{_hits_block(hits)}"
    )
    reply, reason = _complete(
        load_prompt("synthesizer"),
        _compose_user(text, history, synth_extra),
    )
    status = reason or planner_reason or "ok"
    if not reply:
        reply = _fallback_brief(text, hits)
        if not reason:
            status = "llm passthrough"
    return ResearchResult(
        text=reply,
        sources=format_sources(hits),
        status=status,
        queries=queries,
    )


def slug_for_prompt(prompt: str) -> str:
    """Filesystem slug from the first words of the message."""
    raw = (prompt or "brief").lower()
    slug = _SLUG_RE.sub("-", raw).strip("-")
    if not slug:
        slug = "brief"
    return slug[:40]


def write_brief(
    result: ResearchResult,
    prompt: str,
    output_dir: Path | None = None,
) -> Path | None:
    """Write ``ez_research_<slug>.md`` under ``COMFY_OUTPUT_DIR/research``.

    Never writes under MODELS_DIR.
    """
    if output_dir is None:
        env = os.environ.get("COMFY_OUTPUT_DIR")
        if not env:
            return None
        output_dir = Path(env)
    models = os.environ.get("MODELS_DIR")
    try:
        dest_dir = (output_dir / "research").resolve()
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"ez_research_{slug_for_prompt(prompt)}.md"
        resolved = dest.resolve()
        if models:
            models_root = Path(models).resolve()
            try:
                resolved.relative_to(models_root)
            except ValueError:
                pass
            else:
                _log("refusing to write research brief under MODELS_DIR")
                return None
        body = result.text.strip()
        if result.sources.strip() and "## Sources" not in body:
            body = f"{body}\n\n## Sources\n{result.sources.strip()}\n"
        dest.write_text(body + "\n", encoding="utf-8")
        return dest
    except OSError as exc:
        _log(f"brief write failed: {exc}")
        return None
