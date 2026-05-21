# ============================================================
# lead_fetcher.py — Fetch leads from Apollo.io + Web Scraper fallback
# ============================================================
# Priority order:
#   1. Apollo.io API (verified emails, rich data)
#   2. Web scraper fallback (unlimited, free, less structured)
# ============================================================

import requests
import json
import time
from config import (
    APOLLO_API_KEY,
    APOLLO_TITLES,
    APOLLO_LOCATIONS,
    APOLLO_INDUSTRIES,
    LEADS_PER_DAY,
    SCRAPER_AUTO_FALLBACK,
)


APOLLO_SEARCH_URL = "https://api.apollo.io/v1/mixed_people/search"


def fetch_leads(already_contacted_emails: set, page: int = 1, count: int = None, niche: str = "") -> list[dict]:
    """
    Fetch leads using Apollo.io first.
    If Apollo fails or returns too few leads, auto-fallback to web scraper.
    count: how many leads to fetch (overrides LEADS_PER_DAY from config).
    niche: optional niche string to focus scraper queries (e.g. "beauty brands in Texas").
    """
    needed = count if count is not None else LEADS_PER_DAY
    niche = (niche or "").strip()

    if niche:
        print(f"[Fetcher] Niche target: '{niche}'")

    apollo_leads = []
    apollo_ok = False

    # ── Try Apollo first (niche not used for Apollo — it uses config titles/industries) ──
    if APOLLO_API_KEY and APOLLO_API_KEY != "YOUR_APOLLO_API_KEY_HERE":
        apollo_leads, apollo_ok = _fetch_from_apollo(already_contacted_emails, page, needed)
    else:
        print("[Fetcher] Apollo API key not set — skipping Apollo, going straight to scraper.")

    # ── Fallback: web scraper ──
    if SCRAPER_AUTO_FALLBACK and len(apollo_leads) < needed:
        still_needed = needed - len(apollo_leads)

        if not apollo_ok:
            print(f"[Fetcher] Apollo unavailable. Falling back to web scraper...")
        else:
            print(f"[Fetcher] Apollo returned {len(apollo_leads)}/{needed} leads. "
                  f"Scraping {still_needed} more...")

        try:
            from web_scraper import scrape_leads
            already_seen = set(already_contacted_emails)
            already_seen.update(lead["email"] for lead in apollo_leads)

            scraper_leads = scrape_leads(
                already_contacted_emails=already_seen,
                needed=still_needed,
                niche=niche,
            )
            apollo_leads.extend(scraper_leads)
            print(f"[Fetcher] Scraper added {len(scraper_leads)} leads.")

        except ImportError:
            print("[Fetcher] web_scraper.py not found. Install beautifulsoup4: pip install beautifulsoup4 lxml")
        except Exception as e:
            print(f"[Fetcher] Web scraper error: {e}")

    total = len(apollo_leads)
    print(f"\n[Fetcher] Total leads ready: {total}")
    return apollo_leads[:needed]


# ============================================================
# APOLLO.IO
# ============================================================

def _fetch_from_apollo(already_contacted_emails: set, page: int = 1, needed: int = None) -> tuple[list[dict], bool]:
    """
    Fetch from Apollo.io API.
    Returns (leads_list, success_bool).
    """
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
    }

    if needed is None:
        needed = LEADS_PER_DAY

    payload = {
        "api_key": APOLLO_API_KEY,
        "page": page,
        "per_page": needed * 3,
        "person_titles": APOLLO_TITLES,
        "person_locations": APOLLO_LOCATIONS,
        "contact_email_status": ["verified"],
    }

    if APOLLO_INDUSTRIES:
        payload["q_organization_industries"] = APOLLO_INDUSTRIES

    print(f"[Apollo] Fetching leads (page {page})...")

    try:
        response = requests.post(
            APOLLO_SEARCH_URL,
            headers=headers,
            json=payload,
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            people = data.get("people", [])
            print(f"[Apollo] Got {len(people)} raw results.")
            leads = _parse_apollo_leads(people, already_contacted_emails, needed)
            return leads, True

        elif response.status_code == 401:
            print("[Apollo] Invalid API key — skipping Apollo.")
            return [], False

        elif response.status_code == 422:
            # Often means monthly quota exhausted
            print("[Apollo] Apollo quota likely exhausted for this month.")
            return [], False

        elif response.status_code == 429:
            print("[Apollo] Rate limit hit. Waiting 60s...")
            time.sleep(60)
            return _fetch_from_apollo(already_contacted_emails, page)

        else:
            print(f"[Apollo] Unexpected status {response.status_code}")
            return [], False

    except requests.exceptions.ConnectionError:
        print("[Apollo] No internet connection.")
        return [], False
    except requests.exceptions.Timeout:
        print("[Apollo] Request timed out.")
        return [], False
    except Exception as e:
        print(f"[Apollo] Error: {e}")
        return [], False


def _parse_apollo_leads(people: list, already_contacted_emails: set, needed: int = None) -> list[dict]:
    """Parse Apollo response into clean lead dicts."""
    if needed is None:
        needed = LEADS_PER_DAY
    leads = []

    for person in people:
        email = person.get("email")
        if not email or email.lower() in already_contacted_emails:
            continue

        email_status = person.get("email_status", "")
        if email_status in ["invalid", "likely_invalid"]:
            continue

        lead = {
            "first_name": person.get("first_name", ""),
            "last_name": person.get("last_name", ""),
            "full_name": person.get("name", ""),
            "email": email.lower(),
            "title": person.get("title", ""),
            "company": _get_company(person),
            "linkedin_url": person.get("linkedin_url", ""),
            "city": person.get("city", ""),
            "state": person.get("state", ""),
            "country": person.get("country", "United States"),
            "industry": _get_industry(person),
            "website": _get_website(person),
            "source": "apollo",
        }

        if lead["first_name"] and lead["email"]:
            leads.append(lead)

        if len(leads) >= needed:
            break

    print(f"[Apollo] {len(leads)} usable leads after filtering.")
    return leads


def _get_company(person: dict) -> str:
    org = person.get("organization")
    if org:
        return org.get("name", "")
    return person.get("company_name", "")


def _get_industry(person: dict) -> str:
    org = person.get("organization")
    if org:
        return org.get("industry", "")
    return ""


def _get_website(person: dict) -> str:
    org = person.get("organization")
    if org:
        return org.get("website_url", "")
    return ""


# ---- TEST ----
if __name__ == "__main__":
    print("Testing lead fetcher (Apollo + scraper fallback)...")
    leads = fetch_leads(already_contacted_emails=set())
    if leads:
        print(f"\nSample lead:")
        print(json.dumps(leads[0], indent=2))
    else:
        print("No leads returned.")
