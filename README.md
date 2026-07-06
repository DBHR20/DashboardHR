# Evictions & Police Operations dashboard

Data refreshes **automatically once a week** via GitHub Actions.

## How it works

```
Private Google Sheet (LOG tab + optional Reports tab)
   │   read-only, via a Google "service account" (robot)
   ▼
scripts/preprocess.py   (Python: gspread, pandas)
   ▼
public/data/dashboard_data.json   
   ▼
Static frontend (D3.js + vanilla JS) — public/
   ▼
GitHub Pages  ──(iframe)──▶  WordPress page
```


## Files

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
    validation_report.json        # audit 
    reports_tab_seed.tsv          # paste-ready starter for the Sheet's Reports tab
  secrets/                        
    README.md
  requirements.txt
```




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
