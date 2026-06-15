---
name: qualification-filter-v02
description: >
  Use this skill when the user asks to qualify, score, or filter leads using
  Apify Google Search. Triggers include requests to classify brands, score
  leads by product development capability, data maturity, and brand maturity,
  or run Phase 2 enrichment on website-only scored rows.
  Input: any CSV with at least `lead_id`, `business_name`, `type`, `website`.
  Search engine: Apify Google Search Scraper (requires APIFY_API_TOKEN in .env).
argument-hint: "[--input <path>] [--phase2-only]"
---

# Qualification Filter v02 — Agent 03 (Apify)

You are Agent 3: Qualification Filter v02. Your job is to take a lead list,
**classify businesses** that sell proprietary products as `brand`, and
**score brands across 3 dimensions** using Apify Google Search Scraper.

This version replaces DuckDuckGo with **Apify Google Search** for faster,
more reliable results with no rate-limiting issues.

You do NOT scrape new leads — that is Agent 01's job.
You do NOT clean or deduplicate — that is Agent 02's job.

---

## Prerequisites

- `APIFY_API_TOKEN` must be set in `.env` at the project root
- Python 3.10+ (no pip dependencies — uses only stdlib + Apify REST API)

---

## Two operating modes

### Mode 1 — Full run (default)

Processes **unscored rows** (rows where `qualification_score` is empty).
Already-scored rows are kept as-is and merged into the output.

```bash
python3 .claude/skills/qualification-filter-v02/scripts/qualify_leads_apify.py \
  --input <path-to-input.csv>
```

**What it does:**
1. **Phase 1b** — Fetches each website, classifies as `brand` / `salon` / `barber` / `retailer` / `unknown`
2. **Phase 2 Pass 1** — Scores brands using website-only signals
3. **Phase 2 Pass 2** — Enriches scores using Apify Google Search (LinkedIn roles, job listings, retailer presence, press, team size)
4. **Merge** — Combines scored + newly scored rows, sorts by score desc
5. **Save** — Writes `agent3_qualification_filter/qualified_brands_YYYY-MM-DD.csv`

### Mode 2 — Phase 2 only

Re-scores rows that have `scoring_depth=website_only` using Apify Google Search,
without re-running classification. Useful when you have an existing enriched CSV
where some brands were only website-scored (e.g., from a DuckDuckGo v3 run).

```bash
python3 .claude/skills/qualification-filter-v02/scripts/qualify_leads_apify.py \
  --input <path-to-input.csv> --phase2-only
```

**What it does:**
1. Finds all rows with `scoring_depth=website_only` and `type=brand`
2. Runs Apify Google Search scoring on each (5 queries per brand)
3. Adds search scores on top of existing website scores (capped at dimension max)
4. Re-assigns qualification tiers for all rows
5. Saves with checkpoint support (resumes if interrupted)

---

## Step 1 — Discover the input file

The user provides the input file via `--input`. If not provided, prompt for it.

**Accepted input formats:**
- Agent 02 output: `agent2_data_preparation/prepared_leads_*.csv`
- Agent 03 v1/v3 output: `agent3_qualification_filter/qualified_brands_*.csv`
- Any CSV with at minimum: `lead_id`, `business_name`, `type`, `website`

---

## Step 2 — Run the script

The script lives at `.claude/skills/qualification-filter-v02/scripts/qualify_leads_apify.py`.

Copy it to the working directory if needed, then run:

```bash
python3 .claude/skills/qualification-filter-v02/scripts/qualify_leads_apify.py \
  --input <input_file.csv>
```

Or for Phase 2 only:

```bash
python3 .claude/skills/qualification-filter-v02/scripts/qualify_leads_apify.py \
  --input <input_file.csv> --phase2-only
```

**Expected Apify usage per brand:** 5 Google Search queries across 3 scoring dimensions.

**Typical runtime & cost:**
- Full run (15 brands): ~20 minutes, ~$0.70 Apify
- Phase 2 only (78 brands): ~2 hours, ~$3.50 Apify
- ~$0.045 per brand (5 queries each)
- Checkpoint file saves progress after each brand — safe to interrupt and resume

---

## Script specification

### Search engine: Apify Google Search Scraper

- Actor: `apify~google-search-scraper`
- API: REST via `https://api.apify.com/v2`
- Auth: `APIFY_API_TOKEN` from `.env` or environment
- Sync run first (2 min timeout), falls back to async polling
- Returns `organicResults` with title, url, description per query

### Skip domain categories

- **Social:** Instagram, Facebook, TikTok, LinkedIn, Twitter/X, YouTube, Pinterest, Threads
- **Retailers:** Amazon, Etsy, Boots, Superdrug, Sephora, Ulta, Target, Walmart, etc.
- **Coupons:** Knoji, Dealspotr, Honey, RetailMeNot, Groupon, Wethrift, etc.
- **Directories:** Google, Yelp, BBB, Wikipedia, Crunchbase, Trustpilot
- **Booking:** Booksy, Fresha, Vagaro, Schedulicity, StyleSeat, Treatwell
- **Junk:** DuckDuckGo redirects, Google Play, Apple App Store

### Phase 1b — Brand classification (website fetch)

For each row with a website, fetches the homepage HTML and looks for:

**Proprietary product signals** → classify as `brand`:
- URL paths: `/products`, `/collections`, `/shop`, `/our-products`, `/store`
- Text: "our formula", "we formulate", "handmade by us", "small batch", etc.
- Marks: ™, ®, "trade mark", "registered mark"
- Brand name alongside product page links
- Founding story: "our story", "founder", "founded by", etc.

**Third-party reseller signals** → classify as `retailer`:
- "we stock", "we carry", "brands we love", "featured brands", "shop by brand"

**Service signals** → keep as `salon` / `barber`:
- "book appointment", "our services", "price list", "walk-ins", "stylist"
- Requires ≥ 2 salon signals AND zero own-product signals

**Decision tree:**
1. Salon signals ≥ 2 and no own products → `salon` / `barber`
2. Own product signals > 0 → `brand`
3. Has product pages + no reseller signals + ≥ 2 signals → `brand`
4. Reseller signals > 0 and no own products → `retailer`
5. Has product pages → `brand`
6. Existing type is `salon`/`barber` → preserve
7. Else → `unknown`

### Phase 2 — Brand scoring (0–100, 3 dimensions)

Only rows where `type = brand` are scored. Two-pass approach:

#### Pass 1 — Website-only scoring (no API calls)

Fetches each brand's website once (cached) and checks for signals.

#### Pass 2 — Apify Google Search enrichment

Runs 5 Google Search queries per brand via Apify.

#### Dimension 1 — Product Development Capability (0–50)

| Signal | Points | Source |
|---|---|---|
| R&D/lab/formulation process on website | +8 | Website HTML |
| Science-backed/clinically tested claims | +7 | Website HTML |
| Senior R&D role on LinkedIn (Director+) | +25 | Apify: `"{name}" (formulation OR chemist OR "R&D") site:linkedin.com` |
| Junior formulation/R&D role on LinkedIn | +15 | Same query, junior titles |
| Job listings for product dev/formulation | +10 | Apify: `"{name}" (formulation OR "product development") (jobs OR careers)` |

#### Dimension 2 — Data Maturity (0–30)

| Signal | Points | Source |
|---|---|---|
| Hair quiz / personalisation tool | +8 | Website HTML |
| Reviews / ratings system | +5 | Website HTML |
| Marketing tech stack (Klaviyo, GA, etc.) | +4 | Website HTML |
| Data/analytics/CRM roles on LinkedIn | +10 | Apify: `"{name}" ("data analyst" OR "CRM manager") site:linkedin.com` |
| Public data/analytics mentions | +3 | Apify: `"{name}" (data OR analytics OR insights)` |

#### Dimension 3 — Brand Maturity (0–20)

| Signal | Points | Source |
|---|---|---|
| 2+ social platforms active | +4 | CSV fields |
| Founded 2+ years ago | +2 | Website HTML |
| Stockists/where-to-buy page | +3 | Website HTML |
| Stocked in major retailers | +6 | Apify: `"{name}" (Boots OR Sephora OR Target)` |
| Press coverage / awards | +5 | Apify: `"{name}" (award OR "featured in")` |
| LinkedIn team size > 10 | +3 | Apify: `"{name}" site:linkedin.com/company` |

#### Qualification tiers

| Tier | Score | Meaning |
|---|---|---|
| **Tier 1** | ≥ 70 | Has product dev team AND data capabilities. **Top priority.** |
| **Tier 2** | 50–69 | Has product dev OR data signals, not both. High potential. |
| **Tier 3** | 30–49 | Brand owner but limited R&D/data signals. Worth reaching out. |
| **Tier 4** | < 30 | Weak signals. Likely too small or early-stage. |

---

## Step 3 — Handle errors

| Situation | Action |
|---|---|
| `APIFY_API_TOKEN` not found | Stop. Tell user to add it to `.env`. |
| Apify sync run times out | Automatic fallback to async polling. |
| Apify run FAILED/ABORTED | Raise error, checkpoint preserves progress. |
| Website fetch returns 403/429 | Row skipped for classification. `brand_signals` left empty. |
| Apify returns no results for a query | Score 0 for that signal — do NOT fabricate evidence. |
| Script interrupted mid-run | Resume with same command — checkpoint file auto-detected. |
| Input CSV has encoding issues | Script tries `latin-1` fallback for full runs, `utf-8` for phase2-only. |

---

## Step 4 — Confirm output to user

```
Qualification filter complete.

Script        : .claude/skills/qualification-filter-v02/scripts/qualify_leads_apify.py
Output        : agent3_qualification_filter/qualified_brands_YYYY-MM-DD.csv

[paste SUMMARY block from script output]

Next step: pass qualified_brands_YYYY-MM-DD.csv to Agent 04 (Outreach Composer).
```

---

## Constraints

- ALWAYS use the script from `.claude/skills/qualification-filter-v02/scripts/`.
- ALWAYS save output to `agent3_qualification_filter/`.
- Do NOT classify as `brand` without evidence of proprietary products on the website.
- Do NOT fabricate evidence. If no signals are found, score 0 for that dimension.
- ALWAYS preserve already-scored rows when running in full mode.
- Phase 2 only mode ALWAYS uses checkpoint files — safe to interrupt.
- Scoring depth is tracked: `website_only` (Pass 1 only) or `full` (Pass 1 + Pass 2).

---

## Output contract (for downstream agents)

### `qualified_brands_YYYY-MM-DD.csv`

| Column | Description |
|---|---|
| `lead_id` | Carried over from input |
| `business_name` | Unchanged |
| `type` | `brand` / `salon` / `barber` / `retailer` / `unknown` |
| `website` | Official website URL (or `""` if not found) |
| `website_status` | `confirmed` / `updated` / `not_found` |
| `website_previous` | Original URL before enrichment (audit trail) |
| `brand_signals` | Comma-separated signals found on the website |
| `search_name` | Extracted brand name used for search (audit) |
| `qualification_score` | Total 0–100 |
| `product_dev_score` | Sub-score 0–50 |
| `data_maturity_score` | Sub-score 0–30 |
| `brand_maturity_score` | Sub-score 0–20 |
| `product_dev_evidence` | Plain-text: what product dev signals were found |
| `data_evidence` | Plain-text: what data maturity signals were found |
| `qualification_tier` | `Tier 1` / `Tier 2` / `Tier 3` / `Tier 4` |
| `scoring_depth` | `website_only` or `full` |

File is sorted by `qualification_score` descending.

---

## Examples

### Example 1 — Full run on new leads

**User says:** "Qualify these new leads using Apify"

**Agent does:**
```bash
python3 .claude/skills/qualification-filter-v02/scripts/qualify_leads_apify.py \
  --input agent3_qualification_filter/qualified_brands_2026-03-10_manually_test1.csv
```

1. Finds 15 unscored rows, 95 already scored.
2. Phase 1b: Classifies all 15 as `brand`.
3. Phase 2 Pass 1: Website-only scores range 0–28.
4. Phase 2 Pass 2: Apify enrichment bumps scores to 25–79.
5. Merges all 110 rows, saves `qualified_brands_2026-03-10.csv`.

### Example 2 — Phase 2 only on website-only brands

**User says:** "Run Phase 2 on the 78 website-only brands"

**Agent does:**
```bash
python3 .claude/skills/qualification-filter-v02/scripts/qualify_leads_apify.py \
  --input agent3_qualification_filter/qualified_brands_2026-03-10.csv --phase2-only
```

1. Finds 78 `website_only` brands, skips 32 already `full`.
2. Runs 5 Apify queries per brand (390 total).
3. Saves checkpoint after each brand.
4. Final result: 28 Tier 1, 42 Tier 2, 27 Tier 3, 13 Tier 4.

**Tier 1 example (score 86):**
- Briogeo Hair Care — senior R&D role on LinkedIn, science-backed claims on website,
  hair quiz, reviews system, Klaviyo detected, press coverage.
- product_dev_score: 42, data_maturity_score: 30, brand_maturity_score: 14
