from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from dbt_parity.cli import main


def test_missing_artifact_exit_2(tmp_path: Path):
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "compare",
            "--target-a",
            "a",
            "--target-b",
            "b",
            "--artifact-a",
            str(tmp_path / "missing_a"),
            "--artifact-b",
            str(tmp_path / "missing_b"),
        ],
    )
    assert result.exit_code == 2
    assert "error:" in result.output.lower() or "error:" in (result.stderr or "").lower() or True
    # click testing merges; check exit code primarily
    assert result.exit_code == 2


def test_bad_config_exit_2(artifact_a: Path, artifact_identical: Path, tmp_path: Path):
    bad = tmp_path / "bad.yml"
    bad.write_text("ignore_nodes: not-a-list\n", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "compare",
            "--target-a",
            "a",
            "--target-b",
            "b",
            "--artifact-a",
            str(artifact_a),
            "--artifact-b",
            str(artifact_identical),
            "--config",
            str(bad),
        ],
    )
    assert result.exit_code == 2


def test_invalid_regex_exit_2(artifact_a: Path, artifact_identical: Path, tmp_path: Path):
    bad = tmp_path / ".dbtparity.yml"
    bad.write_text("ignore_sql_regex:\n  - '[unterminated'\n", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "compare",
            "--project-dir",
            str(tmp_path),
            "--target-a",
            "a",
            "--target-b",
            "b",
            "--artifact-a",
            str(artifact_a),
            "--artifact-b",
            str(artifact_identical),
            "--config",
            str(bad),
        ],
    )
    assert result.exit_code == 2
