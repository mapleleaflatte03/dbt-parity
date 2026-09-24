"""Load dbt compile artifacts (manifest.json + compiled SQL)."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


COMPARABLE_RESOURCE_TYPES = frozenset({"model", "test", "unit_test", "snapshot", "seed"})


@dataclass
class NodeArtifact:
    unique_id: str
    name: str
    resource_type: str
    database: str | None = None
    schema: str | None = None
    alias: str | None = None
    relation_name: str | None = None
    compiled_sql: str | None = None
    compiled_path: str | None = None
    package_name: str | None = None

    @property
    def sql_sha256(self) -> str | None:
        if self.compiled_sql is None:
            return None
        return hashlib.sha256(self.compiled_sql.encode("utf-8")).hexdigest()

    def relation_label(self) -> str | None:
        if self.relation_name:
            return self.relation_name
        parts = [p for p in (self.database, self.schema, self.alias or self.name) if p]
        return ".".join(parts) if parts else None


@dataclass
class ArtifactSide:
    label: str
    target_name: str
    root: Path
    nodes: dict[str, NodeArtifact] = field(default_factory=dict)
    dbt_version: str | None = None
    manifest_path: Path | None = None
    warnings: list[str] = field(default_factory=list)


def resolve_artifact_root(path: Path) -> Path:
    """Accept a target/ dir or a path to manifest.json; return the target dir."""
    path = path.resolve()
    if path.is_file() and path.name == "manifest.json":
        return path.parent
    if path.is_dir():
        if (path / "manifest.json").is_file():
            return path
        # Maybe user passed project root with target/
        if (path / "target" / "manifest.json").is_file():
            return path / "target"
        raise FileNotFoundError(f"No manifest.json under {path}")
    raise FileNotFoundError(f"Artifact path not found: {path}")


def load_side_from_artifacts(label: str, target_name: str, artifact_path: Path) -> ArtifactSide:
    root = resolve_artifact_root(artifact_path)
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"manifest.json missing at {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Unreadable manifest.json at {manifest_path}: {exc}") from exc

    meta = manifest.get("metadata") or {}
    dbt_version = meta.get("dbt_version") or meta.get("dbt_schema_version")
    nodes_raw: dict[str, Any] = dict(manifest.get("nodes") or {})
    # Some manifests put unit tests separately; keep nodes only for v0
    side = ArtifactSide(
        label=label,
        target_name=target_name,
        root=root,
        dbt_version=str(dbt_version) if dbt_version else None,
        manifest_path=manifest_path,
    )

    for unique_id, node in nodes_raw.items():
        resource_type = node.get("resource_type") or ""
        if resource_type not in COMPARABLE_RESOURCE_TYPES:
            continue
        compiled_sql = _extract_compiled_sql(node, root)
        # Include tests/models when we have compiled SQL or a node entry with relation info
        if compiled_sql is None and resource_type == "test":
            # Still include if node exists (one-sided detection); SQL may be absent
            pass
        art = NodeArtifact(
            unique_id=unique_id,
            name=node.get("name") or unique_id.split(".")[-1],
            resource_type=resource_type,
            database=node.get("database"),
            schema=node.get("schema"),
            alias=node.get("alias"),
            relation_name=node.get("relation_name"),
            compiled_sql=compiled_sql,
            compiled_path=node.get("compiled_path"),
            package_name=node.get("package_name"),
        )
        # Prefer nodes that have compiled SQL or are models/tests present
        if art.compiled_sql is not None or resource_type in {"model", "test", "snapshot"}:
            side.nodes[unique_id] = art

    if not side.nodes:
        side.warnings.append(
            f"{label}: no comparable compiled nodes found under {root} "
            "(need models/tests with compiled SQL or node metadata)"
        )
    return side


def _extract_compiled_sql(node: dict[str, Any], target_root: Path) -> str | None:
    # Prefer in-manifest compiled field when present
    for key in ("compiled_code", "compiled_sql", "compiled"):
        val = node.get(key)
        if isinstance(val, str) and val.strip():
            return val
    compiled_path = node.get("compiled_path")
    if compiled_path:
        candidates = [
            target_root / compiled_path,
            target_root.parent / compiled_path,
            Path(compiled_path),
        ]
        for cand in candidates:
            if cand.is_file():
                return cand.read_text(encoding="utf-8")
    # Heuristic: target/compiled/<package>/... matching unique_id path
    unique_id = node.get("unique_id") or ""
    # unique_id like model.pkg.name → look under compiled/pkg/
    package = node.get("package_name")
    original_path = node.get("original_file_path") or node.get("path")
    if package and original_path:
        cand = target_root / "compiled" / package / original_path
        if cand.is_file():
            return cand.read_text(encoding="utf-8")
        # .sql extension if missing
        if not str(original_path).endswith(".sql"):
            cand2 = Path(str(cand) + ".sql")
            if cand2.is_file():
                return cand2.read_text(encoding="utf-8")
    # Last resort: search compiled tree by name
    name = node.get("name")
    if name and (target_root / "compiled").is_dir():
        matches = list((target_root / "compiled").rglob(f"{name}.sql"))
        if len(matches) == 1:
            return matches[0].read_text(encoding="utf-8")
    return None


def run_dbt_compile(project_dir: Path, target: str, profiles_dir: Path | None = None) -> Path:
    """Run `dbt compile --target` and return the project's target/ directory."""
    cmd = ["dbt", "compile", "--project-dir", str(project_dir), "--target", target]
    if profiles_dir is not None:
        cmd.extend(["--profiles-dir", str(profiles_dir)])
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(project_dir),
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "dbt executable not found on PATH. Install dbt-core + adapter, "
            "or pass --artifact-a / --artifact-b to compare pre-built targets."
        ) from exc
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-20:]
        raise RuntimeError(
            f"dbt compile failed for target {target!r} (exit {proc.returncode}). "
            f"stderr/stdout tail:\n" + "\n".join(tail)
        )
    target_dir = project_dir / "target"
    if not (target_dir / "manifest.json").is_file():
        raise RuntimeError(
            f"dbt compile for target {target!r} succeeded but {target_dir / 'manifest.json'} missing"
        )
    return target_dir


def observe_dbt_version() -> str | None:
    try:
        proc = subprocess.run(
            ["dbt", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return None
    if proc.returncode != 0:
        return None
    # Prefer first line mentioning installed version
    text = (proc.stdout or "").strip()
    for line in text.splitlines():
        if "installed version" in line.lower() or line.lower().startswith("core:"):
            return line.strip()
    return text.splitlines()[0].strip() if text else None
