# Contributing

## Setup

```bash
python -m pip install -e ".[dev]"
pytest
```

## Scope

Please keep changes inside the v0 CLI surface: local two-target / artifact compare, ignore rules, exit codes, docs. Do not add data-diff engines, Cloud Admin API clients, or UI dashboards without a maintainer decision.

## Tests

- Prefer synthetic `fixtures/synthetic/` artifacts (no warehouse)
- Assert exit codes `0` / `1` / `2`
- Assert profile secrets never appear in default stdout/JSON

## License

By contributing you agree your contributions are licensed under Apache-2.0.
