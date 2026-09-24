from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "fixtures" / "synthetic"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def artifact_a(fixtures_dir: Path) -> Path:
    return fixtures_dir / "target_a"


@pytest.fixture
def artifact_b(fixtures_dir: Path) -> Path:
    return fixtures_dir / "target_b"


@pytest.fixture
def artifact_identical(fixtures_dir: Path) -> Path:
    return fixtures_dir / "target_identical"
