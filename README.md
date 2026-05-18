# Pipeflight

**A black box recorder for data pipelines.**

Most data quality tools tell you something failed. Pipeflight preserves the evidence bundle you need to debug the incident later: failing rows, schema snapshot, stats, report, and a replay script.

```bash
pipeflight record orders.parquet
```

Generates:

```text
incident_2026_05_18_112233/
  manifest.json
  failing_rows.parquet
  schema.json
  stats.json
  replay.py
  report.html
```

## How It Works

```text
Pipeline failure
       |
       v
pipeflight record orders.parquet
       |
       v
Incident bundle
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

## Screenshot / GIF

A short demo GIF will live here:

```text
pipeflight record examples/bad_orders.parquet
tree incident_*
pipeflight replay incident_*
```

## Install

```bash
pip install pipeflight
```

For local development with `uv`:

```bash
uv venv
uv pip install -e ".[dev]"
```

## Quick Demo

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
