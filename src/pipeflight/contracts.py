from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ColumnRule:
    name: str
    type: str | None = None
    required: bool = False
    unique: bool = False
    min: float | None = None
    max: float | None = None
    allowed: tuple[str, ...] = ()


@dataclass(frozen=True)
class FreshnessRule:
    column: str
    max_age_seconds: int


@dataclass(frozen=True)
class Contract:
    columns: dict[str, ColumnRule] = field(default_factory=dict)
    freshness: FreshnessRule | None = None


def load_contract(path: str | Path | None) -> Contract:
    if path is None:
        return Contract()

    contract_path = Path(path)
    text = contract_path.read_text(encoding="utf-8")
    data: dict[str, Any]

    if contract_path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise RuntimeError("YAML contracts require installing pipeflight[yaml].") from exc
        data = yaml.safe_load(text) or {}
    else:
        data = json.loads(text)

    columns = {
        name: ColumnRule(
            name=name,
            type=rules.get("type"),
            required=bool(rules.get("required", False)),
            unique=bool(rules.get("unique", False)),
            min=rules.get("min"),
            max=rules.get("max"),
            allowed=tuple(str(item) for item in rules.get("allowed", ())),
        )
        for name, rules in (data.get("columns") or {}).items()
    }

    freshness_data = data.get("freshness")
    freshness = None
    if freshness_data:
        freshness = FreshnessRule(
            column=freshness_data["column"],
            max_age_seconds=int(freshness_data["max_age_seconds"]),
        )

    return Contract(columns=columns, freshness=freshness)
