# Google Sheets Setup — 5 Minutes

## Step 1 — Create Google Cloud Project

1. Go to https://console.cloud.google.com
2. Click **Select a project** → **New Project**
3. Name it `Lead Automation` → **Create**

## Step 2 — Enable APIs

1. Go to **APIs & Services → Library**
2. Search `Google Sheets API` → **Enable**
3. Search `Google Drive API` → **Enable**

## Step 3 — Create Service Account

1. Go to **IAM & Admin → Service Accounts**
2. Click **Create Service Account**
3. Name: `lead-automation` → **Create and Continue** → **Done**
4. Click the service account you just created
5. Go to **Keys** tab → **Add Key → Create new key → JSON**
6. A JSON file downloads automatically

## Step 4 — Add Key to Your Folder

1. Rename the downloaded file to exactly: `service_account.json`
2. Move it into your `E:\Lens Of Light\lead_automation\` folder

## Step 5 — Restart and Connect

```powershell
# Stop server.py (Ctrl+C), then restart:
python server.py
```

Open `http://localhost:5000` → click **Leads** tab → sheet is created automatically!

---

## What Happens Automatically

- A Google Sheet named **"Lens Of Light — Lead Automation"** is created
- Every lead you email is synced to the sheet instantly
- The sheet includes: name, email, company, title, status, subject sent, notes
- You can update status and notes directly in the dashboard or the sheet
- Sheet auto-refreshes in dashboard every 30 seconds

---

## Your Sheet Columns

| Column | Description |
|--------|-------------|
| Date | When emailed |
| First Name | Lead's first name |
| Last Name | Lead's last name |
| Email | Email address |
| Company | Company name |
| Title | Job title |
| Industry | Industry |
| City / State | Location |
| Website | Company website |
| LinkedIn | LinkedIn URL |
| Source | apollo or web_scraper |
| Email Status | sent / failed / replied / interested |
| Email Subject | Subject line sent |
| Error | Error message if failed |
| Notes | Your personal notes |

---

## Troubleshooting

**"service_account.json not found"** → Make sure the file is in the `lead_automation` folder (same folder as `server.py`)

**"403 Forbidden"** → Make sure both Google Sheets API and Google Drive API are enabled

**"SpreadsheetNotFound"** → Sheet will be created automatically on first run

**Sheet not updating** → Check that `GSHEET_AUTO_SYNC = True` in `config.py`
