"""Load and apply .dbtparity.yml ignore / allow rules."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ParityConfig:
    """Project-level ignore rules for expected divergence."""

    ignore_nodes: list[str] = field(default_factory=list)
    ignore_sql_regex: list[str] = field(default_factory=list)
    source_path: Path | None = None

    @classmethod
    def empty(cls) -> "ParityConfig":
        return cls()

    @classmethod
    def load(cls, project_dir: Path, explicit: Path | None = None) -> "ParityConfig":
        """Load config from explicit path or project_dir/.dbtparity.yml."""
        path = explicit
        if path is None:
            candidate = project_dir / ".dbtparity.yml"
            if candidate.is_file():
                path = candidate
            else:
                return cls.empty()
        if not path.is_file():
            raise FileNotFoundError(f"Config file not found: {path}")
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML in {path}: {exc}") from exc
        if not isinstance(raw, dict):
            raise ValueError(f"Config root must be a mapping: {path}")
        ignore_nodes = _as_str_list(raw.get("ignore_nodes"), "ignore_nodes", path)
        ignore_sql_regex = _as_str_list(raw.get("ignore_sql_regex"), "ignore_sql_regex", path)
        # Validate regexes early
        for pattern in ignore_sql_regex:
            try:
                re.compile(pattern)
            except re.error as exc:
                raise ValueError(f"Invalid ignore_sql_regex in {path}: {pattern!r}: {exc}") from exc
        return cls(
            ignore_nodes=ignore_nodes,
            ignore_sql_regex=ignore_sql_regex,
            source_path=path,
        )

    def node_ignored(self, unique_id: str, name: str) -> bool:
        for pattern in self.ignore_nodes:
            if fnmatch.fnmatch(unique_id, pattern) or fnmatch.fnmatch(name, pattern):
                return True
        return False

    def sql_diff_is_expected(self, sql_a: str, sql_b: str) -> bool:
        """True if removing ignore_sql_regex matches leaves both sides equal."""
        if not self.ignore_sql_regex:
            return False
        stripped_a = sql_a
        stripped_b = sql_b
        for pattern in self.ignore_sql_regex:
            stripped_a = re.sub(pattern, "", stripped_a)
            stripped_b = re.sub(pattern, "", stripped_b)
        return _normalize_ws(stripped_a) == _normalize_ws(stripped_b)


def _as_str_list(value: Any, key: str, path: Path) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list in {path}")
    out: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"{key} entries must be strings in {path}")
        out.append(item)
    return out


def _normalize_ws(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()
