# Security Policy

## Supported versions

Report issues against the latest `main` / published RC of `dbt-parity`.

## Reporting a vulnerability

Use GitHub security advisories on https://github.com/mapleleaflatte03/dbt-parity (Security tab → Advisories). Do not file public issues that include secrets or live credentials.

## Design defaults (v0)

- Credentials are read only through the operator’s existing dbt `profiles.yml` / environment when running live `dbt compile`. This tool does not upload profiles or SQL to a remote service by default (no phone-home).
- Human and `--json` reports redact common secret-looking substrings; still never paste real credentials into fixtures or tickets.
- Trust boundary: local process inherits the same warehouse access as `dbt compile` for the operator who runs it.

## Dependencies

Dependency risk is skimmed at RC time via direct deps in `pyproject.toml`. Re-check before any public RELEASE.
