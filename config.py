# ============================================================
# config.py — Lead Automation System Settings
# Reads from environment variables when deployed (Render, etc.)
# Falls back to hardcoded values for local development
# ============================================================

import os

# --- APOLLO.IO ---
APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY", "YOUR_APOLLO_API_KEY_HERE")

APOLLO_TITLES = [
    "Founder", "Co-Founder", "CEO", "Brand Manager",
    "Marketing Director", "Head of Marketing", "Influencer", "Content Creator",
]
APOLLO_LOCATIONS = ["United States"]
LEADS_PER_DAY = 10
APOLLO_INDUSTRIES = [
    "Consumer Goods", "Retail", "Fashion", "Health & Wellness",
    "Beauty", "E-Commerce", "Media & Entertainment",
]

# --- GMAIL SMTP ---
GMAIL_ADDRESS      = os.environ.get("GMAIL_ADDRESS",      "contactlensoflight@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "hdiimayynzbduccl")
SENDER_NAME        = os.environ.get("SENDER_NAME",        "Lens Of Light")

# --- EMAIL SETTINGS ---
MAX_EMAILS_PER_DAY   = 20
EMAIL_DELAY_SECONDS  = 30

# --- TRACKING ---
TRACKER_FILE = "leads_tracker.csv"

# ============================================================
# GOOGLE SHEETS SETTINGS
# ============================================================
GSHEET_CREDENTIALS_FILE = os.environ.get("GSHEET_CREDENTIALS_FILE", "service_account.json")
GSHEET_NAME      = "Lens Of Light — Lead Automation"
GSHEET_ID        = os.environ.get("GSHEET_ID", "1QrzNZrBQPWcUlCTiCjmakNpF1ZPKBbbngjCRFGhJbBc")
GSHEET_AUTO_SYNC = True

# ============================================================
# YOUR BUSINESS INFO (used in email templates)
# ============================================================
YOUR_NAME      = os.environ.get("YOUR_NAME",      "Yudhajit")
YOUR_COMPANY   = os.environ.get("YOUR_COMPANY",   "Lens Of Light")
YOUR_SERVICE   = os.environ.get("YOUR_SERVICE",   "complete digital revenue systems")
YOUR_WEBSITE   = os.environ.get("YOUR_WEBSITE",   "https://lensoflight.in")
YOUR_INSTAGRAM = os.environ.get("YOUR_INSTAGRAM", "@lensoflight_media")

# ============================================================
# WEB SCRAPER SETTINGS
# ============================================================
SCRAPER_AUTO_FALLBACK  = True
SCRAPER_DELAY_SECONDS  = 3

SCRAPER_SEARCH_QUERIES = [
    "US fashion brand founder contact email",
    "beauty brand CEO contact us site:.com",
    "wellness brand founder email collab",
    "US ecommerce brand owner contact",
    "influencer marketing agency contact email site:.com",
    "DTC brand founder email hello@",
    "streetwear brand founder contact",
    "skincare brand CEO email",
    "lifestyle brand founder collaboration",
    "US content creator agency contact email",
    "boutique brand owner email contact us",
    "health wellness startup founder email",
]

SCRAPER_SKIP_DOMAINS = [
    "facebook.com", "instagram.com", "twitter.com", "linkedin.com",
    "youtube.com", "tiktok.com", "pinterest.com", "amazon.com",
    "google.com", "yelp.com", "wikipedia.org",
]
