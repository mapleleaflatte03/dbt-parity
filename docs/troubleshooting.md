# Troubleshooting

## `error: dbt executable not found`

Install dbt-core and your adapter, **or** pass `--artifact-a` / `--artifact-b` to compare pre-built `target/` directories without calling dbt.

## `dbt compile failed for target …`

- Confirm the target exists in `profiles.yml`
- Confirm warehouse connectivity (same as a manual `dbt compile --target …`)
- Read the stderr tail printed by dbt-parity for adapter errors

## `No manifest.json under …`

`--artifact-*` must point at a `target/` directory containing `manifest.json`, or directly at `manifest.json`.

## Many `one-sided` nodes

Often means one side compiled a subset (selector, partial parse, or different package versions). Recompile both sides with the same selection, or ignore intentional nodes via `.dbtparity.yml`.

## Introspective macros

Macros that query the warehouse at compile/run time can differ across environments even when project code matches. Prefer artifact comparison from the environments you care about, and document expected branches with ignore rules.

## Secrets in output

dbt-parity does not print profile passwords. If you pipe custom scripts that dump `profiles.yml`, that is outside this tool. Open an issue if a secret string from `--profiles-dir` appears in default stdout/JSON.
