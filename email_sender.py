# ============================================================
# email_sender.py — Gmail SMTP Email Sender
# ============================================================

import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import (
    GMAIL_ADDRESS,
    GMAIL_APP_PASSWORD,
    SENDER_NAME,
    EMAIL_DELAY_SECONDS,
    MAX_EMAILS_PER_DAY,
)
from email_templates import get_email


GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587


def send_emails(leads: list[dict], tracker) -> list[dict]:
    """
    Send personalized emails to list of leads.
    Returns list of results: {lead, subject, status, error}
    Respects daily limit and delay between sends.
    """
    results = []
    sent_count = 0

    if not leads:
        print("[Sender] No leads to email.")
        return results

    print(f"[Sender] Connecting to Gmail SMTP...")

    try:
        server = _connect_smtp()
    except Exception as e:
        print(f"[Sender] FAILED to connect to Gmail: {e}")
        print("[Sender] Check GMAIL_ADDRESS and GMAIL_APP_PASSWORD in config.py")
        return results

    print(f"[Sender] Connected. Sending to {len(leads)} leads...")

    for lead in leads:
        if sent_count >= MAX_EMAILS_PER_DAY:
            print(f"[Sender] Hit daily limit ({MAX_EMAILS_PER_DAY}). Stopping.")
            break

        email_address = lead.get("email")
        if not email_address:
            continue

        try:
            subject, body = get_email(lead)
            _send_single(server, email_address, subject, body)

            result = {
                "lead": lead,
                "subject": subject,
                "status": "sent",
                "error": None,
            }
            results.append(result)
            sent_count += 1

            print(f"[Sender] ✓ Sent to {lead.get('first_name')} {lead.get('last_name')} <{email_address}>")

            # Delay between emails — avoids spam flags
            if sent_count < len(leads):
                print(f"[Sender] Waiting {EMAIL_DELAY_SECONDS}s before next email...")
                time.sleep(EMAIL_DELAY_SECONDS)

        except smtplib.SMTPRecipientsRefused:
            print(f"[Sender] ✗ Rejected: {email_address}")
            results.append({"lead": lead, "subject": "", "status": "failed", "error": "recipient_refused"})

        except smtplib.SMTPServerDisconnected:
            print("[Sender] Disconnected. Reconnecting...")
            try:
                server = _connect_smtp()
            except Exception as e:
                print(f"[Sender] Reconnect failed: {e}")
                break

        except Exception as e:
            print(f"[Sender] ✗ Error sending to {email_address}: {e}")
            results.append({"lead": lead, "subject": "", "status": "failed", "error": str(e)})

    try:
        server.quit()
    except Exception:
        pass

    print(f"\n[Sender] Done. Sent {sent_count} emails.")
    return results


def _connect_smtp():
    """Connect and authenticate with Gmail SMTP."""
    server = smtplib.SMTP(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT, timeout=20)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
    return server


def _send_single(server, to_email: str, subject: str, body: str):
    """Build and send a single email."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{SENDER_NAME} <{GMAIL_ADDRESS}>"
    msg["To"] = to_email

    # Plain text version
    part = MIMEText(body, "plain")
    msg.attach(part)

    server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())


# ---- TEST ----
if __name__ == "__main__":
    print("Testing Gmail connection...")
    try:
        server = _connect_smtp()
        server.quit()
        print("✓ Gmail connection successful!")
    except Exception as e:
        print(f"✗ Gmail connection failed: {e}")
        print("Make sure GMAIL_APP_PASSWORD is set correctly in config.py")
