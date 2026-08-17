import sys
from pathlib import Path
import requests

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/faizan102418/FlyRank-AI-Internship)"
TIMEOUT = 10  # seconds
CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"

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


def main():
    url = "https://books.toscrape.com/catalogue/page-1.html"
    fetch_page(url, "catalogue-page-1.html")


if __name__ == "__main__":
    main()