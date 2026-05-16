"""
PDF data dictionary extraction.

Reads a PDF, extracts text, and heuristically maps column names to descriptions
when the column list is known. CMS dictionaries follow a "Column Name —
description" / "Field — description" pattern in most cases.

The full extracted text is also returned for inclusion in LLM context.
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass
class DictionaryParseResult:
    full_text: str
    column_descriptions: dict[str, str]  # normalized_col_name → description


def extract_pdf_text(path_or_bytes: Path | bytes | io.BytesIO) -> str:
    if isinstance(path_or_bytes, (Path, str)):
        reader = PdfReader(str(path_or_bytes))
    elif isinstance(path_or_bytes, bytes):
        reader = PdfReader(io.BytesIO(path_or_bytes))
    else:
        reader = PdfReader(path_or_bytes)
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            pages.append("")
    return "\n\n".join(pages)


def _normalize(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def map_columns_heuristically(
    full_text: str,
    normalized_columns: list[str],
    display_names: dict[str, str],
) -> dict[str, str]:
    """For each known column, find the first paragraph in the PDF text where
    its display name appears, and grab the surrounding sentences as a description.

    This is intentionally simple — it works on most CMS dictionaries because they
    list the column name on its own line followed by an explanation. Real-world
    PDFs vary, but the LLM also gets the full text as context to fill gaps.
    """
    out: dict[str, str] = {}
    text_lower = full_text.lower()

    for norm in normalized_columns:
        display = display_names.get(norm, norm)
        needle = display.lower()
        idx = text_lower.find(needle)
        if idx == -1:
            # Try the normalized form too
            idx = text_lower.find(norm.replace("_", " "))
        if idx == -1:
            continue

        # Grab the chunk after the occurrence, up to the next double-newline or 500 chars
        chunk = full_text[idx : idx + 500]
        # Trim at next likely column boundary
        chunk = re.split(r"\n\s*\n", chunk, maxsplit=1)[0]
        # Clean whitespace
        chunk = re.sub(r"\s+", " ", chunk).strip()
        # Drop the leading column name from the description if duplicated
        if chunk.lower().startswith(needle):
            chunk = chunk[len(needle):].lstrip(" :—-")
        if chunk and len(chunk) > 10:
            out[norm] = chunk[:400]

    return out


def parse_dictionary(
    path_or_bytes: Path | bytes,
    normalized_columns: list[str],
    display_names: dict[str, str],
) -> DictionaryParseResult:
    full_text = extract_pdf_text(path_or_bytes)
    descriptions = map_columns_heuristically(full_text, normalized_columns, display_names)
    return DictionaryParseResult(full_text=full_text, column_descriptions=descriptions)
