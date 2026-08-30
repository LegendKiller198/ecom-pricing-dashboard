"""
Loads the pre-generated synthetic historical dataset (1,416 rows across 12
weeks) so the pipeline and API have realistic history to serve immediately,
without waiting on a live scraper. This is what the dashboard was built from
originally — same interface as any other source, so it's just one more
pluggable connector, not special-cased.
"""

import json
import os
from datetime import datetime
from typing import List

from app.pipeline.base_scraper import BaseSource, ScrapedListing

_SEED_PATH = os.path.join(os.path.dirname(__file__), "seed_synthetic_rows.json")


class SyntheticSeedSource(BaseSource):
    name = "synthetic-seed"

    def fetch(self) -> List[ScrapedListing]:
        with open(_SEED_PATH) as f:
            rows = json.load(f)
        return [
            ScrapedListing(
                product_name=r["Product Name"],
                brand=r["Brand"],
                category=r["Category"],
                platform=r["Platform"],
                mrp=r["MRP"],
                selling_price=r["Selling Price"],
                rating=r["Rating"],
                num_reviews=r["Num Reviews"],
                stock_status=r["Stock Status"],
                source_url="synthetic-seed",
                is_verified_real=False,
                observed_at=datetime.strptime(r["Date"], "%Y-%m-%d"),
            )
            for r in rows
        ]
