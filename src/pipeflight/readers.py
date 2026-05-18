from __future__ import annotations

import csv
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any


Row = dict[str, Any]


def detect_format(path: str | Path) -> str:
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix in {".jsonl", ".ndjson"}:
        return "jsonl"
    if suffix == ".parquet":
        return "parquet"
    raise ValueError(f"Unsupported file format: {suffix or '<none>'}")


def iter_rows(path: str | Path, limit: int | None = None) -> Iterator[Row]:
    file_format = detect_format(path)
    if file_format == "csv":
        yield from _iter_csv(path, limit)
    elif file_format == "jsonl":
        yield from _iter_jsonl(path, limit)
    elif file_format == "parquet":
        yield from _iter_parquet(path, limit)
    else:
        raise ValueError(f"Unsupported file format: {file_format}")


def _iter_csv(path: str | Path, limit: int | None) -> Iterator[Row]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for index, row in enumerate(reader):
            if limit is not None and index >= limit:
                break
            yield dict(row)


def _iter_jsonl(path: str | Path, limit: int | None) -> Iterator[Row]:
    with Path(path).open("r", encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            if limit is not None and index >= limit:
                break
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"JSONL row {index + 1} is not an object.")
                yield value


def _iter_parquet(path: str | Path, limit: int | None) -> Iterator[Row]:
    import pyarrow.parquet as pq  # type: ignore

    rows_seen = 0
    parquet_file = pq.ParquetFile(path)
    for batch in parquet_file.iter_batches(batch_size=10_000):
        records = batch.to_pylist()
        for row in records:
            if limit is not None and rows_seen >= limit:
                return
            rows_seen += 1
            yield row
