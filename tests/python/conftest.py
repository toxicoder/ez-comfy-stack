"""Pytest configuration for Spark free-memory patch unit tests.

Ensures the ``docker/`` directory is importable as a top-level path so tests can
``import patch_get_free_memory`` and coverage can attribute lines to
``patch_get_free_memory.py`` without packaging the module.

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
