"""
Read manifest.json on startup and preload its datasets into the database.

This is intentionally manifest-driven: the app code knows nothing about which
specific datasets are preloaded. To add or swap, edit manifest.json — no code
changes needed.
"""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from ingest.database import Database, Dataset
from ingest.loader import load_file
from ingest.pdf_dictionary import parse_dictionary


MANIFEST_PATH = Path(__file__).parent.parent / "manifest.json"


@st.cache_resource(show_spinner=False)
def build_initial_database() -> Database:
    """Construct the per-user DB and load whatever the manifest lists.

    The @st.cache_resource decorator means we only do this once per session.
    """
    db = Database()
    if not MANIFEST_PATH.exists():
        return db

    with st.spinner("Loading pilot datasets…"):
        manifest = json.loads(MANIFEST_PATH.read_text())
        base_dir = MANIFEST_PATH.parent
        for entry in manifest.get("datasets", []):
            data_path = base_dir / entry["data_path"]
            if not data_path.exists():
                continue

            res = load_file(
                data_path,
                data_path.name,
                suppression_markers=entry.get("suppression_markers") or None,
            )
            dataset = Dataset(
                table=entry["id"],
                name=entry["name"],
                description=entry["description"],
                row_count=len(res.df),
                column_count=len(res.df.columns),
                encoding=res.encoding,
                suppression_markers=res.suppression_markers_found
                                     or entry.get("suppression_markers", []),
                display_names={v: k for k, v in res.column_map.items()},
            )

            dict_path = entry.get("dictionary_path")
            if dict_path:
                full = base_dir / dict_path
                if full.exists():
                    parsed = parse_dictionary(
                        full,
                        list(res.df.columns),
                        dataset.display_names,
                    )
                    dataset.column_descriptions = parsed.column_descriptions
                    dataset.dictionary_text = parsed.full_text

            method_path = entry.get("methodology_path")
            if method_path:
                full = base_dir / method_path
                if full.exists():
                    from ingest.pdf_dictionary import extract_pdf_text
                    dataset.methodology_text = extract_pdf_text(full)

            db.add_dataset(res.df, dataset)

    return db
