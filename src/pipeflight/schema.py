from __future__ import annotations

from datetime import datetime
from typing import Any


def infer_type(value: Any) -> str:
    if value is None or value == "":
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        stripped = value.strip()
        if _looks_integer(stripped):
            return "integer"
        if _looks_number(stripped):
            return "number"
        if parse_datetime(stripped) is not None:
            return "datetime"
        return "string"
    return type(value).__name__


def merge_type(existing: str | None, incoming: str) -> str:
    if existing is None:
        return incoming
    if existing == incoming:
        return existing
    if "null" in {existing, incoming}:
        return incoming if existing == "null" else existing
    if {existing, incoming} <= {"integer", "number"}:
        return "number"
    return "mixed"


def parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        return None

    candidate = value.strip()
    if not candidate:
        return None
    if candidate.endswith("Z"):
        candidate = f"{candidate[:-1]}+00:00"

    try:
        return datetime.fromisoformat(candidate)
    except ValueError:
        return None


def coerce_number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    try:
        return float(str(value))
    except ValueError:
        return None


def _looks_integer(value: str) -> bool:
    if not value:
        return False
    signless = value[1:] if value[0] in "+-" else value
    return signless.isdigit()


def _looks_number(value: str) -> bool:
    if not value:
        return False
    try:
        float(value)
    except ValueError:
        return False
    return True
