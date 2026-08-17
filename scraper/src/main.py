import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, ValidationError, field_validator

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/faizan102418/FlyRank-AI-Internship)"
TIMEOUT = 10  # seconds
CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
START_URL = "https://books.toscrape.com/catalogue/page-1.html"
MAX_CATALOGUE_PAGES = 3
REQUEST_DELAY = 0.5  # seconds, only applies to real requests, not cache hits
RETRY_WAIT = 1.0  # seconds, before a single retry on timeout/5xx

# Statuses that are worth retrying once — transient problems.
# 404/403 are never retried: the page doesn't exist, or the site said no.
NO_RETRY_STATUSES = {404, 403}


class FetchStats:
    """Tracks honest counts across the whole run, for the final report."""
    def __init__(self):
        self.pages_fetched = 0   # real network requests that succeeded
        self.cache_hits = 0
        self.failed_pages = []   # list of {"url": ..., "reason": ...}


def fetch_page(url: str, cache_name: str, stats: FetchStats) -> str | None:
    """Fetch a page politely, with caching, a single retry on timeout/5xx, and
    no retry on 404/403. Returns None (instead of raising) if the page could
    not be fetched, so the caller can skip it and keep the run alive.
    """
    CACHE_DIR.mkdir(exist_ok=True)
    cache_path = CACHE_DIR / cache_name

    if cache_path.exists():
        html = cache_path.read_text(encoding="utf-8")
        print(f"CACHE HIT {url} ({len(html)} bytes)")
        stats.cache_hits += 1
        return html

    headers = {"User-Agent": USER_AGENT}
    attempts = 0
    max_attempts = 2  # one try + one retry

    while attempts < max_attempts:
        attempts += 1
        try:
            response = requests.get(url, headers=headers, timeout=TIMEOUT)
            response.encoding = "utf-8"

            if response.status_code == 200:
                html = response.text
                cache_path.write_text(html, encoding="utf-8")
                print(f"FETCH {url} ({len(html)} bytes)")
                stats.pages_fetched += 1
                time.sleep(REQUEST_DELAY)
                return html

            if response.status_code in NO_RETRY_STATUSES:
                reason = f"HTTP {response.status_code} — not retrying"
                print(f"FAIL {url}: {reason}")
                stats.failed_pages.append({"url": url, "reason": reason})
                return None

            # Any other non-200 (e.g. 5xx) — worth one retry
            if attempts < max_attempts:
                print(f"RETRY {url}: HTTP {response.status_code}, waiting {RETRY_WAIT}s")
                time.sleep(RETRY_WAIT)
                continue

            reason = f"HTTP {response.status_code} after retry"
            print(f"FAIL {url}: {reason}")
            stats.failed_pages.append({"url": url, "reason": reason})
            return None

        except requests.exceptions.Timeout:
            if attempts < max_attempts:
                print(f"RETRY {url}: timeout, waiting {RETRY_WAIT}s")
                time.sleep(RETRY_WAIT)
                continue
            reason = "timeout after retry"
            print(f"FAIL {url}: {reason}")
            stats.failed_pages.append({"url": url, "reason": reason})
            return None

        except requests.exceptions.RequestException as e:
            # Covers DNS failures, connection errors, etc. — not retried,
            # since these usually mean the URL itself is bad.
            reason = f"request error: {e}"
            print(f"FAIL {url}: {reason}")
            stats.failed_pages.append({"url": url, "reason": reason})
            return None

    return None


def discover_catalogue_pages_and_books(stats: FetchStats):
    """Walk the catalogue's own 'next' links for up to 3 pages.

    Returns (catalogue_pages, book_entries) where book_entries is a list of
    (book_url, source_page) tuples.
    """
    book_entries = []
    page_num = 1
    url = START_URL

    while url and page_num <= MAX_CATALOGUE_PAGES:
        cache_name = f"catalogue-page-{page_num}.html"
        html = fetch_page(url, cache_name, stats)
        if html is None:
            # A broken catalogue page stops discovery from that point —
            # but does not crash the whole run.
            break
        soup = BeautifulSoup(html, "html.parser")

        for article in soup.select("article.product_pod h3 a"):
            href = article.get("href")
            absolute = urljoin(url, href)
            book_entries.append((absolute, url))

        next_link = soup.select_one("li.next a")
        if next_link and page_num < MAX_CATALOGUE_PAGES:
            url = urljoin(url, next_link.get("href"))
            page_num += 1
        else:
            url = None

    return page_num, book_entries


def dedupe_book_entries(book_entries):
    """De-dupe by book URL, keeping the first source_page seen for each."""
    seen = {}
    for book_url, source_page in book_entries:
        if book_url not in seen:
            seen[book_url] = source_page
    return list(seen.items())


def cache_name_for_book(url: str) -> str:
    """Turn a book URL into a safe, unique cache filename."""
    slug = url.rstrip("/").split("/")[-2]
    return f"book-{slug}.html"


def extract_book_record(book_url: str, source_page: str, stats: FetchStats) -> dict | None:
    """Fetch one book detail page and pull the 8 raw fields.
    Returns None if the page could not be fetched or parsed — the caller
    treats that as a failed page and moves on.
    """
    cache_name = cache_name_for_book(book_url)
    html = fetch_page(book_url, cache_name, stats)
    if html is None:
        return None

    try:
        soup = BeautifulSoup(html, "html.parser")
        product_main = soup.select_one("div.product_main")
        title = product_main.select_one("h1").get_text(strip=True)
        price_text = product_main.select_one("p.price_color").get_text(strip=True)
        availability_text = product_main.select_one("p.availability").get_text(strip=True)

        rating_tag = product_main.select_one("p.star-rating")
        rating_classes = rating_tag.get("class", [])
        rating_text = next((c for c in rating_classes if c != "star-rating"), None)

        description_tag = soup.select_one("#product_description ~ p")
        description = description_tag.get_text(strip=True) if description_tag else None

        return {
            "title": title,
            "product_url": book_url,
            "price_text": price_text,
            "availability_text": availability_text,
            "rating_text": rating_text,
            "description": description,
            "source_page": source_page,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except AttributeError as e:
        # A page that fetched fine but didn't have the shape we expected —
        # log it as a failed page rather than crashing the run.
        reason = f"could not parse expected fields: {e}"
        print(f"FAIL {book_url}: {reason}")
        stats.failed_pages.append({"url": book_url, "reason": reason})
        return None


class BookRecord(BaseModel):
    title: str
    product_url: str
    price_gbp: float
    price_text: str
    availability_text: str
    rating_text: str | None
    description: str | None
    source_page: str
    fetched_at: str

    @field_validator("product_url", "source_page")
    @classmethod
    def must_be_absolute(cls, v: str) -> str:
        if not v.startswith("https://"):
            raise ValueError(f"URL is not absolute: {v}")
        return v


def parse_price_gbp(price_text: str) -> float:
    match = re.search(r"[\d.]+", price_text)
    if not match:
        raise ValueError(f"Could not parse a price from: {price_text!r}")
    return float(match.group())


def normalize_and_validate(raw_record: dict) -> tuple[dict | None, dict | None]:
    try:
        price_gbp = parse_price_gbp(raw_record["price_text"])
        candidate = {**raw_record, "price_gbp": price_gbp}
        validated = BookRecord(**candidate)
        return validated.model_dump(), None
    except (ValidationError, ValueError, KeyError) as e:
        error = {
            "product_url": raw_record.get("product_url", "unknown"),
            "reason": str(e),
        }
        return None, error


def main():
    start_time = datetime.now(timezone.utc)
    stats = FetchStats()

    catalogue_pages, book_entries = discover_catalogue_pages_and_books(stats)
    unique_entries = dedupe_book_entries(book_entries)

    # Test hook: pass --inject-fake-url to add one deliberately broken URL,
    # proving the run survives a broken page without crashing.
    if "--inject-fake-url" in sys.argv:
        fake_url = "https://books.toscrape.com/catalogue/this-book-does-not-exist_9999/index.html"
        unique_entries.append((fake_url, START_URL))
        print(f"TEST MODE: injected fake URL {fake_url}")

    print(f"catalogue_pages={catalogue_pages}")
    print(f"discovered={len(book_entries)}")
    print(f"unique_urls={len(unique_entries)}")

    raw_records = []
    for book_url, source_page in unique_entries:
        record = extract_book_record(book_url, source_page, stats)
        if record is not None:
            raw_records.append(record)

    print(f"detail_pages={len(raw_records)}")

    valid_records = []
    errors = []
    for raw in raw_records:
        record, error = normalize_and_validate(raw)
        if record:
            valid_records.append(record)
        else:
            errors.append(error)

    OUTPUT_DIR.mkdir(exist_ok=True)

    with open(OUTPUT_DIR / "books.json", "w", encoding="utf-8") as f:
        json.dump(valid_records, f, indent=2, ensure_ascii=False)

    with open(OUTPUT_DIR / "errors.json", "w", encoding="utf-8") as f:
        json.dump(errors, f, indent=2, ensure_ascii=False)

    end_time = datetime.now(timezone.utc)
    duration_seconds = (end_time - start_time).total_seconds()

    run_report = {
        "start_time": start_time.isoformat(),
        "duration_seconds": round(duration_seconds, 2),
        "catalogue_pages": catalogue_pages,
        "pages_fetched": stats.pages_fetched,
        "cache_hits": stats.cache_hits,
        "valid_records": len(valid_records),
        "invalid_records": len(errors),
        "failed_pages": len(stats.failed_pages),
        "failed_page_details": stats.failed_pages,
    }

    with open(OUTPUT_DIR / "run-report.json", "w", encoding="utf-8") as f:
        json.dump(run_report, f, indent=2, ensure_ascii=False)

    print(f"valid_records={len(valid_records)}")
    print(f"invalid_records={len(errors)}")
    print(f"failed_pages={len(stats.failed_pages)}")
    print(f"duration_seconds={run_report['duration_seconds']}")


if __name__ == "__main__":
    main()