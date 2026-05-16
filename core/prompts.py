"""
Prompt templates for the three LLM tasks: sample questions, SQL generation,
result analysis. Centralized so they can be tuned independently of the
provider implementations.
"""
from __future__ import annotations

import json
from typing import Any


# ── Sample questions ─────────────────────────────────────────────────────
SAMPLE_QUESTIONS_SYS = """You are a data analyst helping a non-technical executive \
explore a dataset they have just loaded. Generate 5 specific, interesting \
starter questions a leader would actually ask. Mix difficulty: 2 simple lookups, \
2 comparative or ranking, 1 deeper pattern. Use the schema and data dictionary \
provided. Be concrete — reference real column names or values from the samples.

Return ONLY valid JSON in this exact shape:
{"questions": ["...", "...", "...", "...", "..."]}"""


def sample_questions_user(dataset_name: str, schema_text: str, dictionary_text: str | None) -> str:
    parts = [f"DATASET: {dataset_name}", "", schema_text]
    if dictionary_text:
        parts.extend(["", "DATA DICTIONARY (verbatim from source):", dictionary_text[:4000]])
    parts.extend(["", "Generate the questions."])
    return "\n".join(parts)


# ── SQL generation ───────────────────────────────────────────────────────
SQL_GEN_SYS = """You translate natural-language questions into SQLite queries.

Rules:
- Use ONLY columns from the schema below.
- Column names with spaces or special characters MUST be wrapped in double quotes.
- Be explicit with aggregations (SUM, AVG, COUNT) — never count rows when the user wants a sum.
- Filter NULLs explicitly when aggregating numerics.
- Order results meaningfully; use LIMIT for "top N" questions.
- Return at most 50 rows for chart-friendly output unless the user asks for more.
- Alias columns to pretty names where helpful (e.g., total_enrollment AS "Total Enrollment").
- If the dataset notes suppression markers (like '*' meaning small-cell suppression), exclude those when aggregating numerics on the underlying column.

Return ONLY valid JSON:
{"sql": "<the SQL query>", "reasoning": "<one short sentence explaining the approach>"}"""


def sql_gen_user(
    question: str,
    table_name: str,
    schema_text: str,
    dictionary_text: str | None,
    history: list[dict[str, Any]],
    suppression_markers: list[str] | None = None,
) -> str:
    parts = [f"TABLE: {table_name}", "", schema_text]
    if suppression_markers:
        parts.append(
            f"\nSUPPRESSION MARKERS in this dataset: {suppression_markers}. "
            f"These appear in raw data where small-cell suppression was applied. "
            f"They have already been converted to NULL on load — you do NOT need "
            f"to filter for the literal marker, but be aware that some rows have "
            f"NULL values in numeric columns as a result."
        )
    if dictionary_text:
        parts.extend(["", "DATA DICTIONARY:", dictionary_text[:4000]])
    if history:
        parts.append("\nPRIOR TURNS IN THIS CONVERSATION:")
        for i, h in enumerate(history, 1):
            parts.append(f"Q{i}: {h['question']}")
            parts.append(f"SQL{i}: {h['sql']}")
    parts.extend(["", f"USER QUESTION: {question}"])
    return "\n".join(parts)


# ── Result analysis ──────────────────────────────────────────────────────
ANALYSIS_SYS = """You are analyzing a SQL query result for a non-technical executive. \
Be specific and quantitative — use actual numbers from the data. Recommend the right \
chart given the data shape.

Chart spec rules:
- chart_type: "bar" | "line" | "pie" | "table" | "none"
- "bar" for category comparisons (category on x, numeric on y).
- "line" for trends over time (time/ordinal on x, numeric on y).
- "pie" only for share-of-whole with <= 6 slices.
- "table" if no visualization adds value (1 number, mixed shapes).
- "none" if results are empty.
- x_column and y_column MUST be EXACT column names from the results.
- y_column must be numeric.
- Never put a numeric column on a bar chart's x-axis — bar x needs a category.

Return ONLY valid JSON:
{
  "summary": "one-sentence headline",
  "key_findings": ["finding 1 with numbers", "finding 2", "finding 3"],
  "caveats": ["optional caveat"],
  "chart_spec": {
    "chart_type": "bar",
    "title": "Short descriptive title",
    "x_column": "exact_column_name",
    "y_column": "exact_column_name",
    "limit": 10
  }
}"""


def analysis_user(
    question: str,
    sql: str,
    columns: list[str],
    rows: list[list[Any]],
) -> str:
    preview = []
    for row in rows[:30]:
        preview.append({c: v for c, v in zip(columns, row)})
    return (
        f"QUESTION: {question}\n"
        f"SQL: {sql}\n"
        f"COLUMNS: {json.dumps(columns)}\n"
        f"ROW COUNT: {len(rows)}\n"
        f"FIRST {len(preview)} ROWS:\n{json.dumps(preview, default=str, indent=2)}\n\n"
        f"Analyze."
    )
