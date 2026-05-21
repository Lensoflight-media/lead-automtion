# ============================================================
# gsheet.py — Google Sheets Integration
# ============================================================
# Syncs all leads + email statuses to a Google Sheet.
# Real-time read back for the dashboard Leads page.
# ============================================================

import json
import os
from datetime import datetime

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

from config import GSHEET_CREDENTIALS_FILE, GSHEET_NAME, GSHEET_ID

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_HEADERS = [
    "Date", "First Name", "Last Name", "Email", "Company",
    "Title", "Industry", "City", "State", "Website", "LinkedIn",
    "Source", "Email Status", "Email Subject", "Error", "Notes",
]

_sheet_cache = None  # cached worksheet object


# ============================================================
# CONNECTION
# ============================================================

def is_configured() -> bool:
    """Return True if GSheet credentials file exists and config is set."""
    if not GSPREAD_AVAILABLE:
        return False
    creds_path = GSHEET_CREDENTIALS_FILE if GSHEET_CREDENTIALS_FILE else "service_account.json"
    return os.path.exists(creds_path)


def reset_cache():
    """Force re-connect on next get_sheet() call (e.g. after config change)."""
    global _sheet_cache
    _sheet_cache = None


def get_sheet():
    """Connect to Google Sheets and return the first worksheet. Creates sheet if needed."""
    global _sheet_cache
    if _sheet_cache is not None:
        return _sheet_cache

    if not is_configured():
        raise RuntimeError(
            "Google Sheets not configured. "
            "Place service_account.json in the lead_automation folder. "
            "See GSHEET_SETUP.md for instructions."
        )

    creds_file = GSHEET_CREDENTIALS_FILE if os.path.exists(GSHEET_CREDENTIALS_FILE) else "service_account.json"
    creds = Credentials.from_service_account_file(creds_file, scopes=SCOPES)
    client = gspread.authorize(creds)

    try:
        # Prefer opening by ID if set — avoids Drive quota issues with service accounts
        if GSHEET_ID:
            print(f"[GSheet] Opening sheet by ID: {GSHEET_ID}")
            spreadsheet = client.open_by_key(GSHEET_ID)
        else:
            spreadsheet = client.open(GSHEET_NAME)
    except gspread.SpreadsheetNotFound:
        raise RuntimeError(
            f"Sheet not found. Please:\n"
            f"1. Create a Google Sheet manually at https://sheets.google.com\n"
            f"2. Share it with: lead-automation@lead-automation-496209.iam.gserviceaccount.com (Editor)\n"
            f"3. Copy the Sheet ID from the URL and set GSHEET_ID in config.py"
        )

    worksheet = spreadsheet.sheet1
    worksheet.update_title("Leads")

    # Add headers if sheet is empty
    if worksheet.row_count == 0 or not worksheet.row_values(1):
        worksheet.append_row(SHEET_HEADERS, value_input_option="RAW")
        # Bold the header row
        try:
            worksheet.format("A1:P1", {
                "textFormat": {"bold": True},
                "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.35},
            })
        except Exception:
            pass

    _sheet_cache = worksheet
    print(f"[GSheet] Connected to '{GSHEET_NAME}'")
    return worksheet


# ============================================================
# WRITE
# ============================================================

def sync_fetched_leads(leads: list[dict]):
    """
    Write freshly fetched leads to the Google Sheet immediately after fetching.
    Skips any lead whose email already exists in the sheet (no duplicates).
    Status is set to 'fetched' until an email is actually sent.
    """
    if not leads:
        return

    if not is_configured():
        print("[GSheet] Skipping sync — not configured.")
        return

    try:
        ws = get_sheet()

        # Get existing emails from column D to avoid duplicates
        existing_emails = set(e.lower() for e in ws.col_values(4)[1:] if e)

        rows = []
        for lead in leads:
            email = lead.get("email", "")
            if not email or email.lower() in existing_emails:
                continue
            existing_emails.add(email.lower())
            rows.append([
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                lead.get("first_name", ""),
                lead.get("last_name", ""),
                email,
                lead.get("company", ""),
                lead.get("title", ""),
                lead.get("industry", ""),
                lead.get("city", ""),
                lead.get("state", ""),
                lead.get("website", ""),
                lead.get("linkedin_url", ""),
                lead.get("source", ""),
                "fetched",   # Email Status
                "",          # Email Subject
                "",          # Error
                "",          # Notes
            ])

        if rows:
            ws.append_rows(rows, value_input_option="RAW")
            print(f"[GSheet] Added {len(rows)} fetched leads to sheet.")
        else:
            print("[GSheet] No new leads to add (all already in sheet).")

    except Exception as e:
        print(f"[GSheet] Sync error: {e}")


def sync_results(results: list[dict]):
    """
    Append send results to Google Sheet.
    Called after each email campaign send.
    """
    if not results:
        return

    if not is_configured():
        print("[GSheet] Skipping GSheet sync — not configured. See GSHEET_SETUP.md")
        return

    try:
        ws = get_sheet()

        # Get existing emails so we can UPDATE rows instead of appending duplicates
        existing_emails = ws.col_values(4)[1:]  # Column D, skip header
        email_to_row = {e.lower(): i + 2 for i, e in enumerate(existing_emails) if e}

        new_rows = []
        for result in results:
            lead = result.get("lead", {})
            email = lead.get("email", "")
            status = result.get("status", "")
            subject = result.get("subject", "")
            error = result.get("error", "") or ""

            if email.lower() in email_to_row:
                # Update existing row's status, subject, and error columns
                row_num = email_to_row[email.lower()]
                ws.update_cell(row_num, 13, status)   # Column M = Email Status
                ws.update_cell(row_num, 14, subject)  # Column N = Email Subject
                ws.update_cell(row_num, 15, error)    # Column O = Error
            else:
                # Lead wasn't fetched before — append as new row
                new_rows.append([
                    datetime.now().strftime("%Y-%m-%d %H:%M"),
                    lead.get("first_name", ""),
                    lead.get("last_name", ""),
                    email,
                    lead.get("company", ""),
                    lead.get("title", ""),
                    lead.get("industry", ""),
                    lead.get("city", ""),
                    lead.get("state", ""),
                    lead.get("website", ""),
                    lead.get("linkedin_url", ""),
                    lead.get("source", ""),
                    status,
                    subject,
                    error,
                    "",  # Notes
                ])

        if new_rows:
            ws.append_rows(new_rows, value_input_option="RAW")

        print(f"[GSheet] Updated {len(results)} lead statuses in Google Sheet.")

        # Color-code status cells
        _color_status_column(ws)

    except Exception as e:
        print(f"[GSheet] Sync error: {e}")


def update_lead_status(email: str, new_status: str, notes: str = ""):
    """Update the status of a lead in the sheet by email address."""
    if not is_configured():
        return False

    try:
        ws = get_sheet()
        cell = ws.find(email, in_column=4)  # Email is column D (4)
        if cell:
            ws.update_cell(cell.row, 13, new_status)  # Column M = Email Status
            if notes:
                ws.update_cell(cell.row, 16, notes)   # Column P = Notes
            # Invalidate cache so next fetch gets fresh data
            return True
    except Exception as e:
        print(f"[GSheet] Update error: {e}")
    return False


# ============================================================
# READ
# ============================================================

def fetch_all_leads() -> list[dict]:
    """
    Fetch all leads from Google Sheet as list of dicts.
    Used by dashboard real-time Leads page.
    """
    if not is_configured():
        return []

    try:
        ws = get_sheet()
        records = ws.get_all_records()  # Returns list of dicts using header row as keys
        return records
    except Exception as e:
        print(f"[GSheet] Fetch error: {e}")
        return []


def get_sheet_url() -> str:
    """Return the URL of the connected Google Sheet."""
    if not is_configured():
        return ""
    try:
        ws = get_sheet()
        return f"https://docs.google.com/spreadsheets/d/{ws.spreadsheet.id}"
    except Exception:
        return ""


# ============================================================
# FORMATTING HELPERS
# ============================================================

def _color_status_column(ws):
    """Color-code the Email Status column (M) — green=sent, red=failed."""
    try:
        all_values = ws.col_values(13)  # Column M = Email Status
        for i, val in enumerate(all_values[1:], start=2):  # skip header
            if val == "sent":
                ws.format(f"M{i}", {"backgroundColor": {"red": 0.18, "green": 0.49, "blue": 0.2}})
            elif val == "failed":
                ws.format(f"M{i}", {"backgroundColor": {"red": 0.7, "green": 0.18, "blue": 0.18}})
    except Exception:
        pass  # formatting is optional


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("Testing Google Sheets connection...")
    if not GSPREAD_AVAILABLE:
        print("✗ gspread not installed. Run: pip install gspread google-auth")
    elif not is_configured():
        print("✗ service_account.json not found. See GSHEET_SETUP.md")
    else:
        try:
            ws = get_sheet()
            url = get_sheet_url()
            print(f"✓ Connected! Sheet URL: {url}")
            leads = fetch_all_leads()
            print(f"  {len(leads)} leads in sheet.")
        except Exception as e:
            print(f"✗ Error: {e}")
