# Lead Automation System — Setup Guide

## What This Does
Fetches new leads (US founders, brands, influencers) from Apollo.io every day,
then automatically sends personalized emails via your Gmail account.
All free. No monthly fees.

---

## Step 1 — Install Python

Download from https://python.org/downloads
Choose Python 3.10 or newer.
During install: **check "Add Python to PATH"**

Verify install:
```
python --version
```

---

## Step 2 — Install Dependencies

Open Terminal / Command Prompt in the `lead_automation` folder, then run:

```bash
pip install requests
```

That's the only external library needed.

---

## Step 3 — Get Apollo.io Free API Key

1. Go to https://app.apollo.io
2. Sign up free (no credit card)
3. Go to **Settings → Integrations → API**
4. Copy your API key
5. Paste it in `config.py` → `APOLLO_API_KEY`

Free tier gives ~50 contact exports/month.

---

## Step 4 — Set Up Gmail App Password

Gmail requires an **App Password** (not your regular password) for SMTP.

1. Go to https://myaccount.google.com/security
2. Enable **2-Step Verification** (required)
3. Go back to Security → search **"App passwords"**
4. Select app: **Mail**, device: **Windows Computer**
5. Click **Generate** — copy the 16-character password
6. Paste into `config.py` → `GMAIL_APP_PASSWORD`

---

## Step 5 — Fill In config.py

Open `config.py` and fill in:

```python
APOLLO_API_KEY = "your_key_here"
GMAIL_ADDRESS = "your@gmail.com"
GMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"
SENDER_NAME = "Your Name"
YOUR_NAME = "Your Name"
YOUR_COMPANY = "Your Company"
YOUR_SERVICE = "what you offer"
YOUR_WEBSITE = "https://yoursite.com"
YOUR_INSTAGRAM = "@yourhandle"
```

Also customize:
- `APOLLO_TITLES` — who to target (Founder, CEO, etc.)
- `APOLLO_INDUSTRIES` — what industries
- `LEADS_PER_DAY` — how many leads per day (keep ≤ 10 on free tier)
- `MAX_EMAILS_PER_DAY` — max emails to send

---

## Step 6 — Test It

Test Gmail connection:
```bash
python email_sender.py
```

Preview an email template:
```bash
python email_templates.py
```

Test Apollo connection:
```bash
python lead_fetcher.py
```

Run the full system once:
```bash
python main.py
```

---

## Step 7 — Schedule Daily (Windows)

1. Press **Win + R**, type `taskschd.msc`, press Enter
2. Click **Create Basic Task**
3. Name: `Lead Automation`
4. Trigger: **Daily** → set your preferred time (e.g. 9:00 AM)
5. Action: **Start a program**
6. Program: `python`
7. Arguments: `main.py`
8. Start in: `C:\path\to\lead_automation` (full path to your folder)
9. Click **Finish**

Now runs automatically every day at your chosen time.

---

## Step 7 — Schedule Daily (Mac)

Open Terminal and run:
```bash
crontab -e
```

Add this line (runs at 9am daily):
```
0 9 * * * cd /path/to/lead_automation && python3 main.py >> automation.log 2>&1
```

Replace `/path/to/lead_automation` with the actual folder path.

---

## Tracking Results

All results saved to `leads_tracker.csv` in the same folder.
Open with Excel or Google Sheets to see:
- Who was emailed
- What subject line was used
- Status (sent / failed)
- Date, company, title, LinkedIn

---

## Customizing Email Templates

Edit `email_templates.py` to change what the emails say.
Three templates rotate randomly — add more as you like.
Use `{first_name}`, `{company}` etc. to personalize.

---

## Free Tier Limits

| Tool | Free Limit |
|------|-----------|
| Apollo.io | ~50 lead exports/month |
| Gmail SMTP | 500 emails/day |
| Python | Unlimited |

**Tip:** Set `LEADS_PER_DAY = 2` to stretch Apollo free credits across the month.

---

## Troubleshooting

**"Invalid API key"** → Re-copy Apollo key from Settings → API

**"Gmail login failed"** → Make sure you used App Password, not regular password

**"No leads returned"** → Apollo free credits may be used up; wait until next month

**"Connection error"** → Check internet connection
