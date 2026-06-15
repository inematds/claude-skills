#!/usr/bin/env python3
"""
Agent 03 — Qualification Filter (Apify Google Search)
=====================================================
Same logic as qualify_leads_v3.py but uses Apify's Google Search Scraper
instead of DuckDuckGo for website enrichment and brand scoring.

Only processes rows that are missing a qualification_score.
Already-scored rows are kept as-is.

Usage:
  python3 agent3_qualification_filter/qualify_leads_apify.py \
    --input agent3_qualification_filter/qualified_brands_2026-03-10_manually_test1.csv
"""

import argparse
import csv
import json
import os
import re
import time
import urllib.request
import urllib.parse
from datetime import date
from urllib.parse import urlparse

# ── CONFIG ────────────────────────────────────────────────────────────────────
OUTPUT_DIR = "agent3_qualification_filter"
TODAY = date.today().isoformat()

APIFY_BASE = "https://api.apify.com/v2"
ACTOR = "apify~google-search-scraper"

QUALIFIED_COLS = [
    "lead_id", "business_name", "type", "platform", "black_owned",
    "website", "location", "instagram", "facebook", "tiktok",
    "niche_category", "source_query", "merged_from", "date_prepared",
    "website_status", "website_previous", "brand_signals",
    "search_name",
    "qualification_score", "product_dev_score", "data_maturity_score",
    "brand_maturity_score", "product_dev_evidence", "data_evidence",
    "qualification_tier", "scoring_depth",
]

# ── SKIP DOMAINS ──────────────────────────────────────────────────────────────
SOCIAL_DOMAINS = {
    "instagram.com", "facebook.com", "linkedin.com",
    "tiktok.com", "twitter.com", "x.com", "pinterest.com",
    "youtube.com", "threads.net",
}
RETAILER_DOMAINS = {
    "amazon.com", "amazon.co.uk", "etsy.com", "ebay.com", "ebay.co.uk",
    "boots.com", "superdrug.com", "lookfantastic.com", "asos.com",
    "feelunique.com", "naturalisticproducts.co.uk", "cultbeauty.co.uk",
    "hollandandbarrett.com", "sephora.com", "ulta.com", "target.com",
    "walmart.com", "cvs.com", "walgreens.com", "sallybeauty.com",
    "tjmaxx.com", "nordstrom.com", "macys.com",
}
COUPON_DOMAINS = {
    "knoji.com", "dealspotr.com", "promotioncode.org", "vouchercloud.com",
    "honey.com", "retailmenot.com", "groupon.com", "hotukdeals.com",
    "wethrift.com", "couponbirds.com", "vouchercodes.co.uk",
    "discountcode.co.uk", "topcashback.co.uk", "quidco.com",
}
DIRECTORY_DOMAINS = {
    "google.com", "yelp.com", "yellowpages.com", "bbb.org",
    "tripadvisor.com", "thumbtack.com", "bark.com", "reddit.com",
    "wikipedia.org", "crunchbase.com", "trustpilot.com",
    "glassdoor.com", "indeed.com", "companies.house.gov.uk",
}
BOOKING_DOMAINS = {
    "booksy.com", "fresha.com", "vagaro.com", "schedulicity.com",
    "styleseat.com", "squareup.com", "square.site", "genbook.com",
    "treatwell.co.uk", "mindbodyonline.com",
}
JUNK_DOMAINS = {
    "duckduckgo.com", "play.google.com", "apps.apple.com",
    "m.yelp.com", "affiliates.naturalisticproducts.co.uk",
}
SKIP_DOMAINS = (
    SOCIAL_DOMAINS | RETAILER_DOMAINS | COUPON_DOMAINS |
    DIRECTORY_DOMAINS | BOOKING_DOMAINS | JUNK_DOMAINS
)

# ── HELPERS ───────────────────────────────────────────────────────────────────

def get_apify_token() -> str:
    # Try .env file
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("APIFY_API_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    # Try environment
    token = os.environ.get("APIFY_API_TOKEN", "")
    if not token:
        raise RuntimeError("APIFY_API_TOKEN not found in .env or environment")
    return token


def root_domain(url: str) -> str:
    if not url:
        return ""
    try:
        host = urlparse(url).netloc.lower()
        host = host.removeprefix("www.")
        parts = host.split(".")
        KNOWN_SLDS = {"co", "com", "org", "net", "gov", "edu", "ac", "me", "ltd", "plc"}
        if len(parts) >= 3 and parts[-2] in KNOWN_SLDS:
            return ".".join(parts[-3:])
        return ".".join(parts[-2:]) if len(parts) >= 2 else host
    except Exception:
        return ""


def is_skip_domain(url: str) -> bool:
    domain = root_domain(url)
    return any(domain == s or domain.endswith("." + s) for s in SKIP_DOMAINS)


def domain_matches_name(url: str, name: str) -> bool:
    if not url or not name:
        return False
    domain = root_domain(url)
    domain_slug = re.sub(r"[^a-z0-9]", "", domain.split(".")[0])
    name_slug = re.sub(r"[^a-z0-9]", "", name.lower())
    if len(name_slug) >= 3 and len(domain_slug) >= 3:
        if (name_slug.startswith(domain_slug) or domain_slug.startswith(name_slug)
                or name_slug in domain_slug or domain_slug in name_slug):
            return True
    stopwords = {"the", "and", "of", "by", "for", "a", "an", "its", "my",
                 "our", "llc", "inc", "co", "uk", "us", "brand", "beauty",
                 "hair", "care", "natural"}
    tokens = [t for t in re.sub(r"[^a-z0-9\s]", "", name.lower()).split()
              if t not in stopwords and len(t) >= 3]
    if not tokens:
        return False
    longest = max(tokens, key=len)
    if len(longest) >= 4 and longest in domain_slug:
        return True
    concat = "".join(tokens)
    if len(concat) >= 4 and (concat in domain_slug or domain_slug in concat):
        return True
    return False


def fetch_url(url: str, timeout: int = 15) -> str:
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        return ""


# ── APIFY GOOGLE SEARCH ──────────────────────────────────────────────────────

def apify_google_search(queries: list[str], token: str) -> list[dict]:
    """
    Run Google searches via Apify and return list of {title, url, description}.
    Batches all queries into a single Apify run.
    """
    body = json.dumps({
        "queries": "\n".join(queries),
        "maxPagesPerQuery": 1,
        "resultsPerPage": 10,
        "countryCode": "us",
        "languageCode": "en",
        "includeUnfilteredResults": False,
        "saveHtml": False,
        "saveHtmlToKeyValueStore": False,
    }).encode("utf-8")

    # Try sync run first (2 min timeout)
    sync_url = f"{APIFY_BASE}/acts/{ACTOR}/run-sync-get-dataset-items?token={token}&timeout=120&memory=256"
    req = urllib.request.Request(
        sync_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=130) as resp:
            raw = json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception as e:
        # Fall back to async
        print(f"    Sync run failed ({e}), trying async…", flush=True)
        raw = _apify_async_run(body, token)

    results = []
    for page in raw:
        for item in page.get("organicResults", []):
            if item.get("url"):
                results.append({
                    "title": item.get("title", ""),
                    "url": item["url"],
                    "description": item.get("description", ""),
                    "query": page.get("searchQuery", {}).get("term", ""),
                })
    return results


def _apify_async_run(body: bytes, token: str) -> list:
    """Start an async Apify run and poll until done."""
    run_url = f"{APIFY_BASE}/acts/{ACTOR}/runs?token={token}"
    req = urllib.request.Request(
        run_url, data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        run_data = json.loads(resp.read().decode("utf-8", errors="replace"))

    run_id = run_data["data"]["id"]
    status = run_data["data"]["status"]
    print(f"    Apify run started: {run_id} (status={status})", flush=True)

    while status not in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
        time.sleep(10)
        poll_url = f"{APIFY_BASE}/actor-runs/{run_id}?token={token}"
        poll_req = urllib.request.Request(poll_url)
        with urllib.request.urlopen(poll_req, timeout=30) as resp:
            poll_data = json.loads(resp.read().decode("utf-8", errors="replace"))
        status = poll_data["data"]["status"]
        print(f"    Polling… status={status}", flush=True)

    if status != "SUCCEEDED":
        raise RuntimeError(f"Apify run ended with status: {status}")

    dataset_id = run_data["data"]["defaultDatasetId"]
    items_url = f"{APIFY_BASE}/datasets/{dataset_id}/items?token={token}"
    items_req = urllib.request.Request(items_url)
    with urllib.request.urlopen(items_req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def apify_search_urls(query: str, token: str) -> list[str]:
    """Run a single Google query via Apify and return result URLs."""
    results = apify_google_search([query], token)
    urls = []
    seen = set()
    for r in results:
        url = r["url"]
        d = root_domain(url)
        if d and d not in seen and not is_skip_domain(url):
            seen.add(d)
            urls.append(url)
    return urls


def apify_search_text(queries: list[str], token: str) -> str:
    """Run queries via Apify and return all titles + descriptions + URLs as one string for signal matching."""
    results = apify_google_search(queries, token)
    parts = []
    for r in results:
        parts.append(r.get("title", ""))
        parts.append(r.get("description", ""))
        parts.append(r.get("url", ""))
    return " ".join(parts).lower()


# ── BRAND CLASSIFICATION ─────────────────────────────────────────────────────

PRODUCT_URL_SIGNALS = ["/products", "/collections", "/shop", "/our-products", "/store"]
FORMULA_TEXT_SIGNALS = [
    "our formula", "we formulate", "handmade by us", "our ingredients",
    "hand-crafted", "small batch", "made in-house", "our blend",
    "proprietary", "exclusive formula", "created by us",
]
BRAND_OWNERSHIP_SIGNALS = ["™", "®", "trade mark", "registered mark"]
THIRD_PARTY_SIGNALS = [
    "we stock", "we carry", "brands we love", "featured brands",
    "shop brands", "our brands", "partner brands", "browse brands",
    "shop by brand",
]
SALON_SIGNALS = [
    "book appointment", "book now", "our services", "salon services",
    "hair services", "price list", "walk-ins", "stylist",
    "book online", "schedule appointment",
]


def classify_business_type(website: str, business_name: str, current_type: str) -> tuple[str, list]:
    if not website:
        return current_type, []

    html = fetch_url(website, timeout=20)
    if not html:
        return current_type, []

    html_lower = html.lower()
    signals = []
    has_products = False
    own_product_count = 0

    for signal in PRODUCT_URL_SIGNALS:
        if signal in html_lower:
            signals.append(f"has {signal} page")
            has_products = True

    for signal in FORMULA_TEXT_SIGNALS:
        if signal in html_lower:
            signals.append(signal)
            own_product_count += 1

    for mark in BRAND_OWNERSHIP_SIGNALS:
        if mark in html:
            signals.append(f"{mark} found")
            own_product_count += 1

    if business_name.lower() in html_lower and has_products:
        signals.append("brand name on product pages")
        own_product_count += 1

    for sig in ["our story", "founder", "founded by", "i started", "our journey", "about us"]:
        if sig in html_lower:
            signals.append(f"has '{sig}'")
            break

    retailer_count = sum(1 for s in THIRD_PARTY_SIGNALS if s in html_lower)
    salon_count = sum(1 for s in SALON_SIGNALS if s in html_lower)

    # Decision tree
    if salon_count >= 2 and own_product_count == 0:
        return current_type if current_type in ("salon", "barber") else "salon", signals
    if own_product_count > 0:
        return "brand", signals
    if has_products and retailer_count == 0 and len(signals) >= 2:
        return "brand", signals
    if retailer_count > 0 and own_product_count == 0:
        return "retailer", signals
    if has_products:
        return "brand", signals
    if current_type in ("salon", "barber"):
        return current_type, signals
    return "unknown", signals


# ── SCORING ───────────────────────────────────────────────────────────────────

_html_cache: dict[str, str] = {}


def fetch_cached(url: str, timeout: int = 20) -> str:
    if not url:
        return ""
    if url not in _html_cache:
        _html_cache[url] = fetch_url(url, timeout)
    return _html_cache[url]


def score_product_development_website(website: str) -> tuple[int, list[str]]:
    """Dimension 1 — Website-only signals (max 15 pts)."""
    score = 0
    evidence: list[str] = []

    html_lower = fetch_cached(website).lower()
    if not html_lower:
        return 0, []

    if any(s in html_lower for s in [
        "r&d", "research and development", "lab facility", "our lab",
        "clinical testing", "clinically formulated", "laboratory",
        "formulation process", "ingredient research", "our science",
        "our process", "our ingredients",
    ]):
        score += 8
        evidence.append("R&D/lab/process mentions on website")

    if any(s in html_lower for s in [
        "clinically tested", "clinically proven", "dermatologically tested",
        "dermatologist tested", "backed by science", "science-backed",
        "clinical study", "evidence-based", "scientifically formulated",
    ]):
        score += 7
        evidence.append("science-backed/clinically tested claims on website")

    return score, evidence


def score_product_development_apify(brand_name: str, token: str) -> tuple[int, list[str]]:
    """Dimension 1 — Apify Google Search signals (max 35 pts)."""
    score = 0
    evidence: list[str] = []

    # +15/+25 LinkedIn: formulation / R&D roles
    linkedin_text = apify_search_text([
        f'"{brand_name}" (formulation OR chemist OR "R&D" OR "product development" OR "cosmetic scientist") site:linkedin.com',
    ], token)
    senior = ["r&d director", "head of product", "chief scientific", "vp product",
              "vp of product", "director of product", "director, product"]
    junior = ["formulation", "chemist", "product development", "cosmetic scientist",
              "research and development"]
    if any(t in linkedin_text for t in senior):
        score += 25
        evidence.append("LinkedIn: senior R&D/product dev role found")
    elif any(t in linkedin_text for t in junior):
        score += 15
        evidence.append("LinkedIn: formulation/R&D team member found")

    # +10 Job listings
    jobs_text = apify_search_text([
        f'"{brand_name}" (formulation OR "product development" OR "R&D") (jobs OR careers OR hiring)',
    ], token)
    if any(t in jobs_text for t in ["formulation", "product development", "r&d", "cosmetic chemist"]):
        score += 10
        evidence.append("job listing: product development/formulation role found")

    return score, evidence


def score_data_maturity_website(website: str, row: dict) -> tuple[int, list[str]]:
    """Dimension 2 — Website-only signals (max 17 pts)."""
    score = 0
    evidence: list[str] = []

    html_lower = fetch_cached(website).lower()
    if not html_lower:
        return 0, []

    if any(s in html_lower for s in [
        "hair quiz", "find your", "hair type quiz", "take the quiz",
        "product finder", "personalised", "personalized",
        "recommend", "hair profiler", "diagnostic",
    ]):
        score += 8
        evidence.append("hair quiz/personalisation tool on website")

    if any(s in html_lower for s in [
        "reviews", "customer reviews", "write a review", "star rating",
        "trustpilot", "yotpo", "okendo", "stamped", "judge.me", "loox",
    ]):
        score += 5
        evidence.append("reviews/ratings system on website")

    if any(s in html_lower for s in [
        "klaviyo", "mailchimp", "omnisend", "drip", "attentive",
        "segment.com", "mixpanel", "hotjar", "heap.io", "amplitude",
        "google-analytics", "googletagmanager", "ga4",
    ]):
        score += 4
        evidence.append("marketing tech stack detected (email/analytics tools)")

    return score, evidence


def score_data_maturity_apify(brand_name: str, token: str) -> tuple[int, list[str]]:
    """Dimension 2 — Apify Google Search signals (max 13 pts)."""
    score = 0
    evidence: list[str] = []

    # +10 Data roles on LinkedIn
    linkedin_data = apify_search_text([
        f'"{brand_name}" ("data analyst" OR "data scientist" OR "data engineer" OR "CRM manager" OR "BI analyst") site:linkedin.com',
    ], token)
    if any(t in linkedin_data for t in [
        "data analyst", "data scientist", "data engineer",
        "crm manager", "bi analyst", "business intelligence",
    ]):
        score += 10
        evidence.append("LinkedIn: data/analytics/CRM role found")

    # +3 Public data/analytics mentions
    public_data = apify_search_text([
        f'"{brand_name}" (data OR analytics OR insights OR "customer data" OR "data-driven")',
    ], token)
    if any(t in public_data for t in ["data-driven", "customer data", "analytics", "insights"]):
        score += 3
        evidence.append("public data/analytics mentions found")

    return score, evidence


def score_brand_maturity_website(website: str, row: dict) -> tuple[int, list[str]]:
    """Dimension 3 — Website-only signals (max 9 pts)."""
    score = 0
    evidence: list[str] = []

    html_lower = fetch_cached(website).lower()

    social_count = sum(1 for k in ["instagram", "facebook", "tiktok"] if row.get(k))
    if social_count >= 2:
        score += 4
        evidence.append(f"{social_count} social platforms active")
    elif social_count == 1:
        score += 2

    import datetime
    current_year = datetime.date.today().year
    if html_lower:
        m = re.search(r"\b(?:founded|since|established|est\.?)\s+(?:in\s+)?(\d{4})\b", html_lower)
        if m:
            year = int(m.group(1))
            if 1990 <= year <= current_year - 2:
                score += 2
                evidence.append(f"founded {year}")

    if html_lower and any(s in html_lower for s in ["stockists", "where to buy", "find us in stores", "available at"]):
        score += 3
        evidence.append("stockists/where-to-buy page on website")

    return score, evidence


def score_brand_maturity_apify(brand_name: str, token: str) -> tuple[int, list[str]]:
    """Dimension 3 — Apify Google Search signals (max 14 pts)."""
    score = 0
    evidence: list[str] = []

    # +6 Stocked in major retailers
    retail_text = apify_search_text([
        f'"{brand_name}" (Boots OR "Whole Foods" OR Sephora OR Target OR Superdrug OR ULTA OR "Holland & Barrett")',
    ], token)
    retailers_found = [r for r in ["boots", "whole foods", "sephora", "target",
                                    "superdrug", "ulta", "holland & barrett"]
                       if r in retail_text]
    if retailers_found:
        score += 6
        evidence.append(f"stocked in: {', '.join(retailers_found[:3])}")

    # +5 Press coverage / awards
    press_text = apify_search_text([
        f'"{brand_name}" (award OR "as seen in" OR "featured in" OR "best of" OR winner)',
    ], token)
    if any(t in press_text for t in ["award", "as seen in", "featured in", "winner", "best of"]):
        score += 5
        evidence.append("press coverage/award mention found")

    # +3 Team size > 10 (LinkedIn)
    linkedin_co = apify_search_text([f'"{brand_name}" site:linkedin.com/company'], token)
    if any(t in linkedin_co for t in ["11-50", "51-200", "201-500", "501-1000", "1,001"]):
        score += 3
        evidence.append("LinkedIn: team size > 10")

    return score, evidence


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main(input_file: str):
    token = get_apify_token()
    print("=" * 60)
    print("Agent 03 — Qualification Filter (Apify Google Search)")
    print("=" * 60)

    # Load input
    print(f"\n[1] Loading: {input_file}")
    with open(input_file, newline="", encoding="latin-1") as f:
        rows = list(csv.DictReader(f))
    print(f"    → {len(rows)} total rows")

    # Split into already-scored and needs-scoring
    scored = [r for r in rows if r.get("qualification_score")]
    unscored = [r for r in rows if not r.get("qualification_score")]
    print(f"    → {len(scored)} already scored, {len(unscored)} to process")

    if not unscored:
        print("    Nothing to do — all rows already scored.")
        return

    # Phase 1b — Brand classification for unscored rows
    print(f"\n[2] Phase 1b — Brand classification ({len(unscored)} rows)")
    for idx, row in enumerate(unscored, start=1):
        name = row.get("business_name", "")
        website = row.get("website", "")
        current_type = row.get("type", "")

        # Mark website as confirmed if it exists and isn't a skip domain
        if website and not is_skip_domain(website):
            row["website_status"] = "confirmed"
            row["website_previous"] = website

        print(f"  [{idx}/{len(unscored)}] {name}", flush=True)
        if website:
            new_type, signals = classify_business_type(website, name, current_type)
            row["type"] = new_type
            row["brand_signals"] = ", ".join(signals)
            print(f"    → type={new_type}, signals={len(signals)}", flush=True)
        else:
            row.setdefault("brand_signals", "")

    # Phase 2 — Scoring (only brand rows)
    brand_rows = [r for r in unscored if r.get("type", "").lower() in ("brand", "salon with own brand")]
    # Normalize "Salon with own brand" to "brand" for scoring
    for r in brand_rows:
        if r.get("type", "").lower() == "salon with own brand":
            r["type"] = "brand"

    print(f"\n[3] Phase 2 — Brand scoring ({len(brand_rows)} brands)")

    # Pass 1: Website-only scoring
    print("\n  Pass 1 — Website-only scoring…")
    for idx, row in enumerate(brand_rows, start=1):
        name = row.get("business_name", "")
        website = row.get("website", "")
        print(f"    [{idx}/{len(brand_rows)}] {name}", flush=True)

        pd_score, pd_ev = score_product_development_website(website)
        dm_score, dm_ev = score_data_maturity_website(website, row)
        bm_score, bm_ev = score_brand_maturity_website(website, row)
        total = pd_score + dm_score + bm_score

        row["product_dev_score"] = pd_score
        row["data_maturity_score"] = dm_score
        row["brand_maturity_score"] = bm_score
        row["qualification_score"] = total
        row["product_dev_evidence"] = " | ".join(pd_ev) if pd_ev else "No product dev signals found"
        row["data_evidence"] = " | ".join(dm_ev) if dm_ev else "No data maturity signals found"
        row["scoring_depth"] = "website_only"
        print(f"      website_only score={total} (pd={pd_score} dm={dm_score} bm={bm_score})", flush=True)

    # Pass 2: Apify Google Search enrichment (all brands)
    _run_apify_pass2(brand_rows, token)

    # Assign tiers
    for row in unscored:
        total = int(row.get("qualification_score", 0))
        if total >= 70:
            row["qualification_tier"] = "Tier 1"
        elif total >= 50:
            row["qualification_tier"] = "Tier 2"
        elif total >= 30:
            row["qualification_tier"] = "Tier 3"
        else:
            row["qualification_tier"] = "Tier 4"

    # Merge: scored + newly scored, sort by qualification_score desc
    all_rows = scored + unscored
    all_rows.sort(key=lambda r: int(r.get("qualification_score", 0)), reverse=True)

    # Save & summarize
    output_file = os.path.join(OUTPUT_DIR, f"qualified_brands_{TODAY}.csv")
    _save_and_summarize(all_rows, input_file, output_file, len(scored), unscored, brand_rows)


def main_phase2_only(input_file: str):
    """Re-run Phase 2 (Apify search scoring) on all website_only rows."""
    token = get_apify_token()
    print("=" * 60)
    print("Agent 03 — Phase 2 Only (Apify Google Search)")
    print("=" * 60)

    # Load input
    print(f"\n[1] Loading: {input_file}")
    with open(input_file, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"    → {len(rows)} total rows")

    # Find website_only brand rows
    web_only = [r for r in rows if r.get("scoring_depth") == "website_only" and r.get("type") == "brand"]
    already_full = [r for r in rows if r.get("scoring_depth") == "full"]
    print(f"    → {len(web_only)} website_only brands to enrich")
    print(f"    → {len(already_full)} already fully scored (skipped)")

    if not web_only:
        print("    Nothing to do — no website_only brands found.")
        return

    # Checkpoint support
    checkpoint_file = os.path.join(OUTPUT_DIR, f"apify_checkpoint_{TODAY}.json")
    checkpoint: dict = {}
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, "r") as cf:
                checkpoint = json.load(cf)
            print(f"    Resuming from checkpoint ({len(checkpoint)} brands already done)")
        except (json.JSONDecodeError, OSError):
            checkpoint = {}

    # Run Apify Pass 2
    print(f"\n[2] Apify Google Search enrichment ({len(web_only)} brands)…")
    for idx, row in enumerate(web_only, start=1):
        name = row.get("business_name", "")
        lead_id = row.get("lead_id", "")

        # Skip if already in checkpoint
        if lead_id and lead_id in checkpoint:
            saved = checkpoint[lead_id]
            row["product_dev_score"] = min(int(row["product_dev_score"]) + saved["pd"], 50)
            row["data_maturity_score"] = min(int(row["data_maturity_score"]) + saved["dm"], 30)
            row["brand_maturity_score"] = min(int(row["brand_maturity_score"]) + saved["bm"], 20)
            row["qualification_score"] = (
                int(row["product_dev_score"]) +
                int(row["data_maturity_score"]) +
                int(row["brand_maturity_score"])
            )
            if saved.get("pd_ev"):
                existing = row.get("product_dev_evidence", "")
                if existing and existing != "No product dev signals found":
                    row["product_dev_evidence"] = existing + " | " + saved["pd_ev"]
                else:
                    row["product_dev_evidence"] = saved["pd_ev"]
            if saved.get("dm_ev"):
                existing = row.get("data_evidence", "")
                if existing and existing != "No data maturity signals found":
                    row["data_evidence"] = existing + " | " + saved["dm_ev"]
                else:
                    row["data_evidence"] = saved["dm_ev"]
            row["scoring_depth"] = "full"
            print(f"    [{idx}/{len(web_only)}] {name[:50]} (from checkpoint, score={row['qualification_score']})", flush=True)
            continue

        print(f"    [{idx}/{len(web_only)}] Apify scoring: {name}", flush=True)

        pd_apify, pd_apify_ev = score_product_development_apify(name, token)
        dm_apify, dm_apify_ev = score_data_maturity_apify(name, token)
        bm_apify, bm_apify_ev = score_brand_maturity_apify(name, token)

        # Add Apify scores on top of existing website scores (capped)
        row["product_dev_score"] = min(int(row["product_dev_score"]) + pd_apify, 50)
        row["data_maturity_score"] = min(int(row["data_maturity_score"]) + dm_apify, 30)
        row["brand_maturity_score"] = min(int(row["brand_maturity_score"]) + bm_apify, 20)
        row["qualification_score"] = (
            int(row["product_dev_score"]) +
            int(row["data_maturity_score"]) +
            int(row["brand_maturity_score"])
        )

        if pd_apify_ev:
            existing = row.get("product_dev_evidence", "")
            if existing and existing != "No product dev signals found":
                row["product_dev_evidence"] = existing + " | " + " | ".join(pd_apify_ev)
            else:
                row["product_dev_evidence"] = " | ".join(pd_apify_ev)
        if dm_apify_ev:
            existing = row.get("data_evidence", "")
            if existing and existing != "No data maturity signals found":
                row["data_evidence"] = existing + " | " + " | ".join(dm_apify_ev)
            else:
                row["data_evidence"] = " | ".join(dm_apify_ev)
        row["scoring_depth"] = "full"

        print(f"      final score={row['qualification_score']} "
              f"(pd={row['product_dev_score']} dm={row['data_maturity_score']} bm={row['brand_maturity_score']})",
              flush=True)

        # Save checkpoint
        checkpoint[lead_id] = {
            "pd": pd_apify, "dm": dm_apify, "bm": bm_apify,
            "pd_ev": " | ".join(pd_apify_ev), "dm_ev": " | ".join(dm_apify_ev),
        }
        try:
            with open(checkpoint_file, "w") as cf:
                json.dump(checkpoint, cf)
        except OSError:
            pass

    # Re-assign tiers for ALL rows
    for row in rows:
        total = int(row.get("qualification_score", 0))
        if total >= 70:
            row["qualification_tier"] = "Tier 1"
        elif total >= 50:
            row["qualification_tier"] = "Tier 2"
        elif total >= 30:
            row["qualification_tier"] = "Tier 3"
        else:
            row["qualification_tier"] = "Tier 4"

    rows.sort(key=lambda r: int(r.get("qualification_score", 0)), reverse=True)

    # Save
    output_file = os.path.join(OUTPUT_DIR, f"qualified_brands_{TODAY}.csv")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=QUALIFIED_COLS, quoting=csv.QUOTE_ALL, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n[3] Saved: {output_file}")

    # Clean up checkpoint
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)
        print(f"    Checkpoint file removed (run completed)")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Input              : {input_file}")
    print(f"Total rows         : {len(rows)}")
    print(f"Enriched (phase 2) : {len(web_only)}")
    print(f"Already full       : {len(already_full)}")

    n_tier1 = sum(1 for r in rows if r.get("qualification_tier") == "Tier 1")
    n_tier2 = sum(1 for r in rows if r.get("qualification_tier") == "Tier 2")
    n_tier3 = sum(1 for r in rows if r.get("qualification_tier") == "Tier 3")
    n_tier4 = sum(1 for r in rows if r.get("qualification_tier") == "Tier 4")
    print(f"\nTier breakdown (all rows):")
    print(f"  Tier 1 (>=70)    : {n_tier1}")
    print(f"  Tier 2 (50-69)   : {n_tier2}")
    print(f"  Tier 3 (30-49)   : {n_tier3}")
    print(f"  Tier 4 (<30)     : {n_tier4}")

    print(f"\nNewly enriched brands (sorted by score):")
    enriched = sorted(web_only, key=lambda r: int(r.get("qualification_score", 0)), reverse=True)
    for j, row in enumerate(enriched[:20], start=1):
        print(
            f"  {j:>2}. {row['business_name'][:38]:<38} "
            f"score={row['qualification_score']:>3}  "
            f"{row.get('qualification_tier', '')}  "
            f"pd={row['product_dev_score']} dm={row['data_maturity_score']} bm={row['brand_maturity_score']}"
        )
        if row.get("product_dev_evidence") and row["product_dev_evidence"] != "No product dev signals found":
            print(f"      pd: {row['product_dev_evidence'][:90]}")
        if row.get("data_evidence") and row["data_evidence"] != "No data maturity signals found":
            print(f"      dm: {row['data_evidence'][:90]}")
    if len(enriched) > 20:
        print(f"  … and {len(enriched) - 20} more")

    print(f"\nOutput: {output_file}")
    print("=" * 60)


def _run_apify_pass2(brand_rows: list, token: str):
    """Run Apify Google Search enrichment on a list of brand rows."""
    print(f"\n  Pass 2 — Apify Google Search enrichment ({len(brand_rows)} brands)…")
    for idx, row in enumerate(brand_rows, start=1):
        name = row.get("business_name", "")
        print(f"    [{idx}/{len(brand_rows)}] Apify scoring: {name}", flush=True)

        pd_apify, pd_apify_ev = score_product_development_apify(name, token)
        dm_apify, dm_apify_ev = score_data_maturity_apify(name, token)
        bm_apify, bm_apify_ev = score_brand_maturity_apify(name, token)

        row["product_dev_score"] = min(int(row["product_dev_score"]) + pd_apify, 50)
        row["data_maturity_score"] = min(int(row["data_maturity_score"]) + dm_apify, 30)
        row["brand_maturity_score"] = min(int(row["brand_maturity_score"]) + bm_apify, 20)
        row["qualification_score"] = (
            int(row["product_dev_score"]) +
            int(row["data_maturity_score"]) +
            int(row["brand_maturity_score"])
        )

        if pd_apify_ev:
            existing = row.get("product_dev_evidence", "")
            if existing and existing != "No product dev signals found":
                row["product_dev_evidence"] = existing + " | " + " | ".join(pd_apify_ev)
            else:
                row["product_dev_evidence"] = " | ".join(pd_apify_ev)
        if dm_apify_ev:
            existing = row.get("data_evidence", "")
            if existing and existing != "No data maturity signals found":
                row["data_evidence"] = existing + " | " + " | ".join(dm_apify_ev)
            else:
                row["data_evidence"] = " | ".join(dm_apify_ev)
        row["scoring_depth"] = "full"

        print(f"      final score={row['qualification_score']} "
              f"(pd={row['product_dev_score']} dm={row['data_maturity_score']} bm={row['brand_maturity_score']})",
              flush=True)


def _save_and_summarize(all_rows, input_file, output_file, n_prev_scored, unscored, brand_rows):
    """Save output CSV and print summary."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=QUALIFIED_COLS, quoting=csv.QUOTE_ALL, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"\n[4] Saved: {output_file}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Input              : {input_file}")
    print(f"Total rows         : {len(all_rows)}")
    print(f"Previously scored  : {n_prev_scored}")
    print(f"Newly processed    : {len(unscored)}")
    print(f"  Brands scored    : {len(brand_rows)}")

    n_tier1 = sum(1 for r in all_rows if r.get("qualification_tier") == "Tier 1")
    n_tier2 = sum(1 for r in all_rows if r.get("qualification_tier") == "Tier 2")
    n_tier3 = sum(1 for r in all_rows if r.get("qualification_tier") == "Tier 3")
    n_tier4 = sum(1 for r in all_rows if r.get("qualification_tier") == "Tier 4")
    print(f"\nTier breakdown (all rows):")
    print(f"  Tier 1 (>=70)    : {n_tier1}")
    print(f"  Tier 2 (50-69)   : {n_tier2}")
    print(f"  Tier 3 (30-49)   : {n_tier3}")
    print(f"  Tier 4 (<30)     : {n_tier4}")

    print(f"\nNewly scored brands:")
    newly_scored = sorted(
        [r for r in unscored if r.get("qualification_score")],
        key=lambda r: int(r.get("qualification_score", 0)),
        reverse=True,
    )
    for j, row in enumerate(newly_scored, start=1):
        print(
            f"  {j:>2}. {row['business_name'][:38]:<38} "
            f"score={row['qualification_score']:>3}  "
            f"{row.get('qualification_tier', '')}  "
            f"pd={row['product_dev_score']} dm={row['data_maturity_score']} bm={row['brand_maturity_score']}"
        )
        if row.get("product_dev_evidence") and row["product_dev_evidence"] != "No product dev signals found":
            print(f"      pd: {row['product_dev_evidence'][:90]}")
        if row.get("data_evidence") and row["data_evidence"] != "No data maturity signals found":
            print(f"      dm: {row['data_evidence'][:90]}")

    print(f"\nOutput: {output_file}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agent 03 Qualification Filter (Apify)")
    parser.add_argument("--input", required=True, help="Path to input CSV")
    parser.add_argument("--phase2-only", action="store_true",
                        help="Re-run Phase 2 Apify scoring on website_only rows (skip classification)")
    args = parser.parse_args()
    if args.phase2_only:
        main_phase2_only(args.input)
    else:
        main(args.input)
