# ============================================================
# main.py — Lead Automation System | Daily Runner
# ============================================================
# Run manually:        python main.py
# Schedule daily:      See SETUP.md for Task Scheduler setup
# ============================================================

import sys
from datetime import datetime
from lead_fetcher import fetch_leads
from email_sender import send_emails
from tracker import load_tracker, log_results, get_summary


def run():
    print("=" * 60)
    print(f"  LEAD AUTOMATION — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # ── STEP 1: Load tracker (get already-contacted emails) ──
    print("\n[1/4] Loading tracker...")
    _, already_contacted = load_tracker()
    print(f"      {len(already_contacted)} emails already in system.")

    # ── STEP 2: Fetch new leads ──
    print("\n[2/4] Fetching new leads from Apollo.io...")
    leads = fetch_leads(already_contacted_emails=already_contacted)

    if not leads:
        print("\n[!] No new leads found today.")
        print("    Possible reasons:")
        print("    - Apollo free tier exhausted for the month")
        print("    - API key issue (check config.py)")
        print("    - All matching leads already contacted")
        print("\nExiting. Try again tomorrow.")
        sys.exit(0)

    print(f"      {len(leads)} new leads ready.")

    # ── STEP 3: Send emails ──
    print(f"\n[3/4] Sending personalized emails...")
    results = send_emails(leads, tracker=None)

    # ── STEP 4: Log results ──
    print("\n[4/4] Logging results to tracker...")
    log_results(results)

    # ── SUMMARY ──
    summary = get_summary()
    sent_today = sum(1 for r in results if r.get("status") == "sent")
    failed_today = sum(1 for r in results if r.get("status") == "failed")

    print("\n" + "=" * 60)
    print("  TODAY'S RUN COMPLETE")
    print("=" * 60)
    print(f"  Leads fetched:    {len(leads)}")
    print(f"  Emails sent:      {sent_today}")
    print(f"  Emails failed:    {failed_today}")
    print(f"  ─────────────────────────────")
    print(f"  All-time sent:    {summary['emails_sent']}")
    print(f"  All-time total:   {summary['total_leads']}")
    print(f"  Tracker file:     leads_tracker.csv")
    print("=" * 60)

    if sent_today > 0:
        print(f"\n✓ Done! {sent_today} emails sent. Check leads_tracker.csv for details.")
    else:
        print("\n[!] No emails were sent. Check errors above.")


if __name__ == "__main__":
    run()
