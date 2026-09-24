"""Render human and JSON parity reports (never echo secrets)."""

from __future__ import annotations

import json
from typing import Any

from dbt_parity.compare import CompareResult, NodeComparison


def result_to_dict(result: CompareResult) -> dict[str, Any]:
    return {
        "tool_version": result.tool_version,
        "target_a": result.target_a,
        "target_b": result.target_b,
        "dbt_version_a": result.dbt_version_a,
        "dbt_version_b": result.dbt_version_b,
        "counts": result.counts,
        "warnings": list(result.warnings),
        "nodes": [_node_to_dict(n) for n in result.nodes],
    }


def _node_to_dict(n: NodeComparison) -> dict[str, Any]:
    return {
        "unique_id": n.unique_id,
        "name": n.name,
        "resource_type": n.resource_type,
        "classification": n.classification,
        "database_a": n.database_a,
        "schema_a": n.schema_a,
        "alias_a": n.alias_a,
        "relation_a": n.relation_a,
        "database_b": n.database_b,
        "schema_b": n.schema_b,
        "alias_b": n.alias_b,
        "relation_b": n.relation_b,
        "sql_sha256_a": n.sql_sha256_a,
        "sql_sha256_b": n.sql_sha256_b,
        "diff": n.diff,
        "reason": n.reason,
        "ignore_matched": n.ignore_matched,
    }


def render_json(result: CompareResult) -> str:
    return json.dumps(result_to_dict(result), indent=2, sort_keys=False)


def render_human(result: CompareResult) -> str:
    lines: list[str] = []
    lines.append(f"dbt-parity {result.tool_version}")
    lines.append(f"Comparing targets: {result.target_a!r} vs {result.target_b!r}")
    if result.dbt_version_a or result.dbt_version_b:
        lines.append(
            f"Observed dbt: A={result.dbt_version_a or 'unknown'} | "
            f"B={result.dbt_version_b or 'unknown'}"
        )
    counts = result.counts
    lines.append(
        "Summary: "
        f"identical={counts['identical']} expected={counts['expected']} "
        f"actionable={counts['actionable']} one-sided={counts['one-sided']}"
    )
    for w in result.warnings:
        lines.append(f"WARNING: {w}")
    lines.append("")

    interesting = [n for n in result.nodes if n.classification != "identical"]
    if not interesting:
        lines.append("No differences.")
        return "\n".join(lines)

    for n in interesting:
        lines.append(f"[{n.classification}] {n.unique_id} ({n.resource_type})")
        if n.reason:
            lines.append(f"  reason: {n.reason}")
        if n.relation_a or n.relation_b:
            lines.append(f"  relation A: {n.relation_a or '-'}")
            lines.append(f"  relation B: {n.relation_b or '-'}")
        if n.sql_sha256_a or n.sql_sha256_b:
            sha_a = (n.sql_sha256_a or "-")[:12]
            sha_b = (n.sql_sha256_b or "-")[:12]
            lines.append(f"  sql sha256: A={sha_a}… B={sha_b}…")
        if n.diff:
            lines.append("  diff:")
            for dl in n.diff.splitlines():
                lines.append(f"    {dl}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
