"""Loads relocated legacy prompt constants without importing evolution.prompts."""

from __future__ import annotations

from pathlib import Path

_LEGACY_DIR = Path(__file__).resolve().parent.parent / "prompts" / "legacy"


def load_legacy_prompt(name: str) -> str:
    return (_LEGACY_DIR / f"{name}.md").read_text(encoding="utf-8")
