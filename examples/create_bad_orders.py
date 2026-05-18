from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


def main() -> None:
    output = Path(__file__).with_name("bad_orders.parquet")
    table = pa.table(
        {
            "order_id": ["o-001", "o-002", "o-002", ""],
            "amount": [19.95, 42.00, -4.50, 12.00],
            "created_at": [
                "2026-05-17T10:00:00+00:00",
                "2026-05-17T10:05:00+00:00",
                "2026-05-17T10:10:00+00:00",
                "not-a-date",
            ],
        }
    )
    pq.write_table(table, output)
    print(output)


if __name__ == "__main__":
    main()
