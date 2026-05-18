# Pipeflight

**A black box recorder for data pipelines.**

Most data quality tools tell you that something failed. Pipeflight preserves the evidence you need to debug it later: failing rows, schema snapshot, stats, report, and a replay script.

```bash
pipeflight record orders.parquet --key order_id --contract orders.contract.json
```

Pipeflight creates a small incident folder:

```text
incident_2026_05_18_112233/
  manifest.json
  failing_rows.parquet
  schema.json
  stats.json
  replay.py
  report.html
```

You can attach that folder to a ticket, send it to another engineer, or replay it locally without sharing the full source dataset.

## What Problem Does It Solve?

When a production data pipeline fails, the original dataset can be huge, sensitive, temporary, or already overwritten. The team may know that validation failed, but not have the exact rows, schema, or stats needed to reproduce the incident.

Pipeflight records a compact evidence bundle at failure time so debugging is reproducible.

It helps answer:

- Which exact rows failed validation?
- Which rule failed?
- What did the schema look like?
- How many rows were scanned?
- Was the timestamp data stale?
- Can another engineer replay the incident locally?

## How It Works

```text
Dataset + optional contract
       |
       v
pipeflight record orders.parquet --key order_id --contract orders.contract.json
       |
       v
Incident bundle
  |-- manifest.json
  |-- failing_rows.parquet
  |-- schema.json
  |-- stats.json
  |-- replay.py
  `-- report.html
       |
       v
pipeflight replay incident_2026_05_18_112233
       |
       v
Reproducible debugging
```

## Input And Output

### Input

Pipeflight accepts:

- CSV files: `.csv`
- JSON Lines files: `.jsonl` or `.ndjson`
- Parquet files: `.parquet`
- optional contract files: JSON, or YAML when installed with `pipeflight[yaml]`
- optional key column: used to detect missing identifiers

Example:

```bash
pipeflight record examples/validation_matrix.csv --key order_id --contract examples/validation_matrix.contract.json --out incident_validation_matrix
```

### Output

Pipeflight writes an incident directory containing:

- `manifest.json`: run metadata, status, source path, row count, violation count
- `failing_rows.parquet`: only the rows that failed validation
- `schema.json`: inferred column types
- `stats.json`: row count, null counts, min/max values, max datetimes
- `report.html`: human-readable incident report
- `replay.py`: tiny script for replaying the incident folder

Example output:

```text
recorded incident_validation_matrix status=failed rows=13 violations=16
```

## Why Pipeflight?

Existing tools are good at detection. But when a pipeline fails in production, engineers often still ask:

- Which exact rows caused this?
- What did the schema look like at failure time?
- How many rows were scanned?
- Can another engineer reproduce the incident locally?
- Can this evidence be attached to a ticket without copying the whole dataset?

Pipeflight focuses on **incident reproducibility + replay**.

## Why This Exists

In many production incidents, teams know a dataset failed validation, but they cannot reproduce the exact conditions that caused the failure later.

Pipeflight was created to preserve small, shareable evidence bundles so data incidents can be debugged quickly and collaboratively.

## Who Is This For?

- Data engineers debugging pipeline failures.
- ML engineers investigating corrupted training data.
- Platform teams tracking schema drift.
- CI/CD workflows that validate data before promotion.
- Incident response teams that need reproducible evidence.

## Pipeflight vs Traditional Data Quality Tools

Traditional tools usually focus on:

- detection
- monitoring
- dashboards
- long-running observability

Pipeflight focuses on:

- reproducibility
- evidence preservation
- replayable incidents
- forensic debugging

It is intentionally small in v0.1. No dashboards, no orchestration, no RBAC, no distributed system. Just a clean incident bundle.

## Install

From PyPI:

```bash
pip install pipeflight
```

For local development:

```bash
uv venv
uv pip install -e ".[dev]"
```

If your local Python environment is stale, you can run commands through `uv` directly:

```bash
uv run pipeflight --help
```

## Quick Demo: Bad Orders

Create a demo Parquet file:

```bash
python examples/create_bad_orders.py
```

Record an incident:

```bash
pipeflight record examples/bad_orders.parquet --key order_id --contract examples/orders.contract.json
```

Replay it:

```bash
pipeflight replay incident_2026_05_18_112233
```

Example output:

```text
recorded incident_2026_05_18_112233 status=failed rows=4 violations=5
replayed incident_2026_05_18_112233 status=failed rows=4 violations=5
```

The demo is expected to fail because the input intentionally contains invalid rows. A failed status means Pipeflight found evidence and preserved it.

## Full Validation Matrix

The repository includes a CSV that exercises the main validation rules:

- valid row
- duplicate key
- missing key
- bad number type
- minimum value failure
- maximum value failure
- bad datetime
- invalid allowed value
- missing required value

Input snapshot from `examples/validation_matrix.csv`:

```csv
order_id,amount,created_at,status,discount
ok-001,99.95,2026-05-17T10:00:00+00:00,paid,10
dup-001,25.00,2026-05-17T10:05:00+00:00,new,0
dup-001,30.00,2026-05-17T10:10:00+00:00,paid,5
,12.00,2026-05-17T10:15:00+00:00,paid,3
bad-amount-type,not-a-number,2026-05-17T10:20:00+00:00,paid,8
bad-amount-min,-1,2026-05-17T10:25:00+00:00,paid,8
bad-amount-max,1500,2026-05-17T10:30:00+00:00,paid,8
bad-date,42.00,not-a-date,paid,8
bad-status,42.00,2026-05-17T10:35:00+00:00,cancelled,8
missing-status,42.00,2026-05-17T10:40:00+00:00,,8
bad-discount-min,42.00,2026-05-17T10:45:00+00:00,paid,-5
bad-discount-max,42.00,2026-05-17T10:50:00+00:00,paid,105
bad-discount-type,42.00,2026-05-17T10:55:00+00:00,paid,free
```

Run it:

```bash
uv run pipeflight record examples/validation_matrix.csv --key order_id --contract examples/validation_matrix.contract.json --out incident_validation_matrix
uv run pipeflight replay incident_validation_matrix
```

Expected output:

```text
recorded incident_validation_matrix status=failed rows=13 violations=16
replayed incident_validation_matrix status=failed rows=13 violations=16
```

`rows=13` means Pipeflight scanned 13 CSV records. `violations=16` means it found 16 rule failures across those rows. One row can create more than one violation when it breaks more than one rule.

Why this example produces 16 violations:

| Input row | What it proves | Violations |
| --- | --- | --- |
| `ok-001` | valid row | 0 |
| first `dup-001` | first value for a unique key is accepted | 0 |
| second `dup-001` | duplicate key detection | 1: `order_id unique` |
| empty `order_id` | required key and CLI key check | 2: `order_id required`, `order_id key` |
| `bad-amount-type` | non-numeric amount | 3: `amount type`, `amount min`, `amount max` |
| `bad-amount-min` | amount below minimum | 1: `amount min` |
| `bad-amount-max` | amount above maximum | 1: `amount max` |
| `bad-date` | invalid datetime | 1: `created_at type` |
| `bad-status` | value outside allowed list | 1: `status allowed` |
| `missing-status` | required field is empty | 1: `status required` |
| `bad-discount-min` | optional numeric field below minimum | 1: `discount min` |
| `bad-discount-max` | optional numeric field above maximum | 1: `discount max` |
| `bad-discount-type` | non-numeric optional value | 3: `discount type`, `discount min`, `discount max` |

Total: `0 + 0 + 1 + 2 + 3 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 3 = 16`.

The same run also proves the output bundle:

```text
incident_validation_matrix/
  manifest.json          # status=failed, rows=13, violations=16
  failing_rows.parquet   # only rows that failed validation
  schema.json            # inferred types such as amount=mixed
  stats.json             # null counts, min/max values, latest timestamps
  report.html            # human-readable list of violations
  replay.py              # local replay helper
```

## Run Tests

```bash
uv run pytest --basetemp .pytest_tmp -p no:cacheprovider
```

Expected result:

```text
3 passed
```

## Python API

```python
from pipeflight import record_incident, replay_incident

incident = record_incident(
    "orders.parquet",
    key="order_id",
    contract="orders.contract.json",
)

print(incident.path)
print(incident.status)

replayed = replay_incident(incident.path)
print(replayed.violation_count)
```

## Contract Example

Contracts describe the checks Pipeflight should run.

```json
{
  "columns": {
    "order_id": { "type": "string", "required": true, "unique": true },
    "amount": { "type": "number", "required": true, "min": 0 },
    "created_at": { "type": "datetime", "required": true }
  },
  "freshness": {
    "column": "created_at",
    "max_age_seconds": 86400
  }
}
```

Supported column rules in v0.1:

- `type`: `string`, `number`, `integer`, `datetime`, or `boolean`
- `required`: value must be present and not empty
- `unique`: duplicate values fail validation
- `min`: numeric minimum
- `max`: numeric maximum
- `allowed`: list of accepted values

Supported freshness rule:

- `freshness.column`: datetime column to inspect
- `freshness.max_age_seconds`: maximum allowed age of the latest timestamp

## Example Scenarios

- Schema drift: detect missing or unexpected contract columns.
- Freshness failure: capture evidence when the latest event timestamp is too old.
- Null explosion: capture rows where required fields disappear.
- Replay demo: send a small incident folder to another engineer instead of the entire source data.

## Release Plan

v0.1 stays intentionally narrow:

- `pipeflight record orders.parquet`
- `pipeflight replay incident_*`
- local incident bundle
- Parquet failing rows
- HTML report
- publish-ready packaging

Later versions can add integrations, but the first promise is simple:

> Preserve reproducible evidence when data pipelines fail.

## Later Roadmap

One likely future command:

```bash
pipeflight compare incident_a incident_b
```

Potential output:

- schema diff
- null drift
- freshness drift
- row count delta

## License

MIT
