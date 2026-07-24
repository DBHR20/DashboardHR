

from __future__ import annotations

import json
import os
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
from openpyxl.utils import column_index_from_string



CONFIG: dict[str, Any] = {
    "source": "google_sheets",
    "google_sheets": [
        {
            "sheet_id": "1tAyjugD8iWhAcOa5qHvpN4k3p-ISYDBoE2R7mhshR3Y",
            "region": "Dunkirk area",
        },
    ],
    "service_account_file": "secrets/service-account.json",
    "reports_tab_name": "Reports",

    "sheet_name": "LOG",
    "header_row": 3,
    "data_start_row": 4,
    "date_col": "B",
    "operation_marker_col": "C",
    "living_site_col": "D",
    "people_evicted_col": "E",
    "legal_basis_col": "F",
    "region_col": "A",
    "operation_marker_value": "Y",
    "unknown_legal_basis": "Unknown / not specified",
    "default_aggregation": "weekly",
    "region_mapping": {
        "Calais":        "Calais area",
        "Calaisis":      "Calais area",
        "Dunkerque":     "Dunkirk area",
        "Dunkirk":       "Dunkirk area",
        "Dunkerquois":   "Dunkirk area",
        "GS":            "Dunkirk area",
        "Grande-Synthe": "Dunkirk area",
        "Grande_Synthe": "Dunkirk area",
    },

    "extra_regions": [
        "Calais area",
        "Dunkirk area",
    ],
    "legal_basis_groups": [
        {
            "label": "Flagrante delicto",
            "members": [
                "Flagrance",
                "Flagrant délit",
                "Flagrante delicto",
            ],
        },
        {
            "label": "Court decision not communicated",
            "members": [
                "Décision de justice - non-communiquée",
                "Décision de justice non-communiquée",
                "Decision de justice - non-communiquee",
                "Court decision not communicated",
            ],
        },
        {
            "label": "Court decision communicated",
            "members": [
                "Décision de justice - communiquée",
                "Décision de justice communiquée",
                "Decision de justice - communiquee",
                "Court decision communicated",
            ],
        },
        {"label": "Other", "members": []},
    ],
    "legal_basis_default_label": "Other",
    "monthly_reports_index_url": "https://humanrightsobservers.org/fr/monthly-observations/",
    "monthly_reports": {
        # 2026
        "2026-04": {
            "Calais area":  "https://humanrightsobservers.org/wp-content/uploads/2026/05/Monthly-report-Calais-area-April-English.pdf",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2026/05/NM-DK-042026-1.pdf",
        },
        "2026-03": {
            "Calais area":  "https://humanrightsobservers.org/wp-content/uploads/2026/04/Note-mensuelle-Calaisis-Mars-2026-english-version.pdf",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2026/04/Note-mensuelle-Dunkerquois-March-2026-English-version.pdf",
        },
        "2026-02": {
            "Calais area":  "https://humanrightsobservers.org/wp-content/uploads/2026/03/Monthly-report_Calais-area_feb_2026.pdf",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2026/03/Monthly-report_Dunkirk-area_feb_2026.pdf",
        },
        "2026-01": {
            "Calais area":  "https://humanrightsobservers.org/wp-content/uploads/2026/02/Montlhy_report_HRO_KL_01_2026_EN.pdf",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2026/02/Montlhy_report_HRO_DK_01_2026_EN.pdf",
        },
        # 2025
        "2025-12": {
            "Calais area":  "https://humanrightsobservers.org/wp-content/uploads/2026/01/Monthly-report-Calais-12-2025.pdf",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2026/01/Monthly-Report-December-2025-Grande-Synthe.pdf",
        },
        "2025-11": {
            "Calais area":  "https://humanrightsobservers.org/fr/hro-montly-report-calais-area-nov-2025/",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2025/12/NM-DK-1125-ENG.pdf",
        },
        "2025-10": {
            "Calais area":  "https://humanrightsobservers.org/wp-content/uploads/2025/12/Monthly-report-Calais-october-2025-1.pdf",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2025/12/Note-mensuelle-GS-octobre-2025-FR.pdf",
        },
        "2025-09": {
            "Calais area":  "https://humanrightsobservers.org/wp-content/uploads/2025/11/Calais-September-1-1.pdf",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2025/11/Dunkirk-September-2025.pdf",
        },
        "2025-08": {
            "Calais area":  "https://humanrightsobservers.org/wp-content/uploads/2025/10/EN-Note-Mensuelle-Calais-Aout-2025-2.pdf",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2025/10/EN-NM-DK-aout-2025-2-1.pdf",
        },
        "2025-07": {
            "Calais area":  "https://humanrightsobservers.org/wp-content/uploads/2025/08/2025-07_Monthly_Report_Calaisis_EN-1.pdf",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2025/08/2025-07_Monthly_Report_Dunkerquois_EN-1.pdf",
        },
        "2025-06": {
            "Calais area":  "https://humanrightsobservers.org/wp-content/uploads/2025/07/2025_06_Monthly_Report_Calaisis_EN.pdf",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2025/07/2025_06_Monthly_Report_Dunkerquois_EN.pdf",
        },
        "2025-05": {
            "Calais area":  "https://humanrightsobservers.org/wp-content/uploads/2025/06/2025-05_Monthly_Report_Calaisis_EN.pdf",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2025/06/2025-05_Monthly_Report_Dunkerquois_EN.pdf",
        },
        "2025-04": {
            "Calais area":  "https://humanrightsobservers.org/wp-content/uploads/2025/05/2025_Avril_NM_Calaisis_EN.pdf",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2025/05/2025_Avril_NM_Dunkerquois_EN.pdf",
        },
        "2025-03": {
            "Calais area":  "https://humanrightsobservers.org/wp-content/uploads/2025/04/2025_03_Monthly_Report_Calaisis_EN.pdf",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2025/04/2025_03_monthly_report_Dunkerquois_EN.pdf",
        },
        "2025-02": {
            "Calais area":  "https://humanrightsobservers.org/wp-content/uploads/2025/03/2025-02-monthly_report_Calaisis_EN.pdf",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2025/03/2025-02-monthly_report_Dunkerquois_EN.pdf",
        },
        "2025-01": {
            "Calais area":  "https://humanrightsobservers.org/wp-content/uploads/2025/03/2025-01-monthly_report_Calaisis_EN.pdf",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2025/03/2025-01_monthly_report_Dunkerquois_EN.pdf",
        },
        # 2024
        "2024-12": {
            "Calais area":  "https://humanrightsobservers.org/wp-content/uploads/2025/01/2024-12_Monthly_report_Calais_EN.pdf",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2025/01/2024-12_Monthly_report_Dunkirk_EN.pdf",
        },
        "2024-11": {
            "Calais area":  "https://humanrightsobservers.org/wp-content/uploads/2025/01/2024-11_Monthly_report_Calais_EN.pdf.pdf",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2025/01/2024-11_Monthly_report_Dunkirk_EN.pdf.pdf",
        },
        "2024-10": {
            "Calais area":  "https://humanrightsobservers.org/wp-content/uploads/2024/11/2024-10_Monthly_report_Calais_EN.pdf",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2024/11/2024-10_Monthly_report_Dunkirk_EN.pdf",
        },
        "2024-09": {
            "Calais area":  "https://humanrightsobservers.org/wp-content/uploads/2024/11/2024-09_Monthly_report_Calaisis_EN.pdf",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2024/11/2024-09_Monthly_report_Dunkirk_EN.pdf",
        },
        "2024-08": {
            "Calais area":  "https://humanrightsobservers.org/wp-content/uploads/2024/11/2024-08_Monthly_report_Calaisis_EN.pdf",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2024/11/2024-08_Monthly_report_Dunkirk_EN.pdf",
        },
        "2024-07": {
            "Calais area":  "https://humanrightsobservers.org/wp-content/uploads/2024/08/2024-07_Monthly_report_Calais_EN.pdf",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2024/08/2024-07_Monthly_report_DK_EN.pdf",
        },
        "2024-06": {
            "Calais area":  "https://humanrightsobservers.org/wp-content/uploads/2024/07/2024-06_Monthly_report_Calais_ENG.pdf",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2024/07/2024-06_Montlhy_report_Dunkirk_ENG.pdf",
        },
        "2024-05": {
            "Calais area":  "https://humanrightsobservers.org/wp-content/uploads/2024/07/2024-05_Monthly_report_Calais_EN.pdf",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2024/07/2024-05_Monthly_report_Dunkirk_EN.pdf",
        },
        "2024-04": {
            "Calais area":  "https://humanrightsobservers.org/wp-content/uploads/2024/06/2024-04-Monthly-Report-Calais-EN.pdf",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2024/06/2024-04-Monthly-Report-Dunkirk-EN.pdf",
        },
        "2024-03": {
            "Calais area":  "https://humanrightsobservers.org/wp-content/uploads/2024/04/03_Kl-March-2024-EN.pdf",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2024/04/03_Dk-March-2024-EN.pdf",
        },
        "2024-02": {
            "Calais area":  "https://humanrightsobservers.org/wp-content/uploads/2024/03/Monthly-bulletin-February-2024-Calais.pdf",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2024/03/monthly-bulletin-February-2024-Dunkirk.pdf",
        },
        "2024-01": {
            "Calais area":  "https://humanrightsobservers.org/wp-content/uploads/2024/02/Calais-January-2024-EN.pdf",
            "Dunkirk area": "https://humanrightsobservers.org/wp-content/uploads/2024/02/Dunkirk-January-2024-EN.pdf",
        },
    },

    "data_raw_dir": "data_raw",
    "data_processed_dir": "data_processed",
    "frontend_data_dir": "public/data",
}

GOOGLE_SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _col_index(letter: str) -> int:
    """Convert spreadsheet column letter to 0-based index used by pandas."""
    return column_index_from_string(letter) - 1


def _infer_region(filename: str, mapping: dict[str, str]) -> str | None:
    """Return canonical region for a filename, or None if no mapping matches."""
    name = filename.lower()
    for key, canonical in mapping.items():
        if key.lower() in name:
            return canonical
    return None


def _parse_date(value: Any) -> date | None:
    """Convert serials, datetime objects, and date strings to a date."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, (int, float)):
        if pd.isna(value):
            return None
        try:
            return (datetime(1899, 12, 30) + timedelta(days=float(value))).date()
        except (OverflowError, ValueError):
            return None
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        # A bare numeric string is a serial (Google "UNFORMATTED_VALUE" can
        # hand dates back as numbers rendered as text in some locales).
        if re.fullmatch(r"\d+(\.\d+)?", s):
            try:
                return (datetime(1899, 12, 30) + timedelta(days=float(s))).date()
            except (OverflowError, ValueError):
                pass
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%d.%m.%Y"):
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue
        try:
            return pd.to_datetime(s, dayfirst=True, errors="raise").date()
        except (ValueError, TypeError):
            return None
    return None


def _is_truthy_marker(value: Any, expected: str) -> bool:
    if value is None:
        return False
    if isinstance(value, float) and pd.isna(value):
        return False
    return str(value).strip().lower() == expected.strip().lower()


def _is_non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, float) and pd.isna(value):
        return False
    return str(value).strip() != ""


def _clean_legal_basis(value: Any, unknown_label: str) -> str:
    if not _is_non_empty(value):
        return unknown_label
    return re.sub(r"\s+", " ", str(value).strip())


_ACCENT_TABLE = str.maketrans(
    "àáâãäåçèéêëìíîïñòóôõöùúûüýÿÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜÝŸ",
    "aaaaaaceeeeiiiinooooouuuuyyAAAAAACEEEEIIIINOOOOOUUUUYY",
)


def _normalize(s: str) -> str:
    """Lower-case, strip accents and collapse whitespace for tolerant matching."""
    return re.sub(r"\s+", " ", s.translate(_ACCENT_TABLE).lower()).strip()


def _apply_legal_groups(label: str, cfg: dict[str, Any]) -> str:
    """Map a raw legal-basis label to one of the configured group labels."""
    groups = cfg.get("legal_basis_groups") or []
    default = cfg.get("legal_basis_default_label", "Other")
    if not label:
        return default
    norm = _normalize(label)
    for group in groups:
        for member in group.get("members", []):
            if _normalize(member) == norm:
                return group["label"]
    return default


def _parse_people_count(value: Any) -> tuple[int, str]:
    """Return (count, status) where status is 'ok' | 'missing' | 'non_numeric'."""
    if value is None:
        return 0, "missing"
    if isinstance(value, float) and pd.isna(value):
        return 0, "missing"
    if isinstance(value, bool):
        return int(value), "ok"
    if isinstance(value, (int, float)):
        n = int(round(float(value)))
        return (n, "ok") if n >= 0 else (0, "non_numeric")
    s = str(value).strip().replace(",", ".")
    if not s:
        return 0, "missing"
    try:
        n = int(round(float(s)))
        return (n, "ok") if n >= 0 else (0, "non_numeric")
    except ValueError:
        m = re.match(r"^\s*~?\s*(\d+)", s)
        if m:
            return int(m.group(1)), "ok"
        return 0, "non_numeric"


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _new_report(source_label: str, region: str | None) -> dict[str, Any]:
    return {
        "file": source_label,
        "region": region,
        "rows_read": 0,
        "rows_valid_dated": 0,
        "rows_excluded_invalid_date": 0,
        "rows_with_missing_people_evicted": 0,
        "rows_with_non_numeric_people_evicted": 0,
        "total_police_operations": 0,
        "total_living_sites_evicted": 0,
        "total_people_evicted": 0,
        "raw_legal_basis_counts": {},
        "warnings": [],
    }


# ---------------------------------------------------------------------------
# Core processing (shared by both the Google Sheets and Excel readers)
# ---------------------------------------------------------------------------


def process_dataframe(
    df: pd.DataFrame,
    region: str,
    source_label: str,
    cfg: dict[str, Any],
    report: dict[str, Any],
) -> list[dict[str, Any]]:
    """Turn a positional DataFrame (LOG sheet) into cleaned row records.

    `df` must be 0-indexed positionally; column letters in CONFIG map to
    integer positions. All the indicator/cleaning logic lives here so the
    Google Sheets and Excel readers behave identically.
    """
    cols = {
        "region": _col_index(cfg["region_col"]),
        "date": _col_index(cfg["date_col"]),
        "marker": _col_index(cfg["operation_marker_col"]),
        "living": _col_index(cfg["living_site_col"]),
        "people": _col_index(cfg["people_evicted_col"]),
        "legal": _col_index(cfg["legal_basis_col"]),
    }
    if df.shape[1] <= max(cols.values()):
        report["warnings"].append(
            f"Source only has {df.shape[1]} columns; expected at least "
            f"{max(cols.values()) + 1} based on configured column letters."
        )
        return []

    report["rows_read"] = int(len(df))

    rows: list[dict[str, Any]] = []
    marker_seen = False
    unmapped_region_seen = False

    for i, raw in df.iterrows():
        region_value = raw.iloc[cols["region"]]
        date_value = raw.iloc[cols["date"]]
        marker_value = raw.iloc[cols["marker"]]
        living_value = raw.iloc[cols["living"]]
        people_value = raw.iloc[cols["people"]]
        legal_value = raw.iloc[cols["legal"]]

        parsed_date = _parse_date(date_value)
        people_count, people_status = _parse_people_count(people_value)

        if people_status == "missing":
            report["rows_with_missing_people_evicted"] += 1
        elif people_status == "non_numeric":
            report["rows_with_non_numeric_people_evicted"] += 1

        if parsed_date is None:
            # Skip rows that are entirely blank.
            if not any(_is_non_empty(v) for v in (marker_value, living_value, people_value, legal_value)):
                continue
            report["rows_excluded_invalid_date"] += 1
            continue

        is_operation = _is_truthy_marker(marker_value, cfg["operation_marker_value"])
        is_living = _is_non_empty(living_value)
        if is_operation:
            marker_seen = True

        raw_legal = _clean_legal_basis(legal_value, cfg["unknown_legal_basis"])
        mapped_legal = _apply_legal_groups(raw_legal, cfg)
        report["raw_legal_basis_counts"][raw_legal] = (
            report["raw_legal_basis_counts"].get(raw_legal, 0) + 1
        )

        row_region = (
            _infer_region(str(region_value), cfg["region_mapping"])
            if _is_non_empty(region_value) else None
        )
        if row_region is None:
            row_region = region
            unmapped_region_seen = True

        rows.append({
            "date": parsed_date.isoformat(),
            "region": row_region,
            "legal_basis": mapped_legal,
            "police_operations": 1 if is_operation else 0,
            "living_sites_evicted": 1 if is_living else 0,
            "people_evicted": people_count,
            "source_rows": 1,
            "source_file": source_label,
            "source_excel_row": int(i) + cfg["header_row"] + 1,
        })

    report["rows_valid_dated"] = len(rows)
    report["total_police_operations"] = sum(r["police_operations"] for r in rows)
    report["total_living_sites_evicted"] = sum(r["living_sites_evicted"] for r in rows)
    report["total_people_evicted"] = sum(r["people_evicted"] for r in rows)

    if rows and not marker_seen:
        report["warnings"].append(
            f"No row in '{source_label}' contained '{cfg['operation_marker_value']}' "
            f"in column {cfg['operation_marker_col']}. Police operations will be 0."
        )

    if unmapped_region_seen:
        report["warnings"].append(
            f"Some rows in '{source_label}' had a blank or unrecognised region in column "
            f"{cfg['region_col']}; those rows were labelled '{region}' (the source's default). "
            "Edit CONFIG['region_mapping'] if a new spelling needs to be added."
        )

    return rows


# ---------------------------------------------------------------------------
# Google Sheets reader
# ---------------------------------------------------------------------------


def _gspread_client(cfg: dict[str, Any]):
    """Authorize a read-only gspread client from the service-account key."""
    import gspread
    from google.oauth2.service_account import Credentials

    key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not key_path:
        key_path = str(_project_root() / cfg["service_account_file"])
    if not Path(key_path).exists():
        raise FileNotFoundError(
            f"Service-account key not found at {key_path}. Place it there, or "
            "set GOOGLE_APPLICATION_CREDENTIALS to point at it."
        )
    creds = Credentials.from_service_account_file(key_path, scopes=GOOGLE_SCOPES)
    return gspread.authorize(creds)


def _sheet_grid(spreadsheet, tab_name: str) -> list[list[Any]]:
    """Fetch a tab as a list-of-rows of UNFORMATTED values (dates as serials)."""
    result = spreadsheet.values_get(
        f"'{tab_name}'",
        params={
            "valueRenderOption": "UNFORMATTED_VALUE",
            "dateTimeRenderOption": "SERIAL_NUMBER",
        },
    )
    return result.get("values", [])


def _grid_to_dataframe(grid: list[list[Any]], cfg: dict[str, Any]) -> pd.DataFrame:
    """Build a positional DataFrame of the LOG data rows (row 4 onward)."""
    data_rows = grid[cfg["data_start_row"] - 1:]
    needed = max(
        _col_index(cfg[c])
        for c in ("date_col", "operation_marker_col", "living_site_col",
                  "people_evicted_col", "legal_basis_col")
    ) + 1
    width = max([len(r) for r in data_rows], default=0)
    width = max(width, needed)
    padded = [list(r) + [None] * (width - len(r)) for r in data_rows]
    return pd.DataFrame(padded)


def read_google_sheet(
    client, sheet_id: str, region: str, cfg: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Read one online spreadsheet's LOG tab. Returns (cleaned_rows, report)."""
    import gspread

    spreadsheet = client.open_by_key(sheet_id)
    source_label = f"{spreadsheet.title} [{sheet_id[:8]}…]"
    report = _new_report(source_label, region)

    try:
        grid = _sheet_grid(spreadsheet, cfg["sheet_name"])
    except gspread.exceptions.APIError as exc:
        report["warnings"].append(f"Could not read tab '{cfg['sheet_name']}': {exc}")
        return [], report

    if len(grid) < cfg["data_start_row"]:
        report["warnings"].append(
            f"Tab '{cfg['sheet_name']}' has fewer than {cfg['data_start_row']} rows."
        )
        return [], report

    df = _grid_to_dataframe(grid, cfg)
    rows = process_dataframe(df, region, source_label, cfg, report)
    return rows, report


def read_reports_tab(
    client, sheet_id: str, default_region: str, cfg: dict[str, Any]
) -> tuple[dict[str, dict[str, str]], list[str]]:
    """Read a sheet's optional "Reports" tab into {month: {region: url}}.

    Returns (reports, warnings). Missing tab is not an error — returns ({}, []).
    Expected headers (row 1, case-insensitive): month | region | url.
    `region` is optional per row; falls back to the sheet's region.
    """
    import gspread

    tab = cfg.get("reports_tab_name", "Reports")
    warnings: list[str] = []
    try:
        grid = _sheet_grid(client.open_by_key(sheet_id), tab)
    except gspread.exceptions.WorksheetNotFound:
        return {}, warnings
    except gspread.exceptions.APIError:
        # Tab simply doesn't exist (range error) — treat as no reports.
        return {}, warnings

    if not grid:
        return {}, warnings

    header = [str(h).strip().lower() for h in grid[0]]
    try:
        i_month = header.index("month")
        i_url = header.index("url")
    except ValueError:
        warnings.append(
            f"'{tab}' tab found but missing 'month' and/or 'url' header columns; "
            "ignoring it."
        )
        return {}, warnings
    i_region = header.index("region") if "region" in header else None

    reports: dict[str, dict[str, str]] = {}
    for row in grid[1:]:
        if len(row) <= max(filter(None, [i_month, i_url, i_region])):
            row = list(row) + [""] * (max(i_month, i_url, i_region or 0) + 1 - len(row))
        month = str(row[i_month]).strip()
        url = str(row[i_url]).strip()
        if not month or not url:
            continue
        if not re.fullmatch(r"\d{4}-\d{2}", month):
            warnings.append(f"'{tab}': skipping row with bad month {month!r} (need YYYY-MM).")
            continue
        region = default_region
        if i_region is not None and str(row[i_region]).strip():
            region = str(row[i_region]).strip()
        reports.setdefault(month, {})[region] = url

    return reports, warnings


# ---------------------------------------------------------------------------
# Excel reader (fallback: source = "excel")
# ---------------------------------------------------------------------------


def read_excel_file(path: Path, cfg: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Read one local .xlsx file. Returns (cleaned_rows, report)."""
    region = _infer_region(path.name, cfg["region_mapping"])
    report = _new_report(path.name, region)
    if region is None:
        report["warnings"].append(
            f"No region could be inferred from '{path.name}'. "
            "Rows will be labelled 'Unknown region'. Edit CONFIG['region_mapping']."
        )
        region = "Unknown region"

    try:
        df = pd.read_excel(
            path,
            sheet_name=cfg["sheet_name"],
            header=cfg["header_row"] - 1,
            engine="openpyxl",
        )
    except ValueError as exc:
        report["warnings"].append(f"Could not open sheet '{cfg['sheet_name']}': {exc}")
        return [], report

    rows = process_dataframe(df.reset_index(drop=True), region, path.name, cfg, report)
    return rows, report


# ---------------------------------------------------------------------------
# Aggregation + payload
# ---------------------------------------------------------------------------


def weekly_aggregate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convenience weekly aggregate written to JSON output for inspection."""
    buckets: dict[tuple[str, str, str], dict[str, Any]] = {}
    for r in rows:
        d = date.fromisoformat(r["date"])
        start = _week_start(d)
        end = start + timedelta(days=6)
        key = (start.isoformat(), r["region"], r["legal_basis"])
        b = buckets.get(key)
        if b is None:
            b = {
                "period_start": start.isoformat(),
                "period_end": end.isoformat(),
                "aggregation": "weekly",
                "region": r["region"],
                "legal_basis": r["legal_basis"],
                "police_operations": 0,
                "living_sites_evicted": 0,
                "people_evicted": 0,
                "source_rows": 0,
            }
            buckets[key] = b
        b["police_operations"] += r["police_operations"]
        b["living_sites_evicted"] += r["living_sites_evicted"]
        b["people_evicted"] += r["people_evicted"]
        b["source_rows"] += r["source_rows"]
    return sorted(buckets.values(), key=lambda x: (x["period_start"], x["region"], x["legal_basis"]))


def _merge_reports(
    seed: dict[str, dict[str, str]],
    from_sheet: dict[str, dict[str, str]],
) -> dict[str, dict[str, str]]:
    """Merge sheet-provided report links on top of the seed (sheet wins)."""
    merged: dict[str, dict[str, str]] = {m: dict(v) for m, v in seed.items()}
    for month, by_region in from_sheet.items():
        merged.setdefault(month, {}).update(by_region)
    return merged


def build_payload(
    cleaned_rows: list[dict[str, Any]],
    file_reports: list[dict[str, Any]],
    monthly_reports: dict[str, dict[str, str]],
    cfg: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    data_regions = {r["region"] for r in cleaned_rows}
    region_order: list[str] = []
    for r in cfg["extra_regions"]:
        if r not in region_order:
            region_order.append(r)
    for r in sorted(data_regions):
        if r not in region_order:
            region_order.append(r)

    legal_order: list[str] = []
    for group in cfg.get("legal_basis_groups") or []:
        label = group.get("label")
        if label and label not in legal_order:
            legal_order.append(label)
    default = cfg.get("legal_basis_default_label")
    if default and default not in legal_order:
        legal_order.append(default)

    dates = [r["date"] for r in cleaned_rows]
    date_range = {
        "min": min(dates) if dates else None,
        "max": max(dates) if dates else None,
    }

    indicators = [
        {"key": "police_operations",    "label": "Police operations"},
        {"key": "living_sites_evicted", "label": "Living sites evicted"},
        {"key": "people_evicted",       "label": "People evicted"},
    ]

    totals = {
        "police_operations":     sum(r["police_operations"]     for r in cleaned_rows),
        "living_sites_evicted":  sum(r["living_sites_evicted"]  for r in cleaned_rows),
        "people_evicted":        sum(r["people_evicted"]        for r in cleaned_rows),
        "source_rows":           sum(r["source_rows"]           for r in cleaned_rows),
    }

    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")

    payload = {
        "generated_at": generated_at,
        "config": {
            "operation_marker_value": cfg["operation_marker_value"],
            "default_aggregation": cfg["default_aggregation"],
        },
        "regions": region_order,
        "legal_basis_categories": legal_order,
        "indicators": indicators,
        "date_range": date_range,
        "totals": totals,
        "monthly_reports_index_url": cfg.get("monthly_reports_index_url", ""),
        "monthly_reports": dict(sorted(monthly_reports.items(), reverse=True)),
        "cleaned_records": cleaned_rows,
        "weekly": weekly_aggregate(cleaned_rows),
    }

    raw_legal_breakdown: dict[str, int] = {}
    for f in file_reports:
        for label, count in f.get("raw_legal_basis_counts", {}).items():
            raw_legal_breakdown[label] = raw_legal_breakdown.get(label, 0) + count

    validation = {
        "generated_at": generated_at,
        "files_count": len(file_reports),
        "files_processed": file_reports,
        "rows_read": sum(f["rows_read"] for f in file_reports),
        "valid_dated_rows": sum(f["rows_valid_dated"] for f in file_reports),
        "excluded_invalid_or_missing_dates": sum(f["rows_excluded_invalid_date"] for f in file_reports),
        "rows_with_missing_people_evicted": sum(f["rows_with_missing_people_evicted"] for f in file_reports),
        "rows_with_non_numeric_people_evicted": sum(f["rows_with_non_numeric_people_evicted"] for f in file_reports),
        "total_police_operations": totals["police_operations"],
        "total_living_sites_evicted": totals["living_sites_evicted"],
        "total_people_evicted": totals["people_evicted"],
        "unique_legal_basis_categories": legal_order,
        "legal_basis_raw_breakdown": dict(sorted(raw_legal_breakdown.items())),
        "legal_basis_groups": cfg.get("legal_basis_groups"),
        "regions": region_order,
        "date_range": date_range,
        "monthly_reports_months": sorted(monthly_reports.keys(), reverse=True),
        "warnings": [w for f in file_reports for w in f["warnings"]],
    }

    return payload, validation


# ---------------------------------------------------------------------------
# Source dispatch
# ---------------------------------------------------------------------------


def collect_from_google_sheets(
    cfg: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, str]]]:
    client = _gspread_client(cfg)
    all_rows: list[dict[str, Any]] = []
    file_reports: list[dict[str, Any]] = []
    sheet_reports: dict[str, dict[str, str]] = {}

    for entry in cfg["google_sheets"]:
        sheet_id = entry["sheet_id"]
        region = entry["region"]
        print(f"  Reading Google Sheet {sheet_id[:8]}… as region {region!r} ...")
        rows, report = read_google_sheet(client, sheet_id, region, cfg)
        all_rows.extend(rows)
        file_reports.append(report)
        for w in report["warnings"]:
            print(f"    WARN: {w}")

        reports, rwarn = read_reports_tab(client, sheet_id, region, cfg)
        for month, by_region in reports.items():
            sheet_reports.setdefault(month, {}).update(by_region)
        for w in rwarn:
            print(f"    WARN: {w}")
        if reports:
            print(f"    Reports tab: {sum(len(v) for v in reports.values())} link(s) "
                  f"across {len(reports)} month(s).")

    return all_rows, file_reports, sheet_reports


def collect_from_excel(
    cfg: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, str]]]:
    root = _project_root()
    raw_dir = root / cfg["data_raw_dir"]
    if not raw_dir.exists():
        raise FileNotFoundError(f"raw data folder does not exist: {raw_dir}")
    files = sorted(p for p in raw_dir.glob("*.xlsx") if not p.name.startswith("~$"))
    if not files:
        raise FileNotFoundError(f"no .xlsx files found in {raw_dir}")
    print(f"Found {len(files)} Excel file(s) in {raw_dir}")

    all_rows: list[dict[str, Any]] = []
    file_reports: list[dict[str, Any]] = []
    for f in files:
        print(f"  Reading {f.name} ...")
        rows, report = read_excel_file(f, cfg)
        all_rows.extend(rows)
        file_reports.append(report)
        for w in report["warnings"]:
            print(f"    WARN: {w}")
    return all_rows, file_reports, {}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    cfg = CONFIG
    root = _project_root()
    processed_dir = root / cfg["data_processed_dir"]
    frontend_dir = root / cfg["frontend_data_dir"]

    source = cfg.get("source", "google_sheets")
    print(f"Source: {source}")

    try:
        if source == "google_sheets":
            all_rows, file_reports, sheet_reports = collect_from_google_sheets(cfg)
        elif source == "excel":
            all_rows, file_reports, sheet_reports = collect_from_excel(cfg)
        else:
            print(f"ERROR: unknown source {source!r}", file=sys.stderr)
            return 1
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    monthly_reports = _merge_reports(cfg.get("monthly_reports", {}), sheet_reports)

    payload, validation = build_payload(all_rows, file_reports, monthly_reports, cfg)

    processed_dir.mkdir(parents=True, exist_ok=True)
    frontend_dir.mkdir(parents=True, exist_ok=True)

    out_data = processed_dir / "dashboard_data.json"
    out_validation = processed_dir / "validation_report.json"
    out_frontend = frontend_dir / "dashboard_data.json"

    for path in (out_data, out_frontend):
        with path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)

    with out_validation.open("w", encoding="utf-8") as fh:
        json.dump(validation, fh, ensure_ascii=False, indent=2)

    print()
    print("Validation summary")
    print("------------------")
    print(f"  Sources:                           {validation['files_count']}")
    for fr in file_reports:
        print(f"   - {fr['file']}: region={fr['region']!r}, "
              f"rows={fr['rows_read']}, dated={fr['rows_valid_dated']}, "
              f"bad_date={fr['rows_excluded_invalid_date']}, "
              f"police_ops={fr['total_police_operations']}, "
              f"living_sites={fr['total_living_sites_evicted']}, "
              f"people={fr['total_people_evicted']}")
    print(f"  Regions (incl. configured extras): {validation['regions']}")
    print(f"  Legal categories:                  {validation['unique_legal_basis_categories']}")
    print(f"  Raw legal-basis breakdown:")
    for k, v in validation["legal_basis_raw_breakdown"].items():
        print(f"     {k!r}: {v}")
    print(f"  Date range:                        {validation['date_range']}")
    print(f"  Police operations:                 {validation['total_police_operations']}")
    print(f"  Living sites evicted:              {validation['total_living_sites_evicted']}")
    print(f"  People evicted:                    {validation['total_people_evicted']}")
    print(f"  Rows missing 'people evicted':     {validation['rows_with_missing_people_evicted']}")
    print(f"  Rows non-numeric 'people evicted': {validation['rows_with_non_numeric_people_evicted']}")
    print(f"  Monthly-report months:             {len(validation['monthly_reports_months'])}")
    if validation["warnings"]:
        print("  Warnings:")
        for w in validation["warnings"]:
            print(f"    - {w}")
    print()
    print(f"Wrote {out_data}")
    print(f"Wrote {out_frontend}")
    print(f"Wrote {out_validation}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
