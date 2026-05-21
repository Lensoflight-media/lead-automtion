# ============================================================
# web_scraper.py — Free Unlimited Lead Scraper (Fallback)
# ============================================================
# Sources:
#   1. DuckDuckGo search → find company/founder websites
#   2. Website email extractor → regex scrape contact emails
#   3. Yelp business scraper → US business contacts
#   4. ProductHunt → startup makers / founders
# ============================================================

import re
import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from config import LEADS_PER_DAY, SCRAPER_SEARCH_QUERIES, SCRAPER_DELAY_SECONDS


# ── Rotate user agents to avoid blocks ──
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# Emails to skip (generic / useless)
SKIP_EMAIL_PATTERNS = [
    r"noreply", r"no-reply", r"donotreply", r"do-not-reply",
    r"unsubscribe", r"optout", r"opt-out",
    r"support", r"help@", r"abuse@", r"spam@",
    r"privacy", r"legal", r"press@", r"news@",
    r"careers", r"jobs@", r"hr@", r"recruiting",
    r"media@", r"pr@", r"publicrelations",
    r"admin@", r"webmaster", r"postmaster",
    r"sales@", r"billing@", r"accounts@",
    r"generalcounsel", r"counsel@", r"compliance",
    r"recall", r"alert@", r"notifications",
    r"ecom", r"sys@", r"system@", r"mailer",
    r"example\.com", r"test\.com", r"placeholder",
    r"\.png", r"\.jpg", r"\.gif", r"\.svg",
    r"sentry", r"bugsnag", r"rollbar",
]

# Max emails to take from any single domain (avoid harvesting complaint boards)
MAX_EMAILS_PER_DOMAIN = 1

# Domains that are complaint/review sites — skip entirely
SKIP_SITE_DOMAINS = [
    "complaintsboard", "bbb.org", "ripoffreport", "trustpilot",
    "sitejabber", "yelp.com", "glassdoor", "indeed.com",
    "manta.com", "yellowpages", "whitepages", "spokeo",
    "pissedconsumer", "consumeraffairs",
]

# Target email prefixes (prefer these — likely founder/owner)
PRIORITY_EMAIL_PREFIXES = [
    "founder", "ceo", "hello", "hi", "info", "contact",
    "collab", "partner", "brand", "media", "marketing", "team",
]

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]{1,64}@[a-zA-Z0-9.\-]{1,253}\.[a-zA-Z]{2,10}"
)


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def _build_niche_queries(niche: str) -> list:
    """Generate targeted DuckDuckGo search queries from a niche string."""
    n = niche.strip()
    return [
        f"{n} founder contact email",
        f"{n} CEO email contact us site:.com",
        f"{n} owner contact information email",
        f"{n} brand founder email collab",
        f"{n} company founder contact site:.com",
        f"{n} founder hello@ email",
        f"{n} startup founder email",
        f"{n} director contact email site:.com",
    ]


def scrape_leads(already_contacted_emails: set, needed: int = None, niche: str = "") -> list[dict]:
    """
    Run all scrapers and return combined unique leads.
    already_contacted_emails: set of emails already emailed — skip these.
    needed: how many leads to collect (defaults to LEADS_PER_DAY).
    niche: optional niche to focus queries (e.g. 'beauty brands in Texas').
            If empty, uses default SCRAPER_SEARCH_QUERIES from config.
    """
    if needed is None:
        needed = LEADS_PER_DAY

    if niche:
        queries = _build_niche_queries(niche)
        print(f"[Scraper] Using niche queries for: '{niche}' ({len(queries)} queries)")
    else:
        queries = SCRAPER_SEARCH_QUERIES
        print(f"[Scraper] Using default search queries ({len(queries)} queries)")

    print(f"\n[Scraper] Starting free web scraper — need {needed} leads...")
    all_leads = []
    seen_emails = set(already_contacted_emails)

    # ── Source 1: DuckDuckGo → website email extraction ──
    # NOTE: seen_emails is passed by ref — each scraper adds found emails to it
    # so we don't double-check here, just extend directly
    print("[Scraper] Source 1: DuckDuckGo search + website email extraction...")
    ddg_leads = _scrape_via_duckduckgo(seen_emails, needed, queries)
    all_leads.extend(ddg_leads)

    if len(all_leads) < needed:
        # ── Source 2: Yelp business scraper ──
        print(f"[Scraper] Source 2: Yelp business directory...")
        yelp_leads = _scrape_yelp(seen_emails, needed - len(all_leads))
        all_leads.extend(yelp_leads)

    if len(all_leads) < needed:
        # ── Source 3: ProductHunt makers ──
        print(f"[Scraper] Source 3: ProductHunt makers...")
        ph_leads = _scrape_producthunt(seen_emails, needed - len(all_leads))
        all_leads.extend(ph_leads)

    print(f"[Scraper] Total collected: {len(all_leads)} leads.")
    return all_leads[:needed]


# ============================================================
# SOURCE 1: DuckDuckGo → Websites → Email Extraction
# ============================================================

def _scrape_via_duckduckgo(seen_emails: set, needed: int, queries: list = None) -> list[dict]:
    """
    Search DuckDuckGo with target queries → visit result sites → extract emails.
    """
    leads = []
    if queries is None:
        queries = SCRAPER_SEARCH_QUERIES.copy()
    else:
        queries = list(queries)
    random.shuffle(queries)

    for query in queries:
        if len(leads) >= needed:
            break

        print(f"  [DDG] Query: '{query}'")
        urls = _duckduckgo_search(query, max_results=8)
        _polite_delay()

        for url in urls:
            if len(leads) >= needed:
                break
            if _is_skip_domain(url):
                continue

            site_leads = _extract_leads_from_site(url, seen_emails)
            for lead in site_leads:
                if lead["email"] not in seen_emails:
                    leads.append(lead)
                    seen_emails.add(lead["email"])
                    print(f"  [DDG] ✓ Found: {lead['email']} ({lead.get('company', 'unknown')})")

            _polite_delay()

    return leads


def _duckduckgo_search(query: str, max_results: int = 8) -> list[str]:
    """
    Scrape DuckDuckGo HTML results for URLs.
    Returns list of result URLs.
    """
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        params = {"q": query, "kl": "us-en", "kp": "-2"}
        resp = requests.get(
            "https://html.duckduckgo.com/html/",
            params=params,
            headers=headers,
            timeout=15,
        )
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        urls = []

        for result in soup.select(".result__url"):
            href = result.get("href") or result.get_text(strip=True)
            if href and href.startswith("http"):
                urls.append(href)
            if len(urls) >= max_results:
                break

        # Also try result links
        if not urls:
            for a in soup.select(".result__a"):
                href = a.get("href", "")
                if "uddg=" in href:
                    # DuckDuckGo redirect URL — extract real URL
                    import urllib.parse
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                    real = parsed.get("uddg", [""])[0]
                    if real.startswith("http"):
                        urls.append(urllib.parse.unquote(real))
                elif href.startswith("http"):
                    urls.append(href)
                if len(urls) >= max_results:
                    break

        return urls

    except Exception as e:
        print(f"  [DDG] Search error: {e}")
        return []


def _extract_leads_from_site(url: str, seen_emails: set) -> list[dict]:
    """
    Visit a website and extract emails + basic info.
    Checks homepage + /contact + /about pages.
    Max 1 email per domain to avoid harvesting junk sites.
    """
    domain = _get_domain(url)
    if not domain:
        return []

    # Skip complaint/review/directory sites immediately
    if _is_skip_domain(url):
        return []

    company_name = _domain_to_company_name(domain)

    pages_to_check = [url]
    base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    for path in ["/contact", "/about", "/contact-us", "/about-us", "/team"]:
        pages_to_check.append(base + path)

    found_emails = []  # ordered list, priority first

    for page_url in pages_to_check:
        if len(found_emails) >= MAX_EMAILS_PER_DOMAIN:
            break
        try:
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            resp = requests.get(page_url, headers=headers, timeout=10, allow_redirects=True)
            if resp.status_code != 200:
                continue

            emails = _extract_emails_from_html(resp.text)

            for email in emails:
                email_lower = email.lower()
                if email_lower in seen_emails:
                    continue
                if email_lower in found_emails:
                    continue
                if _is_skip_email(email_lower):
                    continue
                found_emails.append(email_lower)
                if len(found_emails) >= MAX_EMAILS_PER_DOMAIN:
                    break

        except Exception:
            continue

        _polite_delay(short=True)

    # Build leads
    leads = []
    for email in found_emails:
        lead = _build_scraped_lead(email, company_name, domain, url)
        leads.append(lead)

    return leads


def _extract_emails_from_html(html: str) -> list[str]:
    """Extract emails from HTML content. Prioritize founder/owner emails."""
    # Also decode mailto: links
    soup = BeautifulSoup(html, "lxml")

    emails = set()

    # From mailto: links
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("mailto:"):
            email = href[7:].split("?")[0].strip()
            if EMAIL_REGEX.match(email):
                emails.add(email.lower())

    # From raw text
    text = soup.get_text()
    for match in EMAIL_REGEX.findall(text):
        emails.add(match.lower())

    # Sort: priority emails first
    def priority_score(email):
        prefix = email.split("@")[0]
        for p in PRIORITY_EMAIL_PREFIXES:
            if p in prefix:
                return 0
        return 1

    return sorted(emails, key=priority_score)


# ============================================================
# SOURCE 2: Yelp Business Scraper
# ============================================================

def _scrape_yelp(seen_emails: set, needed: int) -> list[dict]:
    """
    Scrape Yelp search results for US businesses.
    Visit each business page → extract website → find email.
    """
    leads = []
    categories = ["brands", "influencer marketing", "digital marketing", "ecommerce"]

    for category in categories:
        if len(leads) >= needed:
            break

        try:
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            url = f"https://www.yelp.com/search?find_desc={category.replace(' ', '+')}&find_loc=United+States"
            resp = requests.get(url, headers=headers, timeout=15)

            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "lxml")

            # Find business listing links
            biz_links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/biz/" in href and "?" not in href:
                    full = "https://www.yelp.com" + href if href.startswith("/") else href
                    if full not in biz_links:
                        biz_links.append(full)
                if len(biz_links) >= 6:
                    break

            for biz_url in biz_links:
                if len(leads) >= needed:
                    break
                biz_leads = _extract_yelp_business(biz_url, seen_emails)
                leads.extend(biz_leads)
                _polite_delay()

        except Exception as e:
            print(f"  [Yelp] Error: {e}")
            continue

        _polite_delay()

    return leads


def _extract_yelp_business(biz_url: str, seen_emails: set) -> list[dict]:
    """Visit Yelp business page → get website → scrape email."""
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        resp = requests.get(biz_url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "lxml")

        # Get business name
        company = ""
        h1 = soup.find("h1")
        if h1:
            company = h1.get_text(strip=True)

        # Get website link
        website = ""
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "biz_redir" in href or ("http" in href and "yelp.com" not in href):
                website = href
                break

        if website and not _is_skip_domain(website):
            return _extract_leads_from_site(website, seen_emails)

    except Exception:
        pass

    return []


# ============================================================
# SOURCE 3: ProductHunt Makers
# ============================================================

def _scrape_producthunt(seen_emails: set, needed: int) -> list[dict]:
    """
    Scrape ProductHunt for maker profiles → visit their websites → find emails.
    """
    leads = []

    try:
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        # ProductHunt popular products page
        resp = requests.get("https://www.producthunt.com/", headers=headers, timeout=15)
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "lxml")

        # Find product links
        product_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("/posts/") and href.count("/") == 2:
                full = "https://www.producthunt.com" + href
                if full not in product_links:
                    product_links.append(full)
            if len(product_links) >= 10:
                break

        for product_url in product_links:
            if len(leads) >= needed:
                break

            try:
                _polite_delay()
                resp = requests.get(product_url, headers=headers, timeout=10)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "lxml")

                # Get product website
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if (
                        href.startswith("http")
                        and "producthunt.com" not in href
                        and not _is_skip_domain(href)
                    ):
                        site_leads = _extract_leads_from_site(href, seen_emails)
                        for lead in site_leads:
                            if lead["email"] not in seen_emails:
                                leads.append(lead)
                                seen_emails.add(lead["email"])
                                print(f"  [PH] ✓ Found: {lead['email']} ({lead.get('company', '')})")
                        break

            except Exception:
                continue

    except Exception as e:
        print(f"  [ProductHunt] Error: {e}")

    return leads


# ============================================================
# HELPERS
# ============================================================

def _build_scraped_lead(email: str, company: str, domain: str, source_url: str) -> dict:
    """Build a standardized lead dict from scraped data."""
    # Try to guess first name from email prefix
    prefix = email.split("@")[0].lower()
    first_name = ""
    last_name = ""
    # Only try if prefix looks like a real name (not a generic word)
    generic = {
        "info", "contact", "hello", "hi", "team", "support", "help",
        "admin", "mail", "email", "office", "founder", "ceo", "collab",
        "partner", "brand", "media", "marketing", "sales", "social",
        "general", "enquiries", "enquiry", "customerservice", "service",
        "membership", "atcontact", "noreply", "press", "pr",
    }
    if prefix not in generic and prefix.replace(".", "").replace("_", "").replace("-", "").isalpha():
        # firstname.lastname or firstname_lastname or firstname-lastname
        for sep in (".", "_", "-"):
            if sep in prefix:
                parts = prefix.split(sep)
                if len(parts) >= 2 and all(p.isalpha() and len(p) > 1 for p in parts[:2]):
                    first_name = parts[0].capitalize()
                    last_name = parts[1].capitalize()
                break
        else:
            # Single word — only use if it looks like a real name (3+ chars, not a generic word)
            if len(prefix) >= 3 and prefix.isalpha():
                first_name = prefix.capitalize()

    industry = _detect_industry(company, domain)

    return {
        "first_name": first_name or "",
        "last_name": last_name or "",
        "full_name": (first_name + " " + last_name).strip() if first_name else "",
        "email": email,
        "title": "",
        "company": company,
        "linkedin_url": "",
        "city": "",
        "state": "",
        "country": "United States",
        "industry": industry,
        "website": f"https://{domain}",
        "source": "web_scraper",
    }


def _detect_industry(company: str, domain: str) -> str:
    """Guess the industry from the company name and domain using keyword matching."""
    text = (company + " " + domain).lower()

    rules = [
        ("Beauty & Cosmetics",   ["beauty", "cosmetic", "skincare", "skin care", "makeup", "make-up",
                                   "lipstick", "serum", "glam", "glow", "lash", "brow", "fragrance",
                                   "parfum", "salon", "spa", "nail", "esthetics"]),
        ("Fashion & Apparel",    ["fashion", "apparel", "clothing", "clothes", "wear", "boutique",
                                   "streetwear", "denim", "footwear", "shoes", "sneaker", "handbag",
                                   "accessory", "accessories", "jewel", "luxury"]),
        ("Health & Wellness",    ["wellness", "health", "fitness", "gym", "yoga", "supplement",
                                   "nutrition", "organic", "herbal", "holistic", "medic",
                                   "mindful", "mental", "therapy", "weight"]),
        ("Real Estate",          ["realty", "realtor", "real estate", "realestate", "property",
                                   "properties", "homes", "housing", "mortgage", "broker"]),
        ("Finance & Tax",        ["finance", "financial", "tax", "taxes", "accounting", "cpa",
                                   "bookkeeping", "wealth", "invest", "capital", "insurance"]),
        ("Food & Beverage",      ["food", "restaurant", "cafe", "coffee", "bakery", "catering",
                                   "grocery", "meal", "diet", "snack", "beverage", "drink", "juice"]),
        ("E-Commerce / DTC",     ["shop", "store", "ecommerce", "e-commerce", "dtc", "brand",
                                   "merch", "marketplace", "dropship"]),
        ("Content Creator",      ["influencer", "creator", "content", "media", "blog", "vlog",
                                   "podcast", "youtube", "tiktok", "instagram"]),
        ("Coaching / Consulting", ["coach", "coaching", "consult", "mentor", "academy",
                                    "training", "course", "mastermind", "speaker"]),
        ("Technology",           ["tech", "software", "saas", "app", "digital", "ai", "data",
                                   "platform", "cloud", "cyber", "startup", "dev"]),
    ]

    for industry_name, keywords in rules:
        if any(kw in text for kw in keywords):
            return industry_name

    return ""


def _get_domain(url: str) -> str:
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        return domain
    except Exception:
        return ""


def _domain_to_company_name(domain: str) -> str:
    """Convert domain to readable company name. e.g. 'cool-brand.com' → 'Cool Brand'"""
    name = domain.split(".")[0]
    name = name.replace("-", " ").replace("_", " ")
    return name.title()


def _is_skip_domain(url: str) -> bool:
    """Skip social media, search engines, complaint boards, ad networks."""
    skip = [
        "facebook.com", "twitter.com", "instagram.com", "linkedin.com",
        "youtube.com", "tiktok.com", "pinterest.com", "reddit.com",
        "google.com", "bing.com", "yahoo.com", "duckduckgo.com",
        "amazon.com", "ebay.com", "etsy.com", "shopify.com",
        "yelp.com", "wikipedia.org", "apple.com", "microsoft.com",
        "github.com", "medium.com", "substack.com",
        # Complaint / review / directory sites
        "complaintsboard", "bbb.org", "ripoffreport", "trustpilot",
        "sitejabber", "glassdoor", "indeed.com", "manta.com",
        "yellowpages", "whitepages", "spokeo", "pissedconsumer",
        "consumeraffairs", "scamadviser", "scamwarner",
    ]
    url_lower = url.lower()
    return any(s in url_lower for s in skip)


def _is_skip_email(email: str) -> bool:
    """Return True if email should be ignored."""
    for pattern in SKIP_EMAIL_PATTERNS:
        if re.search(pattern, email):
            return True
    # Skip very short or obviously fake
    local = email.split("@")[0]
    if len(local) < 2:
        return True
    # Skip image/file false positives
    if any(email.endswith(ext) for ext in [".png", ".jpg", ".gif", ".css", ".js"]):
        return True
    return False


def _polite_delay(short: bool = False):
    """Wait between requests to avoid IP bans."""
    delay = random.uniform(1.0, 2.5) if short else random.uniform(
        SCRAPER_DELAY_SECONDS * 0.8,
        SCRAPER_DELAY_SECONDS * 1.5,
    )
    time.sleep(delay)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("Testing web scraper (this may take 1-2 minutes)...\n")
    leads = scrape_leads(already_contacted_emails=set(), needed=3)
    print(f"\n--- Results: {len(leads)} leads ---")
    for lead in leads:
        print(f"  {lead['email']} | {lead['company']} | {lead.get('website', '')}")
