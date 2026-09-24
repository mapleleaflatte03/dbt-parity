from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from dbt_parity.cli import main
from dbt_parity.compare import compare_sides
from dbt_parity.config import ParityConfig
from dbt_parity.artifacts import load_side_from_artifacts


def test_actionable_drift(artifact_a: Path, artifact_b: Path):
    side_a = load_side_from_artifacts("A", "dev", artifact_a)
    side_b = load_side_from_artifacts("B", "prod", artifact_b)
    result = compare_sides(side_a, side_b, ParityConfig.empty(), tool_version="test")
    by_id = {n.unique_id: n for n in result.nodes}
    assert by_id["model.demo_project.orders"].classification == "actionable"
    assert by_id["model.demo_project.prod_only_audit"].classification == "one-sided"
    assert result.exit_code() == 1


def test_ignore_sql_regex_marks_expected(artifact_a: Path, artifact_b: Path, tmp_path: Path):
    # Schema still differs on customers — for pure SQL expected we need same schema
    # Build a B twin that only differs by the date filter SQL, same schema labels.
    import shutil
    import copy

    b2 = tmp_path / "target_b_sql_only"
    shutil.copytree(artifact_a, b2)
    manifest = json.loads((b2 / "manifest.json").read_text())
    node = manifest["nodes"]["model.demo_project.customers"]
    node["compiled_code"] = "select id, email from raw.users\n"
    (b2 / "compiled" / "demo_project" / "models" / "customers.sql").write_text(
        node["compiled_code"], encoding="utf-8"
    )
    (b2 / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    cfg = ParityConfig(
        ignore_sql_regex=[r"where\s+_loaded_at\s*>\s*current_date\s*-\s*7"],
    )
    side_a = load_side_from_artifacts("A", "dev", artifact_a)
    side_b = load_side_from_artifacts("B", "prod", b2)
    result = compare_sides(side_a, side_b, cfg, tool_version="test")
    cust = next(n for n in result.nodes if n.name == "customers")
    assert cust.classification == "expected"
    assert result.exit_code() == 0


def test_ignore_nodes_marks_expected(artifact_a: Path, artifact_b: Path):
    cfg = ParityConfig(ignore_nodes=["model.demo_project.orders", "prod_only_audit", "unique_*"])
    side_a = load_side_from_artifacts("A", "dev", artifact_a)
    side_b = load_side_from_artifacts("B", "prod", artifact_b)
    result = compare_sides(side_a, side_b, cfg, tool_version="test")
    by_id = {n.unique_id: n for n in result.nodes}
    assert by_id["model.demo_project.orders"].classification == "expected"
    assert by_id["model.demo_project.prod_only_audit"].classification == "expected"
    # customers still has schema+sql diff → actionable unless ignored
    assert by_id["model.demo_project.customers"].classification == "actionable"


def test_identical_exit_zero(artifact_a: Path, artifact_identical: Path):
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "compare",
            "--project-dir",
            str(artifact_a.parent),
            "--target-a",
            "dev",
            "--target-b",
            "dev2",
            "--artifact-a",
            str(artifact_a),
            "--artifact-b",
            str(artifact_identical),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "actionable=0" in result.output


def test_cli_actionable_exit_one(artifact_a: Path, artifact_b: Path):
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "compare",
            "--target-a",
            "dev",
            "--target-b",
            "prod",
            "--artifact-a",
            str(artifact_a),
            "--artifact-b",
            str(artifact_b),
            "--json",
        ],
    )
    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["counts"]["actionable"] >= 1
    assert payload["tool_version"]
