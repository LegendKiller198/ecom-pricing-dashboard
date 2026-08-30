"""
Pluggable scraper/connector interface.

Every data source (a real scraper, an official affiliate API client, a CSV
import, or a mock generator for testing) implements this same interface.
The pipeline orchestrator (pipeline.py) doesn't care which kind it's
talking to — this is what makes it possible to swap a mock source for a
real one without touching the database, API, or scheduler code.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class ScrapedListing:
    """Normalized shape every source must produce, regardless of where the
    raw data came from (HTML scrape, API JSON, CSV row, etc.)."""
    product_name: str
    brand: Optional[str]
    category: str
    platform: str
    mrp: float
    selling_price: float
    rating: Optional[float] = None
    num_reviews: Optional[int] = None
    stock_status: Optional[str] = None
    source_url: Optional[str] = None
    is_verified_real: bool = False
    # When the price was actually observed. Sources backfilling history
    # (like the synthetic seed) MUST set this to the real historical date —
    # otherwise every row gets stamped with ingestion time and any
    # time-series/trend query becomes meaningless. Live scrapers can leave
    # this as None to mean "just now".
    observed_at: Optional[datetime] = None


class BaseSource(ABC):
    """Every connector (scraper, API client, importer) subclasses this."""

    name: str = "base"

    @abstractmethod
    def fetch(self) -> List[ScrapedListing]:
        """Return a batch of freshly-observed listings. Must be side-effect
        free with respect to the database — the pipeline handles persistence."""
        raise NotImplementedError
