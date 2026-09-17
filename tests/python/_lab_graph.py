"""Shared Comfy lab Graph builder (podcast / dub / music).

Dump flags preserve each builder's identity and note-rewrite behavior so
shipped JSON does not restamp unless a caller opts in.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from _lab_layout import finalize_layout
from _lab_paths import apply_lab_identity
from _stamp_app_mode import stamp_suite_graph
from _wire_prompt_enhance import _rewrite_enhance_blurb, enable_lab_graph


class Graph:
    """Minimal node/link builder used by underscored workflow scripts."""

    def __init__(
        self,
        graph_id: str,
        *,
        pop_lab_rel: bool = True,
        enable_lab: bool = False,
        rewrite_enhance_note: bool = False,
    ) -> None:
        self.graph_id = graph_id
        self.nodes: list[dict[str, Any]] = []
        self.links: list[list[Any]] = []
        self._lid = 0
        self._pop_lab_rel = pop_lab_rel
        self._enable_lab = enable_lab
        self._rewrite_enhance_note = rewrite_enhance_note

    def add(
        self,
        nid: int,
        ntype: str,
        pos: list[float],
        size: list[float],
        title: str,
        widgets: list[Any] | dict[str, Any],
        *,
        inputs: list[Any] | None = None,
        outputs: list[Any] | None = None,
        mode: int = 0,
        properties: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        node: dict[str, Any] = {
            "id": nid,
            "type": ntype,
            "pos": pos,
            "size": size,
            "flags": {},
            "order": len(self.nodes),
            "mode": mode,
            "inputs": inputs or [],
            "outputs": outputs or [],
            "properties": properties or {"Node name for S&R": ntype},
            "widgets_values": widgets,
            "title": title,
        }
        self.nodes.append(node)
        return node

    def out(
        self,
        name: str,
        ltype: str,
        links: list[int] | None = None,
        slot: int = 0,
    ) -> dict[str, Any]:
        return {
            "name": name,
            "type": ltype,
            "links": links if links is not None else [],
            "slot_index": slot,
        }

    def inp(
        self,
        name: str,
        ltype: str,
        link: int | None = None,
        widget: str | None = None,
    ) -> dict[str, Any]:
        item: dict[str, Any] = {"name": name, "type": ltype, "link": link}
        if widget is not None:
            item["widget"] = {"name": widget}
        return item

    def link(
        self, src: int, src_slot: int, dst: int, dst_slot: int, ltype: str
    ) -> int:
        self._lid += 1
        self.links.append([self._lid, src, src_slot, dst, dst_slot, ltype])
        dst_node = next(n for n in self.nodes if n["id"] == dst)
        dst_node["inputs"][dst_slot]["link"] = self._lid
        src_node = next(n for n in self.nodes if n["id"] == src)
        src_node["outputs"][src_slot]["links"].append(self._lid)
        return self._lid

    def dump(self, extra: dict[str, Any]) -> dict[str, Any]:
        groups = extra.pop("groups")
        if self._pop_lab_rel:
            rel = str(extra.pop("lab_rel", self.graph_id))
            graph_id = Path(rel).name
            identity = rel
        else:
            graph_id = self.graph_id
            identity = self.graph_id
        graph: dict[str, Any] = {
            "id": graph_id,
            "revision": 1,
            "last_node_id": max(n["id"] for n in self.nodes),
            "last_link_id": self._lid,
            "nodes": self.nodes,
            "links": self.links,
            "groups": groups,
            "config": {},
            "extra": extra,
            "version": 0.4,
        }
        apply_lab_identity(graph, identity)
        if self._enable_lab:
            enable_lab_graph(graph)
        stamp_suite_graph(graph)
        if self._rewrite_enhance_note:
            extra_out = graph.setdefault("extra", {})
            extra_out["lab_note"] = _rewrite_enhance_blurb(
                str(extra_out.get("lab_note") or "")
            )
            for node in graph["nodes"]:
                if node.get("type") != "Note":
                    continue
                values = node.get("widgets_values") or [""]
                node["widgets_values"] = [_rewrite_enhance_blurb(str(values[0]))]
                break
        finalize_layout(graph)
        return graph
