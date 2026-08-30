import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "ecom.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# How often the scheduled pipeline job runs, in minutes.
# For a scraper hitting real sites, don't go below ~60 minutes per source —
# frequent polling is what gets IPs blocked and is inconsiderate to the target site.
PIPELINE_INTERVAL_MINUTES = int(os.environ.get("PIPELINE_INTERVAL_MINUTES", 60))

# Per-request delay for any real HTTP scraper, in seconds. Keep this polite.
SCRAPER_REQUEST_DELAY_SECONDS = float(os.environ.get("SCRAPER_REQUEST_DELAY_SECONDS", 2.0))

USER_AGENT = "EcomAnalyticsBot/1.0 (+contact: you@example.com)"
