from __future__ import annotations

import argparse
import glob
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
    replay.add_argument("incident", nargs="+", help="Incident directory or wildcard pattern.")

    return parser


def _expand_incident_args(values: list[str]) -> list[Path]:
    incidents: list[Path] = []
    for value in values:
        has_wildcard = any(char in value for char in "*?[")
        matches = sorted(glob.glob(value)) if has_wildcard else []
        if has_wildcard and not matches:
            raise ValueError(f"No incident directories match {value!r}.")
        incidents.extend(Path(match) for match in matches)
        if not has_wildcard:
            incidents.append(Path(value))
    return incidents


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
        try:
            incidents = _expand_incident_args(args.incident)
        except ValueError as exc:
            parser.error(str(exc))

        exit_code = 0
        for incident in incidents:
            result = replay_incident(incident)
            print(
                f"replayed {Path(result.path)} "
                f"status={result.status} rows={result.row_count} violations={result.violation_count}"
            )
            if result.status == "failed":
                exit_code = 1
        return exit_code

    parser.error("Unknown command.")
    return 2
