# dbt-parity

Compare **compiled SQL** and **schema / relation identifiers** across two dbt targets so analytics engineers can catch IDE ↔ deploy drift before (or after) a job fails.

**Version:** `0.1.0-rc.1` (release candidate — not published to PyPI yet)

## Who this is for

Analytics engineers on **dbt-core** and/or **dbt Cloud** who run staged schemas and deploy jobs, and who debug environment mismatches via compiled SQL under `target/`.

## Install (development)

```bash
git clone https://github.com/mapleleaflatte03/dbt-parity.git
cd dbt-parity
python -m pip install -e ".[dev]"
```

PyPI publish is **not** done for this RC. A future `pip install dbt-parity` path may follow a separate release decision.

## Quickstart

### Artifact mode (no warehouse / no live `dbt compile`)

Useful for CI fixtures and for comparing a local `target/` against a downloaded job artifact:

```bash
dbt-parity compare \
  --target-a dev \
  --target-b prod \
  --artifact-a fixtures/synthetic/target_a \
  --artifact-b fixtures/synthetic/target_b
```

### Two-target compile mode

Requires `dbt` on PATH plus a warehouse connection via your existing `profiles.yml`:

```bash
dbt-parity compare \
  --project-dir /path/to/dbt/project \
  --target-a dev \
  --target-b prod
```

Machine-readable output:

```bash
dbt-parity compare ... --json
```

Full SQL diffs (default is truncated):

```bash
dbt-parity compare ... --full-diff
```

## Exit codes

| Code | Meaning |
|-----:|---------|
| 0 | No actionable drift (only `identical` and/or `expected`) |
| 1 | ≥1 `actionable` or `one-sided` node |
| 2 | Tool / config / dbt error (missing artifact, bad YAML, compile failure) |

## Classifications

Per node: `identical` · `expected` (matched ignore rule) · `actionable` · `one-sided`.

Configure expected divergence in `.dbtparity.yml` at the project root. See [docs/configuration.md](docs/configuration.md).

## Architecture

See [docs/architecture.md](docs/architecture.md).

## Non-goals (v0)

- Not a warehouse **data-diff** / row-content parity tool
- Not a **dbt Cloud** replacement or Cloud IDE plugin
- Not a **`state:modified` / Slim CI** dashboard
- Does **not** re-implement the dbt compiler (wraps `dbt compile` or reads artifacts)
- No Cloud Administrative API fetch in v0

## Absorption kill

If dbt Labs ships a **first-party** IDE ↔ job **compiled SQL and schema/relation parity** comparison that removes the need for a third-party CLI for the users above, this project may be **archived**. Reassess against public docs / release notes.

## Security (safe defaults by design)

- Uses the operator’s existing local dbt profiles when compiling; does not invent a credential store
- Does **not** log password / token / key values from profiles
- Does **not** phone home or upload profiles / SQL by default
- Same trust boundary as running `dbt compile` yourself

## Coverage limits

- Live compile needs a working warehouse connection and adapter
- Introspective / data-dependent macros may produce incomplete or environment-skewed compiled SQL — treat reports with that caveat
- Adapter or dbt-version skew between sides is reported when metadata is available; resolving skew is out of scope for the CLI

## Docs

- [Configuration](docs/configuration.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Examples](docs/examples.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## CI

A pytest workflow template ships at [`ci/github-actions-ci.yml`](ci/github-actions-ci.yml).
Copy it to `.github/workflows/ci.yml` when the pushing credential has the GitHub `workflow` scope
(current `gh` OAuth token for mapleleaflatte03 does not). Local tests: `pytest` after `pip install -e ".[dev]"`.

## License

Apache-2.0 — see [LICENSE](LICENSE).
