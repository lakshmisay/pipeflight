from __future__ import annotations

import json
from pathlib import Path

from pipeflight import record_incident, replay_incident
from pipeflight.cli import main


def test_record_incident_captures_failing_rows(tmp_path: Path) -> None:
    source = tmp_path / "orders.csv"
    contract = tmp_path / "contract.json"
    incident = tmp_path / "incident"

    source.write_text(
        "order_id,amount,created_at\n"
        "a,10,2026-05-17T10:00:00+00:00\n"
        "a,-1,bad-date\n",
        encoding="utf-8",
    )
    contract.write_text(
        json.dumps(
            {
                "columns": {
                    "order_id": {"type": "string", "required": True, "unique": True},
                    "amount": {"type": "number", "required": True, "min": 0},
                    "created_at": {"type": "datetime", "required": True},
                }
            }
        ),
        encoding="utf-8",
    )

    result = record_incident(source, incident, key="order_id", contract=contract)

    assert result.status == "failed"
    assert result.row_count == 2
    assert result.violation_count == 3
    assert (incident / "manifest.json").exists()
    assert (incident / "report.html").exists()
    assert (incident / "failing_rows.parquet").exists()


def test_replay_incident_reads_artifacts(tmp_path: Path) -> None:
    source = tmp_path / "orders.jsonl"
    incident = tmp_path / "incident"
    source.write_text('{"order_id": "a", "amount": 10}\n', encoding="utf-8")

    record_incident(source, incident, key="order_id")
    result = replay_incident(incident)

    assert result.status == "passed"
    assert result.row_count == 1
    assert result.violation_count == 0


def test_replay_cli_expands_wildcard_patterns(tmp_path: Path, capsys) -> None:
    source = tmp_path / "orders.jsonl"
    incident = tmp_path / "incident_demo"
    source.write_text('{"order_id": "a", "amount": 10}\n', encoding="utf-8")

    record_incident(source, incident, key="order_id")

    exit_code = main(["replay", str(tmp_path / "incident_*")])

    assert exit_code == 0
    assert "replayed" in capsys.readouterr().out
