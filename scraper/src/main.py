import json
import re
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


def fetch_page(url: str, cache_name: str) -> str:
    """Fetch a page politely, using a cache to avoid repeat requests during development."""
    CACHE_DIR.mkdir(exist_ok=True)
    cache_path = CACHE_DIR / cache_name

    if cache_path.exists():
        html = cache_path.read_text(encoding="utf-8")
        print(f"CACHE HIT {url} ({len(html)} bytes)")
        return html

    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=TIMEOUT)
    response.encoding = "utf-8"  # site serves UTF-8; don't let requests guess wrong

    if response.status_code != 200:
        raise RuntimeError(f"Fetch failed for {url}: status {response.status_code}")

    html = response.text
    cache_path.write_text(html, encoding="utf-8")
    print(f"FETCH {url} ({len(html)} bytes)")
    time.sleep(REQUEST_DELAY)  # be polite — only real requests wait
    return html


def discover_catalogue_pages_and_books():
    """Walk the catalogue's own 'next' links for up to 3 pages.

    Returns (catalogue_pages, book_entries) where book_entries is a list of
    (book_url, source_page) tuples, so every book keeps a record of exactly
    which catalogue page it was discovered on.
    """
    book_entries = []
    page_num = 1
    url = START_URL

    while url and page_num <= MAX_CATALOGUE_PAGES:
        cache_name = f"catalogue-page-{page_num}.html"
        html = fetch_page(url, cache_name)
        soup = BeautifulSoup(html, "html.parser")

        for article in soup.select("article.product_pod h3 a"):
            href = article.get("href")
            absolute = urljoin(url, href)
            book_entries.append((absolute, url))  # remember which page this came from

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
    return list(seen.items())  # list of (book_url, source_page)


def cache_name_for_book(url: str) -> str:
    """Turn a book URL into a safe, unique cache filename."""
    slug = url.rstrip("/").split("/")[-2]  # e.g. 'a-light-in-the-attic_1000'
    return f"book-{slug}.html"


def extract_book_record(book_url: str, source_page: str) -> dict:
    """Fetch one book detail page and pull the 8 raw fields — no cleaning yet."""
    cache_name = cache_name_for_book(book_url)
    html = fetch_page(book_url, cache_name)
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


class BookRecord(BaseModel):
    """The finished, validated shape of a book record."""
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
    """Turn '£51.77' into 51.77. Raises ValueError if no number is found."""
    match = re.search(r"[\d.]+", price_text)
    if not match:
        raise ValueError(f"Could not parse a price from: {price_text!r}")
    return float(match.group())


def normalize_and_validate(raw_record: dict) -> tuple[dict | None, dict | None]:
    """Returns (valid_record_dict, None) on success, or (None, error_dict) on failure."""
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
    catalogue_pages, book_entries = discover_catalogue_pages_and_books()
    unique_entries = dedupe_book_entries(book_entries)

    print(f"catalogue_pages={catalogue_pages}")
    print(f"discovered={len(book_entries)}")
    print(f"unique_urls={len(unique_entries)}")

    raw_records = []
    for book_url, source_page in unique_entries:
        raw_records.append(extract_book_record(book_url, source_page))

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

    print(f"valid_records={len(valid_records)}")
    print(f"invalid_records={len(errors)}")


if __name__ == "__main__":
    main()