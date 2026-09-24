# Changelog

## 0.1.0-rc.1 — 2026-09-24

Initial release candidate.

- CLI: `dbt-parity compare` with compile mode and `--artifact-a` / `--artifact-b`
- Classifications: `identical` | `expected` | `actionable` | `one-sided`
- `.dbtparity.yml` with `ignore_nodes` and `ignore_sql_regex`
- Exit codes 0 / 1 / 2; human + `--json` reports
- Synthetic fixtures + pytest suite (no warehouse required)
- Docs: README, configuration, troubleshooting, examples
- Safe defaults: no secret logging from profiles; no phone-home
