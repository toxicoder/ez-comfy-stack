"""Pytest configuration for Spark free-memory patch unit tests.

Ensures the ``docker/`` directory is importable as a top-level path so tests can
``import patch_get_free_memory`` / ``patch_unified_memory_copy`` and coverage can
attribute lines without packaging the modules.

This conftest intentionally performs only sys.path setup — no network, Docker,
or GPU fixtures — keeping the suite hermetic for CI and laptops.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCKER = ROOT / "docker"
CUSTOM = ROOT / "custom_nodes"
if str(DOCKER) not in sys.path:
    sys.path.insert(0, str(DOCKER))
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))
