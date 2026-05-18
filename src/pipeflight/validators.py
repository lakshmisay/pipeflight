from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from pipeflight.contracts import Contract
from pipeflight.schema import coerce_number, infer_type, merge_type, parse_datetime


@dataclass
class Violation:
    row_number: int | None
    column: str | None
    rule: str
    message: str


@dataclass
class Profile:
    row_count: int = 0
    columns: dict[str, str] = field(default_factory=dict)
    null_counts: dict[str, int] = field(default_factory=dict)
    min_values: dict[str, float] = field(default_factory=dict)
    max_values: dict[str, float] = field(default_factory=dict)
    max_datetimes: dict[str, str] = field(default_factory=dict)


class ValidationState:
    def __init__(self, contract: Contract, key: str | None = None) -> None:
        self.contract = contract
        self.key = key
        self.profile = Profile()
        self.violations: list[Violation] = []
        self._seen_unique: dict[str, set[str]] = {
            name: set() for name, rule in contract.columns.items() if rule.unique
        }

    def check_row(self, row: dict[str, Any], row_number: int) -> bool:
        self.profile.row_count += 1
        row_failed = False

        for column, value in row.items():
            self.profile.columns[column] = merge_type(self.profile.columns.get(column), infer_type(value))
            if value is None or value == "":
                self.profile.null_counts[column] = self.profile.null_counts.get(column, 0) + 1
            number = coerce_number(value)
            if number is not None:
                self.profile.min_values[column] = min(number, self.profile.min_values.get(column, number))
                self.profile.max_values[column] = max(number, self.profile.max_values.get(column, number))
            parsed = parse_datetime(value)
            if parsed is not None:
                current = self.profile.max_datetimes.get(column)
                if current is None or parsed.isoformat() > current:
                    self.profile.max_datetimes[column] = parsed.isoformat()

        for column, rule in self.contract.columns.items():
            value = row.get(column)
            if rule.required and (column not in row or value is None or value == ""):
                self._add(row_number, column, "required", f"{column} is required.")
                row_failed = True
                continue

            if value is None or value == "":
                continue

            actual_type = infer_type(value)
            if rule.type and not _type_matches(rule.type, actual_type):
                self._add(row_number, column, "type", f"{column} expected {rule.type}, got {actual_type}.")
                row_failed = True

            if rule.min is not None:
                number = coerce_number(value)
                if number is None or number < rule.min:
                    self._add(row_number, column, "min", f"{column} must be >= {rule.min}.")
                    row_failed = True

            if rule.max is not None:
                number = coerce_number(value)
                if number is None or number > rule.max:
                    self._add(row_number, column, "max", f"{column} must be <= {rule.max}.")
                    row_failed = True

            if rule.allowed and str(value) not in rule.allowed:
                self._add(row_number, column, "allowed", f"{column} is not in the allowed set.")
                row_failed = True

            if rule.unique:
                normalized = str(value)
                if normalized in self._seen_unique[column]:
                    self._add(row_number, column, "unique", f"{column} is duplicated.")
                    row_failed = True
                self._seen_unique[column].add(normalized)

        if self.key and not row.get(self.key):
            self._add(row_number, self.key, "key", f"{self.key} is missing or empty.")
            row_failed = True

        return row_failed

    def finalize(self) -> None:
        for column in self.contract.columns:
            if column not in self.profile.columns:
                self._add(None, column, "schema", f"{column} is missing from the dataset.")

        freshness = self.contract.freshness
        if freshness is None:
            return
        latest = self.profile.max_datetimes.get(freshness.column)
        if latest is None:
            self._add(None, freshness.column, "freshness", "No parseable freshness timestamp found.")
            return

        parsed = parse_datetime(latest)
        if parsed is None:
            self._add(None, freshness.column, "freshness", "No parseable freshness timestamp found.")
            return
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        age_seconds = (datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds()
        if age_seconds > freshness.max_age_seconds:
            self._add(
                None,
                freshness.column,
                "freshness",
                f"Latest timestamp is {int(age_seconds)} seconds old.",
            )

    def _add(self, row_number: int | None, column: str | None, rule: str, message: str) -> None:
        self.violations.append(Violation(row_number=row_number, column=column, rule=rule, message=message))


def _type_matches(expected: str, actual: str) -> bool:
    expected = expected.lower()
    if expected == actual:
        return True
    if expected == "number" and actual == "integer":
        return True
    if expected == "string" and actual not in {"null", "mixed"}:
        return True
    return False
