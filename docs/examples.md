# Examples

## Compare synthetic fixtures (ships with the repo)

```bash
dbt-parity compare \
  --target-a dev \
  --target-b prod \
  --artifact-a fixtures/synthetic/target_a \
  --artifact-b fixtures/synthetic/target_b
```

Expect exit code `1` with `actionable` orders drift and a `one-sided` prod-only model.

## Ignore intentional non-prod SQL limits

`.dbtparity.yml`:

```yaml
ignore_sql_regex:
  - "where\\s+_loaded_at\\s*>\\s*current_date\\s*-\\s*\\d+"
ignore_nodes:
  - "prod_only_audit"
```

```bash
dbt-parity compare \
  --project-dir . \
  --target-a dev \
  --target-b prod \
  --artifact-a path/to/dev/target \
  --artifact-b path/to/prod/target
```

## JSON for CI

```bash
dbt-parity compare --target-a a --target-b b \
  --artifact-a ./ta --artifact-b ./tb --json > report.json
echo $?   # 0 / 1 / 2
```
