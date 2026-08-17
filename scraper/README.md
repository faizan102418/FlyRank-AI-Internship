# Scraper - FlyRank Internship A9: The Polite Scraper

## Target classification
- **Site:** https://books.toscrape.com
- **Why:** confirmed at toscrape.com as an official sandbox built for practising scraping.
- **Scope:** first 3 catalogue pages only (~60 book detail pages).
- **Data collected:** title, price, availability, rating, description, product URL.
- **robots.txt result:** requested https://books.toscrape.com/robots.txt - got HTTP 404 Not Found (nginx). No robots file found. This is not the same as permission; it's simply an absent file. toscrape.com's own about page is treated as the real permission, since that's the explicit purpose of the sandbox.

I will not reuse this code on another site without checking its rules and terms first.

## How to run
Requires Python 3.10+ and uv (https://docs.astral.sh/uv/).

```powershell
cd scraper
uv run python src/main.py
```

Add --inject-fake-url to test failure handling (adds one deliberately broken book URL and proves the run survives it):

```powershell
uv run python src/main.py --inject-fake-url
```

Output lands in output/books.json, output/errors.json, and output/run-report.json.

## Record schema
Each record in books.json:

| Field | Type | Notes |
|---|---|---|
| title | string | |
| product_url | string | absolute URL, canonical identity of the record |
| price_gbp | float | parsed from price_text, e.g. 51.77 |
| price_text | string | original raw text, e.g. "51.77 GBP symbol" |
| availability_text | string | raw stock text |
| rating_text | string or null | e.g. "Three" |
| description | string or null | null when the page has none - never invented |
| source_page | string | absolute URL of the catalogue page the book was discovered on |
| fetched_at | string | ISO 8601 UTC timestamp |

## Politeness rules
- User-agent: FlyRankInternshipA9/1.0 (+https://github.com/faizan102418/FlyRank-AI-Internship) on every real request
- Timeout: 10 seconds per request
- Delay: 0.5s minimum between real requests (cache hits never wait)
- Cache: every fetched page is saved to cache/; reruns during development read from disk, not the network
- Retry: one retry on timeout or 5xx, with a 1s wait; 404 and 403 are never retried

## Run report proof
```json
{
  "start_time": "2026-08-17T07:09:30.505659+00:00",
  "duration_seconds": 1.31,
  "catalogue_pages": 3,
  "pages_fetched": 0,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0,
  "failed_page_details": []
}
```

## Why no browser was needed
The book data is already present in the server-rendered HTML - view-source shows title, price, and description directly, with no client-side JavaScript required to populate them. A headless browser (e.g. Playwright) would add real cost (a full browser process, more memory, more time per page) for no benefit here, since there's nothing hidden behind JS rendering to wait for.

## Known limitation
The description for at least one book (A Light in the Attic) contains duplicated text in the source HTML itself - the paragraph runs twice, verbatim, cutting off mid-word the first time. This was confirmed by inspecting the raw cached HTML directly. Per the "trust nothing you scraped, never invent text" rule, this was stored as-is rather than silently cleaned or de-duplicated.

## Ethics note
This scraper only touches a site explicitly built for scraping practice. In general: prefer an official API when one exists, never bypass logins, paywalls, or explicit blocks, and only collect the data actually needed for the task.
