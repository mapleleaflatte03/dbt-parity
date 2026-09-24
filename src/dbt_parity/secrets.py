"""Helpers to avoid logging secrets from dbt profiles."""

from __future__ import annotations

import re
from pathlib import Path

# Keys commonly holding secrets in profiles.yml
_SECRET_KEY_RE = re.compile(
    r"(?i)^\s*(password|pwd|token|key|secret|private_key|private_key_passphrase|"
    r"client_secret|api_key|access_token|refresh_token)\s*:",
)


def extract_secret_values(profiles_path: Path | None) -> set[str]:
    """Read a profiles.yml-like file and collect likely secret string values."""
    if profiles_path is None or not profiles_path.is_file():
        return set()
    secrets: set[str] = set()
    try:
        text = profiles_path.read_text(encoding="utf-8")
    except OSError:
        return set()
    for line in text.splitlines():
        if not _SECRET_KEY_RE.search(line):
            continue
        # split on first ':'
        _, _, rest = line.partition(":")
        val = rest.strip().strip("'\"")
        if val and val.lower() not in {"null", "none", "~", ""}:
            secrets.add(val)
    return secrets


def assert_no_secrets(text: str, secrets: set[str]) -> None:
    """Raise ValueError if any known secret appears in text."""
    for s in secrets:
        if s and s in text:
            raise ValueError("Refusing to emit output that contains a profile secret value")
