from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from dbt_parity.cli import main
from dbt_parity.secrets import extract_secret_values


SECRET = "SuperSecretPassword_xyz_99"


def test_secrets_not_in_stdout_or_json(artifact_a: Path, artifact_b: Path, tmp_path: Path):
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    (profiles_dir / "profiles.yml").write_text(
        f"""
demo:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      user: joe
      password: {SECRET}
      dbname: analytics
      schema: public
""".lstrip(),
        encoding="utf-8",
    )
    assert SECRET in extract_secret_values(profiles_dir / "profiles.yml")

    runner = CliRunner()
    for as_json in (False, True):
        args = [
            "compare",
            "--target-a",
            "dev",
            "--target-b",
            "prod",
            "--artifact-a",
            str(artifact_a),
            "--artifact-b",
            str(artifact_b),
            "--profiles-dir",
            str(profiles_dir),
        ]
        if as_json:
            args.append("--json")
        result = runner.invoke(main, args)
        combined = (result.output or "") + (result.stderr or "")
        assert SECRET not in combined, f"secret leaked in {'json' if as_json else 'human'} output"
