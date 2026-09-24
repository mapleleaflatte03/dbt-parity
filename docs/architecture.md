# Architecture (v0)

`dbt-parity` is a thin local CLI. It does **not** re-implement the dbt compiler.

```
CLI (click)
  → load config (.dbtparity.yml)
  → obtain artifacts per side
       • live: subprocess `dbt compile --target …`
       • or: read pre-built target/ / manifest.json
  → load nodes (models + tests) from manifest + compiled SQL files
  → compare schema/relation + SQL hashes; apply ignore rules
  → emit human or JSON report + exit code 0|1|2
```

Modules under `src/dbt_parity/`:

| Module | Role |
|--------|------|
| `cli.py` | Argument parsing, orchestration, exit codes |
| `artifacts.py` | Compile subprocess + artifact directory / manifest load |
| `compare.py` | Node pairing, classification |
| `config.py` | `.dbtparity.yml` load/validate |
| `report.py` | Human + JSON rendering |
| `secrets.py` | Redaction helpers for stdout/JSON |

Out of v0: Cloud Admin API, data-diff, UI, `state:modified` dashboards.
