# Changelog

## 0.1.0-rc.2 — 2026-09-24

- Version metadata aligned to `0.1.0-rc.2`
- GitHub Actions CI active at `.github/workflows/ci.yml` (pytest on push/PR)
- README CI section updated to match active workflow

## 0.1.0-rc.1 — 2026-09-24

Initial release candidate.

- CLI: `dbt-parity compare` with compile mode and `--artifact-a` / `--artifact-b`
- Classifications: `identical` | `expected` | `actionable` | `one-sided`
- `.dbtparity.yml` with `ignore_nodes` and `ignore_sql_regex`
- Exit codes 0 / 1 / 2; human + `--json` reports
- Synthetic fixtures + pytest suite (no warehouse required)
- Docs: README, configuration, troubleshooting, examples
- Safe defaults: no secret logging from profiles; no phone-home
