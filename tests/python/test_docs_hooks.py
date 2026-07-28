"""Unit tests for docs/hooks.py branch stamping (no MkDocs install required).

Hermetic: only stdlib + the hooks module loaded from docs/hooks.py.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

HOOKS_PATH = Path(__file__).resolve().parents[2] / "docs" / "hooks.py"


def _load_hooks():
    """Load docs/hooks.py as a module without installing a package.

    Returns:
        The loaded hooks module.
    """
    spec = importlib.util.spec_from_file_location("ez_docs_hooks", HOOKS_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def hooks(monkeypatch: pytest.MonkeyPatch):
    """Load hooks with a clean env (no version stamps).

    Args:
        monkeypatch: Pytest monkeypatch fixture.

    Yields:
        Loaded hooks module.
    """
    monkeypatch.delenv("MIKE_DOCS_VERSION", raising=False)
    monkeypatch.delenv("EZ_DOCS_VERSION", raising=False)
    monkeypatch.delenv("EZ_DOCS_GIT_REF", raising=False)
    return _load_hooks()


def test_docs_version_prefers_mike(hooks, monkeypatch: pytest.MonkeyPatch) -> None:
    """MIKE_DOCS_VERSION wins over EZ_DOCS_VERSION."""
    monkeypatch.setenv("MIKE_DOCS_VERSION", "development")
    monkeypatch.setenv("EZ_DOCS_VERSION", "latest")
    assert hooks.docs_version() == "development"


def test_docs_version_falls_back_to_ez(hooks, monkeypatch: pytest.MonkeyPatch) -> None:
    """EZ_DOCS_VERSION is used when MIKE_DOCS_VERSION is unset."""
    monkeypatch.setenv("EZ_DOCS_VERSION", "Development")
    assert hooks.docs_version() == "development"


def test_docs_git_ref_default_main(hooks) -> None:
    """Unset version maps edit/source links to main."""
    assert hooks.docs_git_ref() == "main"


def test_docs_git_ref_development(hooks, monkeypatch: pytest.MonkeyPatch) -> None:
    """Development docs version maps to the development branch."""
    monkeypatch.setenv("EZ_DOCS_VERSION", "development")
    assert hooks.docs_git_ref() == "development"


def test_docs_git_ref_override(hooks, monkeypatch: pytest.MonkeyPatch) -> None:
    """EZ_DOCS_GIT_REF overrides version-derived ref."""
    monkeypatch.setenv("EZ_DOCS_VERSION", "development")
    monkeypatch.setenv("EZ_DOCS_GIT_REF", "main")
    assert hooks.docs_git_ref() == "main"


def test_on_config_stamps_edit_uri(hooks, monkeypatch: pytest.MonkeyPatch) -> None:
    """on_config writes edit_uri for the active long-lived ref."""
    monkeypatch.setenv("MIKE_DOCS_VERSION", "development")
    config = {"edit_uri": "edit/main/docs/"}
    out = hooks.on_config(config)
    assert out["edit_uri"] == "edit/development/docs/"


def test_stamp_git_ref_rewrites_this_repo_only(
    hooks, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only this repo's blob/tree main|master|development segments are stamped."""
    monkeypatch.setenv("EZ_DOCS_VERSION", "development")
    text = (
        "see https://github.com/toxicoder/ez-comfy-stack/blob/main/docs/index.md "
        "and https://github.com/toxicoder/nvidia-dgx-spark-lab/blob/main/README.md "
        "and https://github.com/toxicoder/ez-comfy-stack/tree/master/scripts/"
    )
    out = hooks.stamp_git_ref(text)
    assert (
        "https://github.com/toxicoder/ez-comfy-stack/blob/development/docs/index.md"
        in out
    )
    assert (
        "https://github.com/toxicoder/nvidia-dgx-spark-lab/blob/main/README.md" in out
    )
    assert "https://github.com/toxicoder/ez-comfy-stack/tree/development/scripts/" in out


def test_on_post_page_injects_dev_banner(
    hooks, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Development version injects a banner before the first h1 when needed."""
    monkeypatch.setenv("MIKE_DOCS_VERSION", "development")
    html = "<html><body><h1>Title</h1></body></html>"
    out = hooks.on_post_page(html)
    assert "ez-docs-dev-banner" in out
    assert "Development docs" in out


def test_on_post_page_skips_banner_for_latest(
    hooks, monkeypatch: pytest.MonkeyPatch
) -> None:
    """latest alias does not inject the development banner."""
    monkeypatch.setenv("MIKE_DOCS_VERSION", "latest")
    html = "<html><body><h1>Title</h1></body></html>"
    out = hooks.on_post_page(html)
    assert "ez-docs-dev-banner" not in out
