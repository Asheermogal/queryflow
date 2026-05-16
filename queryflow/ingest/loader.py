"""
File ingestion: CSV and Excel. Handles real-world messiness:
- Encoding detection (latin-1, cp1252, utf-8, utf-8-sig)
- Suppression markers (CMS uses '*'; many use 'N/A', '--', '?')
- Type inference (strings that are actually numerics after suppression)
- Column name normalization (snake_case)
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass
from pathlib import Path

import chardet
import pandas as pd

DEFAULT_SUPPRESSION_MARKERS = ["*", "N/A", "n/a", "--", "—", "."]
ENCODINGS_TO_TRY = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]


@dataclass
class LoadResult:
    df: pd.DataFrame
    encoding: str
    suppression_markers_found: list[str]
    original_columns: list[str]   # before normalization
    column_map: dict[str, str]    # original → normalized


def normalize_column_name(name: str) -> str:
    """Convert any column name to safe snake_case."""
    s = str(name).strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = s.strip("_")
    return s or "col"


def detect_encoding(raw: bytes) -> str:
    """Best-effort encoding detection. Tries the common ones, then chardet."""
    for enc in ENCODINGS_TO_TRY:
        try:
            raw.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    detected = chardet.detect(raw[:50_000])
    return detected.get("encoding") or "latin-1"


def load_file(
    file_input: Path | io.BytesIO | bytes,
    filename: str,
    suppression_markers: list[str] | None = None,
) -> LoadResult:
    """Load CSV or Excel into a DataFrame, handling all the dirty edge cases."""

    markers = suppression_markers or DEFAULT_SUPPRESSION_MARKERS
    ext = Path(filename).suffix.lower()

    # Read raw bytes once for encoding detection (CSV path)
    if isinstance(file_input, (bytes, io.BytesIO)):
        raw_bytes = file_input if isinstance(file_input, bytes) else file_input.getvalue()
    else:
        raw_bytes = Path(file_input).read_bytes()

    if ext in (".xlsx", ".xls", ".xlsm"):
        engine = "openpyxl" if ext in (".xlsx", ".xlsm") else "xlrd"
        df = pd.read_excel(io.BytesIO(raw_bytes), engine=engine, na_values=markers)
        encoding = "—"
    else:
        encoding = detect_encoding(raw_bytes)
        df = pd.read_csv(
            io.BytesIO(raw_bytes),
            encoding=encoding,
            na_values=markers,
            low_memory=False,
        )

    # Track which suppression markers were actually present (for the UI banner)
    markers_found = []
    text_sample = raw_bytes[:200_000].decode(encoding if ext not in (".xlsx", ".xls", ".xlsm") else "latin-1", errors="ignore")
    for m in markers:
        # Match marker as a CSV field (commas around it) — avoids false positives from text content
        if f",{m}," in text_sample or f",{m}\n" in text_sample or f"\n{m}," in text_sample:
            markers_found.append(m)

    # Normalize column names. Track originals.
    original_cols = list(df.columns)
    column_map: dict[str, str] = {}
    new_names: list[str] = []
    seen: dict[str, int] = {}
    for c in original_cols:
        base = normalize_column_name(c)
        # Collision handling
        if base in seen:
            seen[base] += 1
            candidate = f"{base}_{seen[base]}"
        else:
            seen[base] = 0
            candidate = base
        column_map[c] = candidate
        new_names.append(candidate)
    df.columns = new_names

    # Coerce types: try numeric, fall back to leaving as object/string.
    # Handles real-world formats: bare numbers, "$1,234.56", "12,345", "67%"
    for col in df.columns:
        # pd.api.types.is_string_dtype handles both legacy "object" and the
        # newer StringDtype (pyarrow-backed) introduced in recent pandas.
        if pd.api.types.is_string_dtype(df[col]) and not pd.api.types.is_numeric_dtype(df[col]):
            # Clean common numeric formatting from string cells
            cleaned = df[col].astype(str).str.replace(",", "", regex=False)
            cleaned = cleaned.str.replace("$", "", regex=False)
            cleaned = cleaned.str.replace("%", "", regex=False)
            cleaned = cleaned.str.strip()
            # Restore original NaNs (str cast turns NaN into 'nan')
            cleaned = cleaned.where(df[col].notna())

            converted = pd.to_numeric(cleaned, errors="coerce")
            non_null_before = df[col].notna().sum()
            non_null_after = converted.notna().sum()
            # Adopt if we kept ≥90% of the original non-null values
            if non_null_before > 0 and non_null_after / non_null_before >= 0.9:
                df[col] = converted

    return LoadResult(
        df=df,
        encoding=encoding,
        suppression_markers_found=markers_found,
        original_columns=original_cols,
        column_map=column_map,
    )
