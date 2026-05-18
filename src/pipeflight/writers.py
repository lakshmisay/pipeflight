from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def write_json(path: str | Path, data: Any) -> None:
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True, default=str), encoding="utf-8")


def write_rows_parquet(path: str | Path, rows: list[dict[str, Any]]) -> None:
    import pyarrow as pa  # type: ignore
    import pyarrow.parquet as pq  # type: ignore

    output = Path(path)
    if not rows:
        table = pa.table({"_pipeflight_note": pa.array([], type=pa.string())})
    else:
        table = pa.Table.from_pylist(rows)
    pq.write_table(table, output)


def write_report(path: str | Path, manifest: dict[str, Any], stats: dict[str, Any], violations: list[dict[str, Any]]) -> None:
    status = html.escape(str(manifest["status"]))
    source = html.escape(str(manifest["source"]))
    rows = html.escape(str(stats.get("row_count", 0)))
    violation_items = "\n".join(
        f"<li><code>{html.escape(str(item.get('rule')))}</code> "
        f"{html.escape(str(item.get('column') or 'dataset'))}: "
        f"{html.escape(str(item.get('message')))}</li>"
        for item in violations[:200]
    )
    if not violation_items:
        violation_items = "<li>No violations recorded.</li>"

    content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Pipeflight Report</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #17202a; }}
    code {{ background: #eef2f6; padding: 0.1rem 0.3rem; border-radius: 4px; }}
    .status {{ display: inline-block; padding: 0.25rem 0.5rem; border-radius: 4px; background: #e8eef8; }}
    table {{ border-collapse: collapse; margin-top: 1rem; }}
    th, td {{ border: 1px solid #d8dee6; padding: 0.35rem 0.5rem; text-align: left; }}
  </style>
</head>
<body>
  <h1>Pipeflight Report</h1>
  <p><strong>Status:</strong> <span class="status">{status}</span></p>
  <p><strong>Source:</strong> <code>{source}</code></p>
  <p><strong>Rows scanned:</strong> {rows}</p>
  <h2>Violations</h2>
  <ul>{violation_items}</ul>
</body>
</html>
"""
    Path(path).write_text(content, encoding="utf-8")


def write_replay_script(path: str | Path) -> None:
    script = """from pipeflight import replay_incident

if __name__ == "__main__":
    result = replay_incident(".")
    print(f"status={result.status} violations={result.violation_count}")
"""
    Path(path).write_text(script, encoding="utf-8")
