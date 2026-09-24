# Configuration (`.dbtparity.yml`)

Place `.dbtparity.yml` in the dbt project root (or pass `--config PATH`).

```yaml
# Nodes matching these globs (unique_id or name) are classified `expected`.
ignore_nodes:
  - "model.my_project.dev_only_*"
  - "prod_only_audit"

# If BOTH sides' SQL become equal after removing matches of these regexes
# (and schema/relation identifiers also match), classify `expected`.
# If schema/relation still differs, the node stays `actionable`.
ignore_sql_regex:
  - "where\\s+_loaded_at\\s*>\\s*current_date\\s*-\\s*\\d+"
  - "(?i)limit\\s+\\d+"
```

## Semantics

| Rule | Effect |
|------|--------|
| `ignore_nodes` | Entire node → `expected` (including one-sided) |
| `ignore_sql_regex` | Strip regex matches from both SQL strings; if remaining SQL equal **and** relation identifiers equal → `expected` |

Unmatched compiled-SQL or schema/relation differences default to **`actionable`**.

## CLI overrides

- `--config PATH` — explicit config file
- `--full-diff` — do not truncate unified diffs
- `--json` — machine JSON with the same classifications
