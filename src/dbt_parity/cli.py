"""Click CLI entrypoint for dbt-parity."""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

import click

from dbt_parity import __version__
from dbt_parity.artifacts import load_side_from_artifacts, observe_dbt_version, run_dbt_compile
from dbt_parity.compare import compare_sides
from dbt_parity.config import ParityConfig
from dbt_parity.report import render_human, render_json
from dbt_parity.secrets import assert_no_secrets, extract_secret_values


EXIT_OK = 0
EXIT_ACTIONABLE = 1
EXIT_ERROR = 2


@click.group()
@click.version_option(__version__, prog_name="dbt-parity")
def main() -> None:
    """Compare compiled SQL and schema/relation identifiers across two dbt targets."""


@main.command("compare")
@click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=".",
    show_default=True,
    help="dbt project root (used for compile mode and locating .dbtparity.yml).",
)
@click.option("--target-a", required=True, help="First dbt target name.")
@click.option("--target-b", required=True, help="Second dbt target name.")
@click.option(
    "--artifact-a",
    type=click.Path(path_type=Path),
    default=None,
    help="Pre-built target/ dir or manifest.json for side A (skip dbt compile).",
)
@click.option(
    "--artifact-b",
    type=click.Path(path_type=Path),
    default=None,
    help="Pre-built target/ dir or manifest.json for side B (skip dbt compile).",
)
@click.option(
    "--profiles-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Optional profiles directory passed through to dbt compile.",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to .dbtparity.yml (default: <project-dir>/.dbtparity.yml if present).",
)
@click.option("--json", "as_json", is_flag=True, help="Emit machine-readable JSON report.")
@click.option("--full-diff", is_flag=True, help="Do not truncate unified SQL diffs.")
def compare_cmd(
    project_dir: Path,
    target_a: str,
    target_b: str,
    artifact_a: Path | None,
    artifact_b: Path | None,
    profiles_dir: Path | None,
    config_path: Path | None,
    as_json: bool,
    full_diff: bool,
) -> None:
    """Compare two dbt targets (compile or reuse artifacts) and report parity."""
    code = _run_compare(
        project_dir=project_dir,
        target_a=target_a,
        target_b=target_b,
        artifact_a=artifact_a,
        artifact_b=artifact_b,
        profiles_dir=profiles_dir,
        config_path=config_path,
        as_json=as_json,
        full_diff=full_diff,
    )
    sys.exit(code)


def _run_compare(
    *,
    project_dir: Path,
    target_a: str,
    target_b: str,
    artifact_a: Path | None,
    artifact_b: Path | None,
    profiles_dir: Path | None,
    config_path: Path | None,
    as_json: bool,
    full_diff: bool,
) -> int:
    secrets: set[str] = set()
    if profiles_dir is not None:
        secrets |= extract_secret_values(profiles_dir / "profiles.yml")
    # Also scan common default without reading if missing
    home_profiles = Path.home() / ".dbt" / "profiles.yml"
    # Do not auto-load home secrets into filter unless profiles_dir points there;
    # only filter values from the profiles dir we were given.

    try:
        config = ParityConfig.load(project_dir, config_path)
    except (FileNotFoundError, ValueError) as exc:
        click.echo(f"error: {exc}", err=True)
        return EXIT_ERROR

    tmp_dirs: list[Path] = []
    try:
        path_a = artifact_a
        path_b = artifact_b

        if path_a is None:
            # Compile into an isolated target copy so A/B do not overwrite each other
            compiled = run_dbt_compile(project_dir, target_a, profiles_dir)
            path_a = _snapshot_target(compiled, tmp_dirs)
        if path_b is None:
            compiled = run_dbt_compile(project_dir, target_b, profiles_dir)
            path_b = _snapshot_target(compiled, tmp_dirs)

        side_a = load_side_from_artifacts("A", target_a, path_a)
        side_b = load_side_from_artifacts("B", target_b, path_b)

        # Fill dbt version from CLI if manifest lacked it
        observed = observe_dbt_version()
        if side_a.dbt_version is None:
            side_a.dbt_version = observed
        if side_b.dbt_version is None:
            side_b.dbt_version = observed

        result = compare_sides(
            side_a,
            side_b,
            config,
            tool_version=__version__,
            full_diff=full_diff,
        )
        output = render_json(result) if as_json else render_human(result)
        try:
            assert_no_secrets(output, secrets)
        except ValueError as exc:
            click.echo(f"error: {exc}", err=True)
            return EXIT_ERROR
        click.echo(output, nl=not as_json or True)
        return result.exit_code()
    except (FileNotFoundError, ValueError, RuntimeError, OSError) as exc:
        click.echo(f"error: {exc}", err=True)
        return EXIT_ERROR
    finally:
        for d in tmp_dirs:
            shutil.rmtree(d, ignore_errors=True)


def _snapshot_target(target_dir: Path, tmp_dirs: list[Path]) -> Path:
    dest = Path(tempfile.mkdtemp(prefix="dbt-parity-"))
    tmp_dirs.append(dest)
    # copytree into dest/target so structure is a target root with manifest.json
    shutil.copytree(target_dir, dest / "target")
    return dest / "target"


if __name__ == "__main__":
    main()
