# Pilot data folder

This folder backs `manifest.json`.

| Folder | Source | Notes |
|--------|--------|-------|
| `managed_care/` | CMS Medicaid Managed Care Dashboard (March 2025 release) | Real CSV from `data.cms.gov`, ~19.5K rows. |
| `opioid_prescribing/` | CMS Medicaid Opioid Prescribing Mapping Tool | Real CSV from `data.cms.gov`, ~539K rows (~36 MB). |

Each folder also ships an optional `data_dictionary.pdf` and `methodology.pdf`. These are loaded into the LLM context automatically; they are **not** shown in the UI (per the prototype's "dictionaries optional" stance). User uploads do not require a dictionary.
