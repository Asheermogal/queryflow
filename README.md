# Data Explorer

Exploratory analytics for any CSV or Excel dataset.

Upload a file (or pick one of the preloaded pilots), and Data Explorer will:

- write a one-shot **dataset brief** so you know what you're looking at
- let you **chat** in two modes — *Explore* for plain-English insights, *Query* for SQL
- generate editable SQL that **does not run until you click Run**
- show results, an LLM analysis, and an auto-picked chart
- offer a **custom chart builder** under every result set
- build a full **dashboard** with multiple charts and high-level insights on demand

Two CMS pilot datasets are pre-loaded for the demo: **Medicaid Managed Care Dashboard** (~19.5K rows, real) and **Medicaid Opioid Prescribing Rates by Geography** (synthetic; swap in the real CSV later).

---

## Deploy on Streamlit Cloud

1. Push this repo to GitHub.
2. On [share.streamlit.io](https://share.streamlit.io), create a new app pointing at this repo, **entry path `app.py`**, branch `main`.
3. Open the app's **Settings → Secrets** and add:

   ```toml
   app_password = "choose-a-strong-password"
   openai_api_key = "sk-..."        # or anthropic_api_key / google_api_key
   ```

   Save. The app reboots automatically.

That's it. Share the URL + password.

---

## Run it locally

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# edit secrets.toml — set app_password and one provider key
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501).

---

## How to use it

1. **Sign in** with the password from `secrets.toml`.
2. **Pick a dataset** in the sidebar — pilots or your own upload.
3. Read the **dataset brief** in the right rail (one cached LLM call per dataset).
4. In the chat, pick a mode:
   - **Explore** — get plain-English insights without writing SQL.
   - **Query** — the model drafts SQL; you review and edit it; click **Run query** to execute.
5. Under each result set, expand **+ Custom chart** to plot whatever you want from the result columns.
6. Click **Explore the dataset in a dashboard** in the right rail to generate a full dashboard, then **Show the Dashboard** to open it. Use **Back to chat** to return — your chat is preserved.

---

## Uploading your own dataset

Sidebar → **Upload new** → pick a CSV or XLSX file (up to 200 MB). The schema is scanned, types are coerced, and a brief is generated on the first interaction.

Best results: first row should be column headers.

---

## Customizing

| Thing | Where |
|-------|-------|
| App name, version, model defaults, upload limits, dashboard sizing | [core/config.py](core/config.py) |
| Colors, fonts, spacing, radii | [core/design.py](core/design.py) |
| Preloaded datasets | [manifest.json](manifest.json) |
| Prompts | [core/prompts.py](core/prompts.py) |

---

## Project structure

```
app.py                       Entry point + view router (chat | dashboard)
manifest.json                Declarative list of preloaded datasets
requirements.txt
.streamlit/
  config.toml                Base Streamlit theme
  secrets.toml.example       Password + provider API keys
core/
  config.py                  App identity, upload limits, model defaults, sizing
  design.py                  Design tokens (color/font/spacing)
  auth.py                    Password gate
  bootstrap.py               Reads manifest, preloads datasets
  prompts.py                 LLM prompts (brief, sql, analysis, explore, dashboard)
  dataset_brief.py           Cached dataset brief (one LLM call per dataset)
llm/
  base.py                    Abstract LLM client
  registry.py                Provider registry
  openai_client.py
  anthropic_client.py
  gemini_client.py
ingest/
  loader.py                  CSV/XLSX ingestion
  schema.py                  Schema scanner
  pdf_dictionary.py          Optional PDF dictionary parser (kept for manifest pilots)
  database.py                In-memory SQLite wrapper
ui/
  styles.py                  Global CSS
  components.py              Header, footer, atoms
  sidebar.py                 Provider/model + dataset picker + upload
  query_flow.py              Chat: Explore/Query modes, SQL editor, Run, results
  dataset_panel.py           Right rail: stats + brief + dashboard buttons
  dashboard.py               Full-width dashboard view + custom chart builder
  custom_chart.py            Reusable chart builder (works on result df OR full table)
  chart.py                   Plotly renderer from a structured chart spec
data/
  managed_care/              CMS Managed Care Dashboard CSV (real)
  opioid_prescribing/        Synthetic CMS-style opioid prescribing CSV
```

---

## License

Code is yours. The Managed Care CSV is public domain CMS data. The Opioid Prescribing CSV is synthetic.
