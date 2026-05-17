"""
Prompt templates for every LLM task in Data Explorer:
  - dataset brief (one cached call per dataset, on first activation)
  - explore (text-only insights, no SQL)
  - SQL generation (drafted only; user must press Run)
  - result analysis (after Run)
  - dashboard spec (one cached call per dataset, on demand)

Centralized so they can be tuned independently of the provider implementations.
"""
from __future__ import annotations

import json
from typing import Any


# ── Dataset brief (cached per dataset) ───────────────────────────────────
DATASET_BRIEF_SYS = """You are a senior data analyst. Given the schema and a few sample values from a tabular dataset, write a concise brief a non-technical executive can read in under 30 seconds.

Be specific. Reference real column names. Avoid generic platitudes like "this dataset contains data".

Return ONLY valid JSON in this exact shape:
{
  "headline": "one-sentence description of what this dataset is and its grain",
  "bullets": ["fact about the dataset", "another fact", "what kinds of questions it can answer", "..."],
  "key_columns": ["col_a", "col_b", "col_c", "col_d", "col_e"],
  "suggested_questions": ["specific question 1", "specific question 2", "specific question 3", "specific question 4", "specific question 5"]
}

Rules:
- headline: 1 sentence, mention the unit of analysis (one row = ?).
- bullets: 4 to 6 short observations (time range, geographies, scale, quirks).
- key_columns: 3 to 5 normalized column names from the schema that are most analytically useful.
- suggested_questions: 5 specific questions a leader would actually ask. Mix simple lookups and comparisons. Reference real column names or sample values."""


def dataset_brief_user(dataset_name: str, schema_text: str) -> str:
    return f"DATASET: {dataset_name}\n\n{schema_text}\n\nWrite the brief."


# ── Explore (text-only, no SQL) ──────────────────────────────────────────
EXPLORE_SYS = """You are a data analyst helping a non-technical user understand a dataset without writing or running SQL.

The user has asked a question about the dataset (in plain English). Using only the schema, the dataset brief, and the sample values, write a thoughtful answer.

If the question can only be answered by running a query, say so honestly and recommend they switch to Query mode for that specific question.

Return ONLY valid JSON:
{
  "answer": "a 2 to 4 sentence direct answer",
  "bullets": ["supporting point 1", "supporting point 2", "supporting point 3"],
  "switch_to_query": false
}

Set switch_to_query to true only if the question fundamentally requires running aggregation/filtering SQL to be answered. In that case, your answer should explain why and suggest a concrete SQL angle."""


def explore_user(question: str, dataset_name: str, schema_text: str, brief_text: str | None) -> str:
    parts = [f"DATASET: {dataset_name}", "", schema_text]
    if brief_text:
        parts.extend(["", "DATASET BRIEF:", brief_text])
    parts.extend(["", f"USER QUESTION: {question}"])
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


# ── Dashboard spec (cached per dataset) ──────────────────────────────────
DASHBOARD_SYS = """You design a small, clean dashboard for a tabular dataset based purely on its schema and sample values.

Return ONLY valid JSON in this exact shape:
{
  "insights": ["bullet 1", "bullet 2", "bullet 3", "bullet 4", "bullet 5", "bullet 6"],
  "charts": [
    {
      "title": "Short descriptive title",
      "chart_type": "bar" | "line" | "pie",
      "x_column": "<exact normalized column name from schema>",
      "y_column": "<exact normalized column name from schema OR the literal string 'count'>",
      "aggregation": "sum" | "avg" | "count" | "min" | "max",
      "limit": 15
    }
  ]
}

Rules:
- Produce EXACTLY 6 charts.
- The 6 charts should COVER different angles of the dataset (counts, distributions, top-N rankings, trends over time, share-of-whole). Do not produce 6 variants of the same view.
- Use "bar" for category comparisons. Pick a categorical x and a numeric y.
- Use "line" ONLY when there is a clear time/year/date column for x.
- Use "pie" sparingly — only for share-of-whole with a small number of categories.
- For "count" charts, set y_column to "count" and aggregation to "count".
- For numeric aggregations, y_column MUST reference an actual numeric column from the schema and aggregation MUST be one of sum/avg/min/max.
- x_column and y_column MUST be normalized column names that appear verbatim in the schema (or "count" for y).
- limit between 8 and 25. Use smaller limits for pie charts (<=6).
- insights: 6 short, specific bullets a leader can read out loud. Reference real columns and values from samples."""


def dashboard_user(dataset_name: str, schema_text: str, brief_text: str | None) -> str:
    parts = [f"DATASET: {dataset_name}", "", schema_text]
    if brief_text:
        parts.extend(["", "DATASET BRIEF:", brief_text])
    parts.extend(["", "Design the dashboard."])
    return "\n".join(parts)
