# 🔍 Lens Of Light — Lead Automation System

A complete free lead automation dashboard for **Lens Of Light**. Fetch targeted leads, send personalized outreach emails, and track everything in Google Sheets — all from a clean web dashboard.

---

## ✨ Features

- **Lead Fetching** — Apollo.io API + web scraper fallback (unlimited free leads)
- **Niche Targeting** — Type any niche (e.g. "beauty brands in Texas") to get targeted leads
- **Industry Detection** — Automatically detects lead industry from company name/domain
- **4-Step Campaign Flow** — Fetch → Select → Choose Template → Send
- **9 Email Templates** — Tailored for Real Estate, Beauty, Influencers, Coaches, Founders, and more
- **Google Sheets Sync** — All leads sync to your sheet in real-time after fetching
- **Re-campaign from Leads Tab** — Select any leads and add them to a new campaign
- **Lead Drawer** — Click any lead to view details, update status, and add notes
- **Email History** — Full log of every campaign with sent/failed/replied tracking

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
cd "E:\Lens Of Light\lead_automation"
pip install -r requirements.txt
```

### 2. Configure credentials

Open `config.py` and fill in:

```python
GMAIL_ADDRESS      = "contactlensoflight@gmail.com"
GMAIL_APP_PASSWORD = "your-app-password"   # See below for how to get this
YOUR_NAME          = "Yudhajit"
YOUR_COMPANY       = "Lens Of Light"
YOUR_WEBSITE       = "https://lensoflight.in"
YOUR_INSTAGRAM     = "@lensoflight_media"
```

### 3. Start the server

```bash
python server.py
```

### 4. Open the dashboard

```
http://localhost:5000
```

---

## 📧 Getting a Gmail App Password

1. Go to [myaccount.google.com](https://myaccount.google.com) → **Security**
2. Make sure **2-Step Verification** is ON
3. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
4. Type `Lead Automation` → **Create**
5. Copy the 16-character password into `config.py`

---

## 📊 Google Sheets Setup

1. Create a new Google Sheet at [sheets.google.com](https://sheets.google.com)
2. Share it with your service account email as **Editor**:
   ```
   lead-automation@lead-automation-496209.iam.gserviceaccount.com
   ```
3. Copy the Sheet ID from the URL and paste it into `config.py`:
   ```python
   GSHEET_ID = "your-sheet-id-here"
   ```
4. Place `service_account.json` in the `lead_automation` folder

---

## 🗂 Project Structure

```
lead_automation/
├── server.py              # Flask backend — all API endpoints
├── dashboard.html         # Web dashboard frontend
├── config.py              # All settings and credentials
├── lead_fetcher.py        # Apollo.io API + scraper orchestration
├── web_scraper.py         # DuckDuckGo scraper + email extractor
├── email_sender.py        # Gmail SMTP sender
├── email_templates.py     # Default template definitions
├── gsheet.py              # Google Sheets integration
├── tracker.py             # CSV lead tracker
├── main.py                # Standalone daily runner (optional)
├── custom_templates.json  # Your 9 custom email templates
├── service_account.json   # Google service account key (gitignored)
├── requirements.txt       # Python dependencies
└── README.md
```

---

## 🎯 Campaign Workflow

```
Step 1 — Fetch Leads
  └── Enter count + optional niche → hits Apollo or web scraper
  └── Leads instantly sync to Google Sheets

Step 2 — Select Leads
  └── Review leads with name, email, company, industry
  └── Check/uncheck who to email

Step 3 — Choose Template
  └── Pick from 9 targeted templates
  └── Each template matches a customer type

Step 4 — Send
  └── Emails sent one by one with 30s gap (avoids spam filters)
  └── Live log shows sent / failed in real time
  └── Google Sheet auto-updates with status
```

---

## 📬 Email Templates

| # | Template | Best For |
|---|----------|----------|
| 0 | Real Estate Professional | Realtors, brokers |
| 1 | Tax Professional | CPAs, tax strategists |
| 2 | Small Business Owner | Local & small businesses |
| 3 | Entrepreneur / Founder | Startup founders |
| 4 | Influencer / Content Creator | Creators, social media |
| 5 | Digital Coach | Online coaches, educators |
| 6 | Service Business (Full Pitch) | Any service business |
| 7 | Beauty Brand | Cosmetics, skincare, salons |
| 8 | Webinar Invite | Invite any lead to LOL webinar |

All templates include social proof:
> *"We've helped scale @iambillionairebarbie (1M), @dremedici (719K), and @devinjatho (415K)"*

---

## 🌐 Free Deployment (Render)

1. Push code to a GitHub repo (`.gitignore` already excludes secrets)
2. Go to [render.com](https://render.com) → New Web Service → connect repo
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python server.py`
5. Add environment variables in Render dashboard:
   - `GMAIL_ADDRESS`
   - `GMAIL_APP_PASSWORD`
   - `GSHEET_ID`
6. Add `service_account.json` via **Environment → Secret Files**
7. Deploy — get a public URL like `https://your-app.onrender.com`

> **Note:** Render free tier sleeps after 15 min of inactivity. First request after sleeping takes ~30 seconds.

---

## ⚙️ Config Reference

| Setting | Description |
|---------|-------------|
| `APOLLO_API_KEY` | Apollo.io API key (free tier: ~50 leads/month) |
| `GMAIL_ADDRESS` | Gmail address to send from |
| `GMAIL_APP_PASSWORD` | Gmail App Password (not your login password) |
| `GSHEET_ID` | Google Sheet ID from the sheet URL |
| `LEADS_PER_DAY` | Default lead fetch count |
| `EMAIL_DELAY_SECONDS` | Delay between sends (default: 30s) |
| `SCRAPER_AUTO_FALLBACK` | Use scraper when Apollo quota runs out |
| `SCRAPER_SEARCH_QUERIES` | Default DuckDuckGo queries for leads |

---

## 📦 Dependencies

```
flask
requests
beautifulsoup4
lxml
gspread
google-auth
```

Install with:
```bash
pip install -r requirements.txt
```

---

## 🔒 Security Notes

- Never commit `config.py` or `service_account.json` to GitHub — both are in `.gitignore`
- Use environment variables for all credentials when deploying
- Gmail App Password grants full email access — keep it private

---

Built by **Lens Of Light** · [lensoflight.in](https://lensoflight.in) · [@lensoflight_media](https://instagram.com/lensoflight_media)
