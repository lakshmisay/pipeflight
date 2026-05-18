from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from pipeflight.contracts import load_contract
from pipeflight.readers import detect_format, iter_rows
from pipeflight.validators import ValidationState
from pipeflight.writers import write_json, write_report, write_replay_script, write_rows_parquet


@dataclass(frozen=True)
class IncidentResult:
    path: Path
    status: str
    row_count: int
    violation_count: int


def record_incident(
    source: str | Path,
    out: str | Path | None = None,
    key: str | None = None,
    contract: str | Path | None = None,
    max_failing_rows: int = 500,
) -> IncidentResult:
    source_path = Path(source)
    out_path = Path(out) if out else _default_incident_dir()
    out_path.mkdir(parents=True, exist_ok=True)

    contract_model = load_contract(contract)
    state = ValidationState(contract_model, key=key)
    failing_rows: list[dict[str, object]] = []

    for row_number, row in enumerate(iter_rows(source_path), start=1):
        failed = state.check_row(row, row_number)
        row_with_meta = {"_pipeflight_row_number": row_number, **row}
        if failed and len(failing_rows) < max_failing_rows:
            failing_rows.append(row_with_meta)

    state.finalize()

    status = "failed" if state.violations else "passed"
    generated_at = datetime.now(timezone.utc).isoformat()
    manifest = {
        "tool": "pipeflight",
        "version": "0.1.0",
        "status": status,
        "generated_at": generated_at,
        "source": str(source_path),
        "format": detect_format(source_path),
        "key": key,
        "contract": str(contract) if contract else None,
        "row_count": state.profile.row_count,
        "violation_count": len(state.violations),
        "artifacts": {
            "schema": "schema.json",
            "stats": "stats.json",
            "failing_rows": "failing_rows.parquet",
            "report": "report.html",
            "replay": "replay.py",
        },
    }

    schema = {"columns": state.profile.columns}
    stats = asdict(state.profile)
    violations = [asdict(item) for item in state.violations]

    write_json(out_path / "manifest.json", manifest)
    write_json(out_path / "schema.json", schema)
    write_json(out_path / "stats.json", stats)
    write_rows_parquet(out_path / "failing_rows.parquet", failing_rows)
    write_report(out_path / "report.html", manifest, stats, violations)
    write_replay_script(out_path / "replay.py")

    return IncidentResult(
        path=out_path,
        status=status,
        row_count=state.profile.row_count,
        violation_count=len(state.violations),
    )


def replay_incident(path: str | Path) -> IncidentResult:
    incident_path = Path(path)
    manifest = json.loads((incident_path / "manifest.json").read_text(encoding="utf-8"))
    stats = json.loads((incident_path / "stats.json").read_text(encoding="utf-8"))

    required = [
        "manifest.json",
        "schema.json",
        "stats.json",
        "failing_rows.parquet",
    ]
    missing = [name for name in required if not (incident_path / name).exists()]
    if missing:
        raise FileNotFoundError(f"Incident is missing artifacts: {', '.join(missing)}")

    return IncidentResult(
        path=incident_path,
        status=str(manifest["status"]),
        row_count=int(stats.get("row_count", 0)),
        violation_count=int(manifest.get("violation_count", 0)),
    )


def _default_incident_dir() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y_%m_%d_%H%M%S")
    return Path(f"incident_{stamp}")
