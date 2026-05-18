from __future__ import annotations

import argparse
from pathlib import Path

from pipeflight.core import record_incident, replay_incident


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pipeflight",
        description="Record and replay compact evidence for data pipeline incidents.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    record = subparsers.add_parser("record", help="Record an incident artifact from a dataset.")
    record.add_argument("source", help="Input Parquet, CSV, JSONL, or NDJSON file.")
    record.add_argument("--out", help="Output incident directory. Defaults to incident_<timestamp>.")
    record.add_argument("--key", help="Primary identifier column to require.")
    record.add_argument("--contract", help="JSON or YAML data contract.")
    record.add_argument("--max-failing-rows", type=int, default=500, help="Maximum failing rows to capture.")

    replay = subparsers.add_parser("replay", help="Verify and summarize an incident artifact.")
    replay.add_argument("incident", help="Incident directory.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "record":
        result = record_incident(
            source=args.source,
            out=args.out,
            key=args.key,
            contract=args.contract,
            max_failing_rows=args.max_failing_rows,
        )
        print(
            f"recorded {Path(result.path)} "
            f"status={result.status} rows={result.row_count} violations={result.violation_count}"
        )
        return 1 if result.status == "failed" else 0

    if args.command == "replay":
        result = replay_incident(args.incident)
        print(
            f"replayed {Path(result.path)} "
            f"status={result.status} rows={result.row_count} violations={result.violation_count}"
        )
        return 1 if result.status == "failed" else 0

    parser.error("Unknown command.")
    return 2
