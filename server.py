# ============================================================
# server.py — Flask API backend for Lead Automation Dashboard
# ============================================================
# Run:  python server.py
# Open: http://localhost:5000
# ============================================================

import csv
import json
import os
import sys
import threading
from datetime import datetime
from collections import defaultdict
from flask import Flask, jsonify, request, send_from_directory
from config import TRACKER_FILE

app = Flask(__name__, static_folder=".")

# In-memory store for fetched (not yet sent) leads
fetched_leads_store = []
send_running = False
send_log = []


# ============================================================
# SERVE DASHBOARD
# ============================================================

@app.route("/")
def index():
    return send_from_directory(".", "dashboard.html")


# ============================================================
# API: STEP 1 — FETCH LEADS (no email sent yet)
# ============================================================

@app.route("/api/fetch", methods=["POST"])
def fetch_leads_api():
    """
    Fetch N leads from Apollo/scraper.
    Does NOT send any emails. Returns leads for user review.
    Body: { "count": 10 }
    """
    global fetched_leads_store

    data = request.get_json() or {}
    count = int(data.get("count", 10))
    count = max(1, min(count, 50))  # clamp 1–50
    niche = (data.get("niche") or "").strip()

    try:
        from tracker import load_tracker
        from lead_fetcher import fetch_leads

        _, already_contacted = load_tracker()

        leads = fetch_leads(already_contacted_emails=already_contacted, count=count, niche=niche)

        fetched_leads_store = leads

        # Sync to Google Sheet immediately after fetching
        try:
            from gsheet import sync_fetched_leads, is_configured
            if is_configured():
                sync_fetched_leads(leads)
        except Exception as ge:
            print(f"[GSheet] Fetch sync error: {ge}")

        return jsonify({"status": "ok", "leads": leads, "count": len(leads)})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================
# API: STEP 4 — SEND TO SELECTED LEADS WITH CHOSEN TEMPLATE
# ============================================================

@app.route("/api/send", methods=["POST"])
def send_selected():
    """
    Send emails to selected leads using chosen template.
    Body: { "leads": [...], "template_id": 0 }
    """
    global send_running, send_log

    if send_running:
        return jsonify({"status": "already_running"})

    data = request.get_json() or {}
    selected_leads = data.get("leads", [])
    template_id = int(data.get("template_id", 0))

    if not selected_leads:
        return jsonify({"status": "error", "message": "No leads selected."}), 400

    send_running = True
    send_log = []

    def _run():
        global send_running, send_log
        try:
            from email_sender import _connect_smtp, _send_single
            from tracker import log_results
            import time

            # Load the chosen template
            templates = _load_templates()
            tpl = templates[template_id] if template_id < len(templates) else templates[0]

            send_log.append(f"[{_now()}] Connecting to Gmail...")
            server = _connect_smtp()
            send_log.append(f"[{_now()}] Connected. Sending to {len(selected_leads)} leads...")

            results = []
            for i, lead in enumerate(selected_leads):
                email = lead.get("email", "")
                if not email:
                    continue

                first_name = lead.get("first_name") or "there"   # fallback for email greeting only
                company = lead.get("company", "your brand")
                title = lead.get("title", "")

                try:
                    from config import YOUR_NAME, YOUR_COMPANY, YOUR_SERVICE, YOUR_WEBSITE, YOUR_INSTAGRAM
                    # For subject: use empty string so "there" doesn't bleed in
                    fmt_subject = dict(
                        first_name=lead.get("first_name") or "",
                        company=company, title=title,
                        YOUR_NAME=YOUR_NAME, YOUR_COMPANY=YOUR_COMPANY,
                        YOUR_SERVICE=YOUR_SERVICE, YOUR_WEBSITE=YOUR_WEBSITE,
                        YOUR_INSTAGRAM=YOUR_INSTAGRAM,
                    )
                    # For body: "there" is fine as greeting fallback
                    fmt_body = dict(
                        first_name=first_name, company=company, title=title,
                        YOUR_NAME=YOUR_NAME, YOUR_COMPANY=YOUR_COMPANY,
                        YOUR_SERVICE=YOUR_SERVICE, YOUR_WEBSITE=YOUR_WEBSITE,
                        YOUR_INSTAGRAM=YOUR_INSTAGRAM,
                    )
                    subject = tpl["subject"].format(**fmt_subject)
                    # Clean up artifacts like " — " or ", " at start if first_name was empty
                    import re as _re
                    subject = _re.sub(r"^[\s,\-—–]+", "", subject).strip()
                    body = tpl["body"].format(**fmt_body)

                    _send_single(server, email, subject, body)
                    results.append({"lead": lead, "subject": subject, "status": "sent", "error": None})
                    send_log.append(f"[{_now()}] ✓ Sent → {first_name} <{email}>")

                except Exception as e:
                    results.append({"lead": lead, "subject": "", "status": "failed", "error": str(e)})
                    send_log.append(f"[{_now()}] ✗ Failed → {email}: {e}")

                if i < len(selected_leads) - 1:
                    time.sleep(30)

            try:
                server.quit()
            except Exception:
                pass

            log_results(results)
            sent = sum(1 for r in results if r["status"] == "sent")
            send_log.append(f"[{_now()}] Done. {sent}/{len(selected_leads)} sent. Logged to tracker.")

        except Exception as e:
            send_log.append(f"[{_now()}] ERROR: {e}")
        finally:
            send_running = False

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return jsonify({"status": "started"})


@app.route("/api/send/status", methods=["GET"])
def send_status():
    return jsonify({"running": send_running, "log": send_log[-60:]})


# ============================================================
# API: GOOGLE SHEETS
# ============================================================

@app.route("/api/gsheet/leads", methods=["GET"])
def gsheet_leads():
    """Fetch all leads from Google Sheet in real-time."""
    try:
        from gsheet import fetch_all_leads, is_configured, get_sheet_url
        if not is_configured():
            return jsonify({
                "status": "not_configured",
                "message": "Google Sheets not set up yet. See GSHEET_SETUP.md",
                "leads": [],
                "url": "",
            })
        leads = fetch_all_leads()
        url = get_sheet_url()
        return jsonify({"status": "ok", "leads": leads, "total": len(leads), "url": url})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e), "leads": [], "url": ""}), 500


@app.route("/api/gsheet/status", methods=["GET"])
def gsheet_status():
    """Check if GSheet is configured and return sheet URL."""
    try:
        from gsheet import is_configured, get_sheet_url
        configured = is_configured()
        return jsonify({
            "configured": configured,
            "url": get_sheet_url() if configured else "",
        })
    except Exception as e:
        return jsonify({"configured": False, "url": "", "error": str(e)})


@app.route("/api/gsheet/update", methods=["POST"])
def gsheet_update():
    """Update a lead's status and notes in Google Sheet."""
    data = request.get_json() or {}
    email = data.get("email", "")
    status = data.get("status", "")
    notes = data.get("notes", "")
    try:
        from gsheet import update_lead_status
        success = update_lead_status(email, status, notes)
        return jsonify({"status": "ok" if success else "not_found"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================
# API: STATS + HISTORY
# ============================================================

@app.route("/api/leads", methods=["GET"])
def get_leads():
    leads = _read_csv()
    return jsonify({"leads": leads, "total": len(leads)})


@app.route("/api/stats", methods=["GET"])
def get_stats():
    leads = _read_csv()
    total = len(leads)
    sent = sum(1 for r in leads if r.get("email_status") == "sent")
    failed = sum(1 for r in leads if r.get("email_status") == "failed")
    rate = round((sent / total * 100) if total > 0 else 0, 1)

    daily = defaultdict(lambda: {"sent": 0, "failed": 0})
    for row in leads:
        date_str = row.get("date_added", "")
        if date_str:
            day = date_str[:10]
            status = row.get("email_status", "")
            if status == "sent":
                daily[day]["sent"] += 1
            elif status == "failed":
                daily[day]["failed"] += 1

    sorted_days = sorted(daily.keys())[-14:]
    chart_data = {
        "labels": sorted_days,
        "sent": [daily[d]["sent"] for d in sorted_days],
        "failed": [daily[d]["failed"] for d in sorted_days],
    }

    return jsonify({"total": total, "sent": sent, "failed": failed,
                    "success_rate": rate, "chart": chart_data})


# ============================================================
# API: TEMPLATES
# ============================================================

TEMPLATES_FILE = "custom_templates.json"

@app.route("/api/templates", methods=["GET"])
def get_templates():
    if os.path.exists(TEMPLATES_FILE):
        with open(TEMPLATES_FILE, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    return jsonify({"templates": _default_templates()})


@app.route("/api/templates", methods=["POST"])
def save_templates():
    data = request.get_json()
    with open(TEMPLATES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return jsonify({"status": "saved"})


# ============================================================
# HELPERS
# ============================================================

def _load_templates() -> list:
    if os.path.exists(TEMPLATES_FILE):
        with open(TEMPLATES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("templates", _default_templates())
    return _default_templates()


def _default_templates() -> list:
    return [
        {
            "id": 0,
            "name": "Collab Intro",
            "subject": "Collaboration idea for {company} 👋",
            "body": "Hi {first_name},\n\nI came across {company} and love what you're building.\n\nI'm {YOUR_NAME} from {YOUR_COMPANY}. We specialize in {YOUR_SERVICE}, and I think there's a natural fit.\n\nWould you be open to a quick 15-minute call?\n\n{YOUR_NAME}\n{YOUR_WEBSITE}\n{YOUR_INSTAGRAM}",
        },
        {
            "id": 1,
            "name": "Partnership Pitch",
            "subject": "Quick idea — {company} x {YOUR_COMPANY}",
            "body": "Hey {first_name},\n\nAs {title} at {company}, I imagine you're always looking to grow brand visibility.\n\nThat's exactly what we help with at {YOUR_COMPANY}. I'd love to share a few ideas specific to {company}.\n\nWorth a quick chat?\n\nBest,\n{YOUR_NAME}\n{YOUR_WEBSITE}",
        },
        {
            "id": 2,
            "name": "Short Pitch",
            "subject": "{first_name}, quick idea for {company}",
            "body": "Hi {first_name},\n\nHuge fan of {company} — reached out because I think we could do something interesting together.\n\nPortfolio: {YOUR_WEBSITE}\nInstagram: {YOUR_INSTAGRAM}\n\nOpen to a quick call?\n\n{YOUR_NAME}",
        },
    ]


def _read_csv() -> list[dict]:
    if not os.path.exists(TRACKER_FILE):
        return []
    rows = []
    try:
        with open(TRACKER_FILE, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(dict(row))
    except Exception:
        pass
    return rows


def _now() -> str:
    return datetime.now().strftime("%H:%M:%S")


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  Lead Automation Dashboard")
    print("  Open: http://localhost:5000")
    print("=" * 50)
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, port=port, host="0.0.0.0")
