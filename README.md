# Ask the Data

A conversational analytics app for any tabular dataset.

Upload a CSV or Excel file, ask questions in plain English, get back editable SQL, real results, a written analysis, and a chart. Optional PDF data dictionary gives the model precise column definitions.

Two CMS pilot datasets are pre-loaded out of the box: **Medicaid Managed Care Dashboard** (~20K rows) and **Medicaid Opioid Prescribing Rates by Geography** (~540K rows).

---

## What it does

- **Plain-English queries.** Type "which MCOs have the highest dental utilization in Arizona" — the app generates a SQL query, lets you edit it, runs it on the dataset, and writes up the result.
- **Any LLM.** Works with OpenAI, Anthropic, or Google. Pick the provider and specific model in the sidebar — the active model name is always shown in the page header.
- **Any dataset.** Two pilots are pre-loaded, but you can upload any CSV or Excel file alongside an optional PDF data dictionary; the schema gets scanned and the dictionary gets fed to the model as context. Nothing about your two pilots is hardcoded in the app logic — they're loaded from `manifest.json`.
- **Resilient ingestion.** Handles non-UTF-8 encodings, suppression markers (`*`, `N/A`, `--`), comma-formatted numbers (`12,345`), and column-name normalization automatically.
- **Conversation memory.** Follow-up questions use the prior turns as context, so you can drill in without re-stating everything.

---

## Deploy in 5 minutes (recommended path)

This is the path optimized for "no setup pain" — your end user just clicks a link.

### 1. Get an OpenAI API key
[platform.openai.com/api-keys](https://platform.openai.com/api-keys) → "Create new secret key" → copy it. (Or grab a key from Anthropic or Google — the app supports all three.)

### 2. Push this folder to GitHub
Create a new GitHub repo (private is fine), then from this folder:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

### 3. Connect to Streamlit Community Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **New app**, pick your repo, set the main file to `app.py`, and deploy.
3. Once deployed, click the three-dot menu → **Settings** → **Secrets**, and paste:
   ```toml
   app_password = "choose-a-strong-password"
   openai_api_key = "sk-..."
   ```
   Save. The app reboots automatically.

### 4. Share the URL
Streamlit Cloud gives you a URL like `https://your-app.streamlit.app`. Send it to your uncle along with the password. He opens the link, enters the password, and is in.

That's it. He never sees a terminal, never installs anything.

---

## Run it locally (developer path)

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml — set app_password, optionally bake in an API key

# 3. Run
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501).

---

## How to use it

1. **Sign in** with the password from `secrets.toml`.
2. **Pick a dataset** in the sidebar (or upload a new one).
3. **Configure the model** — provider (OpenAI / Anthropic / Google) and specific model. If you've baked the API key into `secrets.toml`, you're done. Otherwise paste your key here.
4. **Click a starter question** the app suggests, or type your own. Examples that work well:
   - "Which states have the lowest opioid prescribing rates?"
   - "Show me the top 10 MCOs by total active patients in Arizona"
   - "How has the opioid prescribing rate changed nationally over time?"
5. **Edit the SQL** if you want — it's just a SQLite query.
6. **Click Run.** Results show up, then an analysis and chart appear.
7. **Ask a follow-up.** Prior turns are remembered for context.

---

## Uploading your own dataset

Sidebar → **Upload new** → pick a CSV or Excel file. Optionally upload a PDF data dictionary alongside. Click **Load dataset**.

Best results:
- Make sure the first row is column headers.
- If your data uses a suppression marker other than `*`, `N/A`, `--`, or `?`, mention it in your first question (or add it to `DEFAULT_SUPPRESSION_MARKERS` in `ingest/loader.py`).
- A data dictionary PDF *dramatically* improves answer quality. The app parses it and heuristically maps each column to its description; the full text is also given to the LLM as context.

---

## Customizing the look

All visual decisions — colors, fonts, spacing, radii — live in `core/design.py`. Change a token there and the entire app re-themes.

Type scale, accent color, and font choices are at the top of the file.

---

## Project structure

```
app.py                       # Entry point
manifest.json                # Declarative list of preloaded datasets
requirements.txt
.streamlit/
  config.toml                # Base Streamlit theme
  secrets.toml.example       # Password + optional API keys
core/
  design.py                  # Design tokens (colors, fonts, spacing)
  auth.py                    # Password gate
  bootstrap.py               # Reads manifest, preloads datasets
  prompts.py                 # LLM prompt templates
llm/
  base.py                    # Abstract LLM client
  registry.py                # Provider registry
  openai_client.py
  anthropic_client.py
  gemini_client.py
ingest/
  loader.py                  # CSV/Excel ingestion (encoding, types, suppression)
  schema.py                  # Schema scanning + LLM-ready prompt text
  pdf_dictionary.py          # PDF dictionary parsing
  database.py                # In-memory SQLite wrapper
ui/
  styles.py                  # Global CSS (overrides Streamlit defaults)
  components.py              # Reusable atoms (badge, hero, footer, etc.)
  sidebar.py                 # Settings + dataset management
  schema_view.py             # Schema panel
  query_flow.py              # The conversational query flow
  chart.py                   # Chart rendering from LLM chart_spec
data/
  managed_care/              # Pilot dataset 1
  opioid_prescribing/        # Pilot dataset 2
```

---

## Why these architectural choices

- **Streamlit + SQLite.** Single-command deploy, no servers to manage. Per-session in-memory database means each user's data is isolated and never persisted server-side.
- **Provider-agnostic LLM layer.** A new model release means changing one entry in `llm/<provider>_client.py`. No prompt code changes.
- **Chart spec, not freeform plot code.** The model emits structured JSON (`chart_type`, `x_column`, `y_column`, `aggregation`, `limit`); we render it deterministically with Plotly. This prevents the entire class of "the chart counted instances instead of summing values" bugs.
- **Manifest-driven preloading.** App code knows nothing about specific datasets — `manifest.json` declares what to load. Swap pilots without touching code.

---

## License & data

The app code is yours. The pilot datasets are public domain: [data.medicaid.gov](https://data.medicaid.gov) (Managed Care Dashboard, Opioid Prescribing Rates by Geography). All credit to CMS.
