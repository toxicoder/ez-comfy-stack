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


def test_stamp_docs_git_ref_placeholder_default_main(hooks) -> None:
    """Unset version replaces __DOCS_GIT_REF__ with main."""
    text = "git clone -b __DOCS_GIT_REF__ https://github.com/toxicoder/ez-comfy-stack.git"
    out = hooks.stamp_docs_git_ref_placeholder(text)
    assert out == (
        "git clone -b main https://github.com/toxicoder/ez-comfy-stack.git"
    )
    assert "__DOCS_GIT_REF__" not in out


def test_stamp_docs_git_ref_placeholder_development(
    hooks, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Development docs version stamps the placeholder to development."""
    monkeypatch.setenv("EZ_DOCS_VERSION", "development")
    text = "git clone -b __DOCS_GIT_REF__ https://example.invalid/repo.git"
    out = hooks.stamp_docs_git_ref_placeholder(text)
    assert "git clone -b development " in out
    assert "__DOCS_GIT_REF__" not in out


def test_stamp_docs_git_ref_placeholder_override(
    hooks, monkeypatch: pytest.MonkeyPatch
) -> None:
    """EZ_DOCS_GIT_REF wins when stamping the placeholder."""
    monkeypatch.setenv("EZ_DOCS_VERSION", "development")
    monkeypatch.setenv("EZ_DOCS_GIT_REF", "main")
    assert (
        hooks.stamp_docs_git_ref_placeholder("ref=__DOCS_GIT_REF__") == "ref=main"
    )


def test_stamp_docs_git_ref_placeholder_leaves_prose(
    hooks, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Literal branch names in prose are not rewritten without the placeholder."""
    monkeypatch.setenv("EZ_DOCS_VERSION", "latest")
    text = "Always branch from development; PR into development."
    assert hooks.stamp_docs_git_ref_placeholder(text) == text


def test_on_page_markdown_stamps_setup_clone(
    hooks, monkeypatch: pytest.MonkeyPatch
) -> None:
    """on_page_markdown stamps Setup-style clone -b and GitHub refs together."""
    monkeypatch.setenv("EZ_DOCS_VERSION", "development")
    md = (
        "```bash\n"
        "git clone -b __DOCS_GIT_REF__ "
        "https://github.com/toxicoder/ez-comfy-stack.git\n"
        "```\n"
        "see https://github.com/toxicoder/ez-comfy-stack/blob/main/README.md\n"
        "Always branch from development.\n"
    )
    out = hooks.on_page_markdown(md)
    assert "git clone -b development " in out
    assert "__DOCS_GIT_REF__" not in out
    assert (
        "https://github.com/toxicoder/ez-comfy-stack/blob/development/README.md"
        in out
    )
    assert "Always branch from development." in out


def test_on_page_markdown_stamps_main_for_latest(
    hooks, monkeypatch: pytest.MonkeyPatch
) -> None:
    """latest alias stamps the placeholder to main."""
    monkeypatch.setenv("EZ_DOCS_VERSION", "latest")
    out = hooks.on_page_markdown("git clone -b __DOCS_GIT_REF__ url")
    assert out == "git clone -b main url"


def test_on_post_page_stamps_placeholder(
    hooks, monkeypatch: pytest.MonkeyPatch
) -> None:
    """on_post_page replaces residual __DOCS_GIT_REF__ in rendered HTML."""
    monkeypatch.setenv("MIKE_DOCS_VERSION", "development")
    html = "<pre>git clone -b __DOCS_GIT_REF__ repo</pre><h1>Title</h1>"
    out = hooks.on_post_page(html)
    assert "git clone -b development " in out
    assert "__DOCS_GIT_REF__" not in out
    assert "ez-docs-dev-banner" in out


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
