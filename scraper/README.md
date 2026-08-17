# Scraper ? FlyRank Internship A9

## Target classification
- **Site:** https://books.toscrape.com
- **Why:** confirmed at toscrape.com as an official sandbox built for practising scraping.
- **Scope:** first 3 catalogue pages only (~60 book detail pages).
- **Data collected:** title, price, availability, rating, description, product URL.
- **robots.txt result:** requested https://books.toscrape.com/robots.txt ? got HTTP 404 Not Found (nginx). No robots file found. This is not the same as permission; it's simply an absent file. The site's own about page (toscrape.com) is treated as the actual permission for scraping it, since that's the explicit purpose of the sandbox.

I will not reuse this code on another site without checking its rules and terms first.
