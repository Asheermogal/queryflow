"""
Per-session SQLite database. Holds all loaded datasets. Stays in memory so
each user gets isolation; survives page navigation via streamlit session state.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass
class Dataset:
    """Metadata about one loaded dataset."""
    table: str                              # SQL-safe identifier
    name: str                               # human-readable
    description: str                        # short blurb (from manifest or generated)
    row_count: int
    column_count: int
    encoding: str
    suppression_markers: list[str] = field(default_factory=list)
    display_names: dict[str, str] = field(default_factory=dict)   # col → original label
    column_descriptions: dict[str, str] = field(default_factory=dict)
    dictionary_text: str | None = None      # full PDF text (for LLM context)
    methodology_text: str | None = None     # optional


class Database:
    def __init__(self) -> None:
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.datasets: dict[str, Dataset] = {}  # table -> Dataset

    def add_dataset(self, df: pd.DataFrame, dataset: Dataset) -> None:
        df.to_sql(dataset.table, self.conn, index=False, if_exists="replace")
        self.datasets[dataset.table] = dataset
        self.conn.commit()

    def remove_dataset(self, table: str) -> None:
        if table in self.datasets:
            self.conn.execute(f'DROP TABLE IF EXISTS "{table}"')
            del self.datasets[table]

    def list_datasets(self) -> list[Dataset]:
        return list(self.datasets.values())

    def query(self, sql: str) -> tuple[list[str], list[list[Any]]]:
        cur = self.conn.execute(sql)
        columns = [d[0] for d in cur.description] if cur.description else []
        rows = [list(r) for r in cur.fetchall()]
        return columns, rows
