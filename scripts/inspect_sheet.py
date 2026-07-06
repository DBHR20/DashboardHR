"""
One-off: inspect the live Google Sheet structure so we know how to adapt
preprocess.py. Read-only. Safe to delete afterwards.

    python scripts/inspect_sheet.py
"""
from __future__ import annotations

from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials
from openpyxl.utils import get_column_letter

SHEET_ID = "1tAyjugD8iWhAcOa5qHvpN4k3p-ISYDBoE2R7mhshR3Y"
KEY_PATH = Path(__file__).resolve().parent.parent / "secrets" / "service-account.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def main() -> int:
    if not KEY_PATH.exists():
        print(f"ERROR: key not found at {KEY_PATH}")
        return 1

    creds = Credentials.from_service_account_file(str(KEY_PATH), scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)

    print(f"Spreadsheet title: {sh.title!r}\n")
    print("Tabs:")
    for ws in sh.worksheets():
        print(f"  - {ws.title!r}: {ws.row_count} rows x {ws.col_count} cols")

    # Show LOG headers (row 3) with their Excel column letters.
    try:
        log = sh.worksheet("LOG")
        header = log.row_values(3)
        print("\nLOG header row (row 3):")
        for i, name in enumerate(header, start=1):
            if name.strip():
                print(f"  {get_column_letter(i):>3} ({i:>3}): {name!r}")
        # Peek at the first data row to sanity-check.
        first = log.row_values(4)
        print(f"\nFirst LOG data row has {len(first)} non-trailing cells.")
    except gspread.WorksheetNotFound:
        print("\nNo 'LOG' tab found.")

    # Is there a Reports tab already?
    titles = [ws.title for ws in sh.worksheets()]
    reports_like = [t for t in titles if "report" in t.lower()]
    print(f"\nReport-like tabs: {reports_like or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
