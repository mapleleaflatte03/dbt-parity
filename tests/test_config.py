from __future__ import annotations

from pathlib import Path

import pytest

from dbt_parity.config import ParityConfig


def test_load_config(tmp_path: Path):
    cfg_path = tmp_path / ".dbtparity.yml"
    cfg_path.write_text(
        """
ignore_nodes:
  - "model.*.staging_*"
  - "my_test"
ignore_sql_regex:
  - "limit\\\\s+\\\\d+"
""".lstrip(),
        encoding="utf-8",
    )
    cfg = ParityConfig.load(tmp_path)
    assert cfg.node_ignored("model.x.staging_users", "staging_users")
    assert cfg.node_ignored("test.x.my_test", "my_test")
    assert not cfg.node_ignored("model.x.orders", "orders")
    assert cfg.sql_diff_is_expected("select 1 limit 10", "select 1")


def test_missing_explicit_config_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        ParityConfig.load(tmp_path, tmp_path / "nope.yml")
