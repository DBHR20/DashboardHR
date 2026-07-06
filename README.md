# Evictions & Police Operations dashboard

Interactive D3.js dashboard backed by a small Python script that reads a live
**Google Sheet** and turns it into a single JSON file. The dashboard is a
compact embeddable block (≈ 1180 px wide, ≈ 720 px tall) designed for a
WordPress page via iframe.

Data refreshes **automatically once a week** via GitHub Actions — nobody has to
run anything. The people who maintain the data only ever touch the Google Sheet.

## How it works

```
Private Google Sheet (LOG tab + optional Reports tab)
   │   read-only, via a Google "service account" (robot)
   ▼
scripts/preprocess.py   (Python: gspread, pandas)
   - LOG tab, headers row 3, data from row 4
   - police operations  = 1 only if col T == "Y"  (case-insensitive)
   - living sites evict  = 1 if col W (location) is non-empty
   - people evicted      = numeric value from col AA (else 0)
   - legal basis         = col AH, folded into 4 canonical categories
   - region              = defined per-sheet in CONFIG["google_sheets"]
   - report links        = merged from the sheet's "Reports" tab
   ▼
public/data/dashboard_data.json   (cleaned aggregates only — safe to publish)
   ▼
Static frontend (D3.js + vanilla JS) — public/
   - aggregates DAILY / WEEKLY / MONTHLY in the browser
   - filters: regions, legal basis, indicators, date range
   - click a point → opens that month's report (from the Reports tab)
   ▼
GitHub Pages  ──(iframe)──▶  WordPress page
```

The full spreadsheet stays private; only the **cleaned, aggregated** JSON is
ever published (no free-text, no names — just dates, regions, counts).

## What's in the box

```
dashboard-project-claude/
  .github/workflows/refresh.yml   # weekly auto-refresh + Pages deploy
  scripts/
    preprocess.py                 # the pipeline (Google Sheets → JSON)
    inspect_sheet.py              # one-off helper to inspect a sheet's structure
  public/                         # this whole folder is what gets deployed
    index.html
    dashboard.js
    styles.css
    data/dashboard_data.json      # cleaned data served to the browser
  data_processed/
    validation_report.json        # audit only, never shown in the UI
    reports_tab_seed.tsv          # paste-ready starter for the Sheet's Reports tab
  secrets/                        # service-account key goes here (gitignored)
    README.md
  requirements.txt
```

---

## One-time Google setup (≈ 10 min)

You need a **service account** (a robot Google account) so the script can read a
private sheet unattended. It's free.

1. **[console.cloud.google.com](https://console.cloud.google.com)** → create a
   project (e.g. `eviction-dashboard`).
2. Search **Google Sheets API** → **Enable**. (Also enable **Google Drive API**.)
3. Search **Service Accounts** → **Create service account** (e.g. `dashboard-bot`)
   → skip the optional steps → **Done**. Copy its email
   (`…@….iam.gserviceaccount.com`).
4. Click the account → **Keys → Add key → Create new key → JSON** → download it.
5. Save the file as `secrets/service-account.json` (see `secrets/README.md`).
6. Open the Google Sheet → **Share** → paste the robot's email → **Viewer**.

The Sheet ID lives in CONFIG (`scripts/preprocess.py`,
`CONFIG["google_sheets"]`). It's the long string in the sheet URL between
`/d/` and `/edit`.

---

## Running locally

### 1. Python deps (once)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Make sure `secrets/service-account.json` is in place (see above).

### 3. Refresh the data from the live sheet

```powershell
python scripts/preprocess.py
```

Writes:
- `public/data/dashboard_data.json` (served to the browser)
- `data_processed/dashboard_data.json` (canonical copy)
- `data_processed/validation_report.json` (audit; raw-vs-mapped legal basis, warnings)

The console prints a summary and any warnings.

### 4. Serve the frontend

The page loads JSON via `fetch`, so it needs HTTP (opening `index.html`
directly will not work):

```powershell
cd public
python -m http.server 8000
# open http://localhost:8000/
```

---

## The data workflow (for non-technical maintainers)

Two independent things, both done **entirely in the Google Sheet**:

1. **Eviction data** — edit the `LOG` tab as normal. The weekly job picks up
   whatever is there.
2. **Monthly report links** — when a new report is published, add **one row** to
   the **`Reports`** tab:

   | month   | region       | url                          |
   |---------|--------------|------------------------------|
   | 2026-05 | Dunkirk area | https://…/may-2026-report.pdf |

   - `month` is `YYYY-MM`. `region` matches the region label (e.g. `Dunkirk area`).
   - Clicking a chart point in that month opens the matching report.
   - To create the tab the first time, copy `data_processed/reports_tab_seed.tsv`
     into a new tab named exactly `Reports` (it pre-fills all existing links).

No code changes, ever. Report links read from the sheet override the seed values
baked into `preprocess.py`.

---

## Deploying with GitHub Pages (the automated path)

This publishes the dashboard and refreshes it weekly, hands-off.

1. Push this folder to a GitHub repo (this folder is the repo root).
2. **Settings → Pages → Source = "GitHub Actions"**.
3. **Settings → Secrets and variables → Actions → New repository secret**:
   - Name: `GCP_SERVICE_ACCOUNT_KEY`
   - Value: the **entire contents** of `secrets/service-account.json`
4. **Actions** tab → run **"Refresh dashboard data & deploy to Pages"** once
   (the **Run workflow** button) to publish immediately. After that it runs
   every Monday automatically.

Your dashboard will be live at `https://<user>.github.io/<repo>/`.

### Embed it in WordPress

Add a **Custom HTML** block to the page and paste (use your Pages URL):

```html
<iframe
  src="https://<user>.github.io/<repo>/"
  style="width:100%; height:720px; border:0;"
  loading="lazy"
  title="Evictions and police operations dashboard">
</iframe>
```

Because the iframe points at the Pages URL, WordPress needs no backend access —
and every weekly refresh shows up automatically.

> **Alternative (no GitHub):** you can still host the `public/` folder anywhere
> static (e.g. upload via SFTP to `/wp-content/uploads/...`) and re-upload
> `public/data/dashboard_data.json` after running the script. But then the
> weekly auto-refresh is on you.

---

## Adding a second region (e.g. Calais)

When Calais area gets its own Google Sheet, share it with the robot and add one
entry to `CONFIG["google_sheets"]` in `scripts/preprocess.py`:

```python
"google_sheets": [
    {"sheet_id": "…dunkirk id…", "region": "Dunkirk area"},
    {"sheet_id": "…calais id…",  "region": "Calais area"},
],
```

Nothing else changes — the script reads both and merges them.

## Adapting the code

| Change                              | Where                                                            |
|-------------------------------------|------------------------------------------------------------------|
| Which sheet(s) / region labels      | `CONFIG["google_sheets"]` in `scripts/preprocess.py`             |
| Switch back to local Excel files    | `CONFIG["source"] = "excel"` (reads `data_raw/*.xlsx`)           |
| Service-account key location        | `CONFIG["service_account_file"]` or `GOOGLE_APPLICATION_CREDENTIALS` env |
| Reports tab name                    | `CONFIG["reports_tab_name"]`                                     |
| Different LOG tab name / header row | `CONFIG["sheet_name"]`, `CONFIG["header_row"]`                   |
| Different date / marker / etc. col  | `CONFIG["*_col"]` (column letter, e.g. `"S"`, `"AA"`)            |
| Marker value (currently `"Y"`)      | `CONFIG["operation_marker_value"]`                               |
| Legal-basis mapping                 | `CONFIG["legal_basis_groups"]`                                   |
| Region that must always show        | `CONFIG["extra_regions"]`                                        |
| Seed report links                   | `CONFIG["monthly_reports"]` (prefer the Sheet's Reports tab)     |
| Refresh schedule                    | the `cron:` line in `.github/workflows/refresh.yml`             |
| Accent / palette / line colours     | `:root` variables at top of `public/styles.css`                  |
| Disclaimer / note text              | `data-editable="..."` / `data-explanation="..."` in `index.html` |

## Placeholders (intentional)

All explanatory copy in `index.html` is placeholder text, tagged with
`data-editable="..."` and `data-explanation="..."`. The project deliberately
does not invent methodology — replace these when ready.
