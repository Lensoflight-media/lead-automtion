# ============================================================
# tracker.py — CSV Lead Tracker
# ============================================================
# Logs every lead: email status, date, subject line
# Prevents duplicate emails to same person
# ============================================================

import csv
import os
from datetime import datetime
from config import TRACKER_FILE


TRACKER_FIELDS = [
    "date_added",
    "email",
    "first_name",
    "last_name",
    "title",
    "company",
    "industry",
    "linkedin_url",
    "city",
    "state",
    "website",
    "email_status",   # sent | failed | skipped
    "email_subject",
    "error_note",
]


def load_tracker() -> tuple[list[dict], set]:
    """
    Load existing tracker CSV.
    Returns (all_rows, set_of_already_contacted_emails).
    """
    rows = []
    emails = set()

    if not os.path.exists(TRACKER_FILE):
        print(f"[Tracker] No existing tracker found. Starting fresh.")
        return rows, emails

    try:
        with open(TRACKER_FILE, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
                if row.get("email"):
                    emails.add(row["email"].strip().lower())

        print(f"[Tracker] Loaded {len(rows)} existing leads ({len(emails)} unique emails).")
    except Exception as e:
        print(f"[Tracker] Warning: Could not load tracker: {e}")

    return rows, emails


def log_results(results: list[dict]):
    """
    Append email send results to tracker CSV.
    Creates file with headers if it doesn't exist.
    """
    if not results:
        return

    file_exists = os.path.exists(TRACKER_FILE)

    try:
        with open(TRACKER_FILE, "a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=TRACKER_FIELDS, extrasaction="ignore")

            # Write header if new file
            if not file_exists:
                writer.writeheader()

            for result in results:
                lead = result.get("lead", {})
                row = {
                    "date_added": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "email": lead.get("email", ""),
                    "first_name": lead.get("first_name", ""),
                    "last_name": lead.get("last_name", ""),
                    "title": lead.get("title", ""),
                    "company": lead.get("company", ""),
                    "industry": lead.get("industry", ""),
                    "linkedin_url": lead.get("linkedin_url", ""),
                    "city": lead.get("city", ""),
                    "state": lead.get("state", ""),
                    "website": lead.get("website", ""),
                    "email_status": result.get("status", "unknown"),
                    "email_subject": result.get("subject", ""),
                    "error_note": result.get("error", "") or "",
                }
                writer.writerow(row)

        print(f"[Tracker] Logged {len(results)} results to {TRACKER_FILE}")

    except Exception as e:
        print(f"[Tracker] ERROR: Could not write to tracker: {e}")

    # ── Auto-sync to Google Sheets ──
    try:
        from config import GSHEET_AUTO_SYNC
        if GSHEET_AUTO_SYNC:
            from gsheet import sync_results, is_configured
            if is_configured():
                sync_results(results)
            else:
                print("[Tracker] GSheet not configured yet — skipping sync. See GSHEET_SETUP.md")
    except Exception as e:
        print(f"[Tracker] GSheet sync skipped: {e}")


def get_summary() -> dict:
    """Return quick stats from tracker."""
    rows, _ = load_tracker()

    total = len(rows)
    sent = sum(1 for r in rows if r.get("email_status") == "sent")
    failed = sum(1 for r in rows if r.get("email_status") == "failed")

    return {
        "total_leads": total,
        "emails_sent": sent,
        "emails_failed": failed,
        "pending": total - sent - failed,
    }


# ---- TEST ----
if __name__ == "__main__":
    summary = get_summary()
    print(f"Tracker Summary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
