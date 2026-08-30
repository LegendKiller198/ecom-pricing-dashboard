"""
A 'source' that isn't scraped at all — it's a small, hand-verified list of
real prices looked up individually (see README). This is real data with an
audit trail (source URL + retrieval date), useful for spot-checking that the
rest of the pipeline's numbers are directionally realistic.
"""

from typing import List
from app.pipeline.base_scraper import BaseSource, ScrapedListing


class ManualVerifiedSource(BaseSource):
    name = "manual-verified"

    _LISTINGS = [
        ("boAt Airdopes 141 (42Hr Playback TWS)", "boAt", "Electronics", "Amazon.in",
         4490, 899, 4.3, "https://dealsmagnet.com (retrieved 2025-08-19)"),
        ("boAt Airdopes 141 Gen 2 (4-Mic ENx)", "boAt", "Electronics", "Amazon.in",
         3990, 799, 4.2, "https://dealsmagnet.com (retrieved 2026-01-04)"),
        ("Mi 20000mAh 22.5W Power Bank", "Mi (Xiaomi)", "Electronics", "Flipkart",
         4999, 1899, 4.4, "https://pricehistory.app (retrieved 2026-06-19)"),
        ("Noise ColorFit Pro 2 Smartwatch", "Noise", "Electronics", "Flipkart",
         4999, 1299, 4.0, "Flipkart listing + Smartprix history (retrieved 2026-04-01)"),
        ("Puma Softride Enzo Evo Running Shoe", "Puma", "Footwear", "Amazon.in",
         4549, 1949, 4.1, "https://www.amazon.in (Puma store page, retrieved 2026-08-01)"),
    ]

    def fetch(self) -> List[ScrapedListing]:
        return [
            ScrapedListing(
                product_name=n, brand=b, category=c, platform=p,
                mrp=mrp, selling_price=sp, rating=r,
                source_url=src, is_verified_real=True,
            )
            for (n, b, c, p, mrp, sp, r, src) in self._LISTINGS
        ]
