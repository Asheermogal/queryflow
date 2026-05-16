"""Schema scanner. Computes column metadata for both the UI and LLM prompts."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any


@dataclass
class ColumnStats:
    name: str               # normalized name (what SQL queries use)
    display_name: str       # human-readable (original from source)
    sql_type: str
    n_rows: int
    n_nulls: int
    n_distinct: int
    samples: list[Any]
    description: str | None = None  # from dictionary, if available

    @property
    def null_pct(self) -> float:
        return 100 * self.n_nulls / self.n_rows if self.n_rows else 0


def scan_table(
    conn: sqlite3.Connection,
    table: str,
    display_names: dict[str, str] | None = None,
    descriptions: dict[str, str] | None = None,
) -> list[ColumnStats]:
    cur = conn.cursor()
    cur.execute(f'PRAGMA table_info("{table}")')
    cols_info = cur.fetchall()  # (cid, name, type, notnull, dflt, pk)
    n_rows = cur.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]

    out: list[ColumnStats] = []
    for _, name, sql_type, *_ in cols_info:
        nulls = cur.execute(
            f'SELECT SUM(CASE WHEN "{name}" IS NULL THEN 1 ELSE 0 END) FROM "{table}"'
        ).fetchone()[0] or 0
        distinct = cur.execute(
            f'SELECT COUNT(DISTINCT "{name}") FROM "{table}"'
        ).fetchone()[0]
        samples = [
            r[0] for r in cur.execute(
                f'SELECT DISTINCT "{name}" FROM "{table}" WHERE "{name}" IS NOT NULL LIMIT 5'
            ).fetchall()
        ]
        out.append(
            ColumnStats(
                name=name,
                display_name=(display_names or {}).get(name, name),
                sql_type=sql_type or "TEXT",
                n_rows=n_rows,
                n_nulls=int(nulls),
                n_distinct=int(distinct),
                samples=samples,
                description=(descriptions or {}).get(name),
            )
        )
    return out


def schema_to_prompt_text(
    table: str,
    description: str,
    stats: list[ColumnStats],
) -> str:
    """LLM-friendly schema dump."""
    lines = [
        f"TABLE: {table}",
        f"DESCRIPTION: {description}",
        f"ROW COUNT: {stats[0].n_rows if stats else 0}",
        "COLUMNS:",
    ]
    for s in stats:
        samples_str = ", ".join(repr(v) for v in s.samples[:3])
        bits = [
            f'  - "{s.name}" ({s.sql_type})',
        ]
        if s.description:
            bits.append(f"      description: {s.description}")
        bits.append(
            f"      stats: {s.n_distinct} distinct, "
            f"{s.null_pct:.1f}% null, "
            f"samples: [{samples_str}]"
        )
        lines.extend(bits)
    return "\n".join(lines)
