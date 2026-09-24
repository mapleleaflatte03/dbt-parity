"""Compare two artifact sides and classify nodes."""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from typing import Literal

from dbt_parity.artifacts import ArtifactSide, NodeArtifact
from dbt_parity.config import ParityConfig

Classification = Literal["identical", "expected", "actionable", "one-sided"]

DEFAULT_DIFF_MAX_LINES = 40


@dataclass
class NodeComparison:
    unique_id: str
    name: str
    resource_type: str
    classification: Classification
    database_a: str | None = None
    schema_a: str | None = None
    alias_a: str | None = None
    relation_a: str | None = None
    database_b: str | None = None
    schema_b: str | None = None
    alias_b: str | None = None
    relation_b: str | None = None
    sql_sha256_a: str | None = None
    sql_sha256_b: str | None = None
    diff: str | None = None
    reason: str | None = None
    ignore_matched: bool = False


@dataclass
class CompareResult:
    target_a: str
    target_b: str
    tool_version: str
    dbt_version_a: str | None
    dbt_version_b: str | None
    nodes: list[NodeComparison] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def counts(self) -> dict[str, int]:
        out = {"identical": 0, "expected": 0, "actionable": 0, "one-sided": 0}
        for n in self.nodes:
            out[n.classification] = out.get(n.classification, 0) + 1
        return out

    @property
    def has_actionable(self) -> bool:
        return any(n.classification in {"actionable", "one-sided"} for n in self.nodes)

    def exit_code(self) -> int:
        return 1 if self.has_actionable else 0


def compare_sides(
    side_a: ArtifactSide,
    side_b: ArtifactSide,
    config: ParityConfig,
    tool_version: str,
    *,
    full_diff: bool = False,
    diff_max_lines: int = DEFAULT_DIFF_MAX_LINES,
) -> CompareResult:
    result = CompareResult(
        target_a=side_a.target_name,
        target_b=side_b.target_name,
        tool_version=tool_version,
        dbt_version_a=side_a.dbt_version,
        dbt_version_b=side_b.dbt_version,
        warnings=list(side_a.warnings) + list(side_b.warnings),
    )
    all_ids = sorted(set(side_a.nodes) | set(side_b.nodes))
    for uid in all_ids:
        na = side_a.nodes.get(uid)
        nb = side_b.nodes.get(uid)
        result.nodes.append(
            _compare_node(
                uid,
                na,
                nb,
                config,
                full_diff=full_diff,
                diff_max_lines=diff_max_lines,
            )
        )
    return result


def _compare_node(
    unique_id: str,
    na: NodeArtifact | None,
    nb: NodeArtifact | None,
    config: ParityConfig,
    *,
    full_diff: bool,
    diff_max_lines: int,
) -> NodeComparison:
    name = (na or nb).name  # type: ignore[union-attr]
    resource_type = (na or nb).resource_type  # type: ignore[union-attr]
    base = NodeComparison(
        unique_id=unique_id,
        name=name,
        resource_type=resource_type,
        classification="identical",
        database_a=na.database if na else None,
        schema_a=na.schema if na else None,
        alias_a=na.alias if na else None,
        relation_a=na.relation_label() if na else None,
        database_b=nb.database if nb else None,
        schema_b=nb.schema if nb else None,
        alias_b=nb.alias if nb else None,
        relation_b=nb.relation_label() if nb else None,
        sql_sha256_a=na.sql_sha256 if na else None,
        sql_sha256_b=nb.sql_sha256 if nb else None,
    )

    if config.node_ignored(unique_id, name):
        base.classification = "expected"
        base.ignore_matched = True
        base.reason = "matched ignore_nodes"
        if na and nb and na.compiled_sql is not None and nb.compiled_sql is not None:
            base.diff = _make_diff(na.compiled_sql, nb.compiled_sql, full_diff, diff_max_lines)
        return base

    if na is None or nb is None:
        base.classification = "one-sided"
        missing = "B" if na and not nb else "A"
        base.reason = f"node missing on side {missing}"
        return base

    schema_diff = (
        (na.database or "") != (nb.database or "")
        or (na.schema or "") != (nb.schema or "")
        or (na.alias or na.name) != (nb.alias or nb.name)
        or (na.relation_name or "") != (nb.relation_name or "")
    )
    sql_a = na.compiled_sql
    sql_b = nb.compiled_sql
    sql_diff = False
    if sql_a is None and sql_b is None:
        sql_diff = False
    elif sql_a is None or sql_b is None:
        sql_diff = True
        base.reason = "compiled SQL missing on one side"
    else:
        sql_diff = sql_a != sql_b
        if sql_diff:
            base.diff = _make_diff(sql_a, sql_b, full_diff, diff_max_lines)

    if not schema_diff and not sql_diff:
        base.classification = "identical"
        return base

    # SQL-only expected via regex (when schema also differs, still actionable unless node ignored)
    if sql_diff and sql_a is not None and sql_b is not None and config.sql_diff_is_expected(sql_a, sql_b):
        if not schema_diff:
            base.classification = "expected"
            base.ignore_matched = True
            base.reason = "matched ignore_sql_regex"
            return base
        # Schema still differs → actionable, note that SQL ignore matched partially
        base.classification = "actionable"
        base.reason = "schema/relation differs (SQL ignore matched but relation still drifts)"
        return base

    base.classification = "actionable"
    reasons = []
    if schema_diff:
        reasons.append("schema/relation differs")
    if sql_diff:
        reasons.append("compiled SQL differs")
    base.reason = "; ".join(reasons) or "differs"
    return base


def _make_diff(sql_a: str, sql_b: str, full_diff: bool, max_lines: int) -> str:
    lines = list(
        difflib.unified_diff(
            sql_a.splitlines(),
            sql_b.splitlines(),
            fromfile="target-a",
            tofile="target-b",
            lineterm="",
        )
    )
    if full_diff or len(lines) <= max_lines:
        return "\n".join(lines)
    truncated = lines[:max_lines]
    truncated.append(f"... truncated {len(lines) - max_lines} more lines; pass --full-diff for complete diff")
    return "\n".join(truncated)
