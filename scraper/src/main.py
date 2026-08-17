import sys
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/faizan102418/FlyRank-AI-Internship)"
TIMEOUT = 10  # seconds
CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
START_URL = "https://books.toscrape.com/catalogue/page-1.html"


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

    if response.status_code != 200:
        raise RuntimeError(f"Fetch failed for {url}: status {response.status_code}")

    html = response.text
    cache_path.write_text(html, encoding="utf-8")
    print(f"FETCH {url} ({len(html)} bytes)")
    return html


MAX_CATALOGUE_PAGES = 3

def discover_catalogue_pages_and_books():
    """Walk the catalogue's own 'next' links for up to 3 pages, collecting absolute book URLs."""
    book_urls = []
    page_num = 1
    url = START_URL

    while url and page_num <= MAX_CATALOGUE_PAGES:
        cache_name = f"catalogue-page-{page_num}.html"
        html = fetch_page(url, cache_name)
        soup = BeautifulSoup(html, "html.parser")

        for article in soup.select("article.product_pod h3 a"):
            href = article.get("href")
            absolute = urljoin(url, href)
            book_urls.append(absolute)

        next_link = soup.select_one("li.next a")
        if next_link and page_num < MAX_CATALOGUE_PAGES:
            url = urljoin(url, next_link.get("href"))
            page_num += 1
        else:
            url = None

    return page_num, book_urls

def main():
    catalogue_pages, book_urls = discover_catalogue_pages_and_books()
    unique_urls = list(dict.fromkeys(book_urls))  # de-dupe, keep order

    print(f"catalogue_pages={catalogue_pages}")
    print(f"discovered={len(book_urls)}")
    print(f"unique_urls={len(unique_urls)}")


if __name__ == "__main__":
    main()