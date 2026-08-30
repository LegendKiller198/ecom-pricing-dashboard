"""
Template for a real scraper hitting a live product listing page.

This is structurally complete and would work against a real target — but it
is intentionally NOT wired into the default pipeline run, for two reasons:

1. This sandbox's network is locked to dev domains (PyPI/npm/GitHub) and
   cannot reach e-commerce sites, so it can't be exercised end-to-end here.
2. Scraping Amazon.in / Flipkart directly is against their Terms of Service.
   For a real product, prefer their official affiliate/product APIs:
     - Amazon Product Advertising API (requires Associates account)
     - Flipkart Affiliate API
   Use this template against sites that explicitly allow scraping in their
   robots.txt / ToS, or swap it for an official API client with the same
   BaseSource interface.

To use this for real:
  1. Point BASE_URLS at pages you have the right to fetch.
  2. Update the CSS selectors in `_parse_listing_page` to match that site's
     actual HTML (inspect the page — every site's markup is different).
  3. Run it on a machine with real internet access, not this sandbox.
"""

import time
import urllib.robotparser as robotparser
from typing import List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from app.config import USER_AGENT, SCRAPER_REQUEST_DELAY_SECONDS
from app.pipeline.base_scraper import BaseSource, ScrapedListing


def _robots_allow(url: str, user_agent: str = USER_AGENT) -> bool:
    """Check the target's robots.txt before fetching. If this returns False,
    do not scrape that URL — respect it."""
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = robotparser.RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception:
        # If robots.txt can't be read, fail closed (assume disallowed)
        return False


class HtmlScraperTemplate(BaseSource):
    name = "html-scraper-template"

    def __init__(self, urls: List[str], category: str, platform: str):
        self.urls = urls
        self.category = category
        self.platform = platform
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def fetch(self) -> List[ScrapedListing]:
        results = []
        for url in self.urls:
            if not _robots_allow(url):
                print(f"[skip] robots.txt disallows fetching {url}")
                continue
            listing = self._fetch_one(url)
            if listing:
                results.append(listing)
            time.sleep(SCRAPER_REQUEST_DELAY_SECONDS)  # be polite between requests
        return results

    def _fetch_one(self, url: str) -> Optional[ScrapedListing]:
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[error] fetching {url}: {e}")
            return None
        return self._parse_listing_page(resp.text, url)

    def _parse_listing_page(self, html: str, url: str) -> Optional[ScrapedListing]:
        """
        NOTE: these selectors are placeholders. Every site's HTML is
        different and changes often — inspect the real page (browser dev
        tools) and update these before use.
        """
        soup = BeautifulSoup(html, "html.parser")

        name_el = soup.select_one("[data-testid='product-title'], h1")
        mrp_el = soup.select_one("[data-testid='mrp'], .mrp-price")
        price_el = soup.select_one("[data-testid='selling-price'], .selling-price")
        rating_el = soup.select_one("[data-testid='rating'], .rating-value")

        if not (name_el and price_el):
            print(f"[warn] could not find expected fields on {url} — selectors likely need updating")
            return None

        def _to_float(text):
            return float("".join(ch for ch in text if ch.isdigit() or ch == "."))

        mrp = _to_float(mrp_el.text) if mrp_el else _to_float(price_el.text)
        selling_price = _to_float(price_el.text)
        rating = _to_float(rating_el.text) if rating_el else None

        return ScrapedListing(
            product_name=name_el.text.strip(),
            brand=None,
            category=self.category,
            platform=self.platform,
            mrp=mrp,
            selling_price=selling_price,
            rating=rating,
            source_url=url,
            is_verified_real=False,
        )
