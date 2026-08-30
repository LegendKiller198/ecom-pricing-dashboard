"""
Run once to set up the database and load initial data:

    python3 bootstrap.py

This creates ecom.db, then ingests:
  - the synthetic historical dataset (1,416 rows, 12 weeks) — gives the
    dashboard/API something realistic to show immediately
  - the 5 hand-verified real listings

After this, `python3 -m app.scheduler` (or the scheduler baked into the API
process) keeps the data fresh going forward.
"""

from app.db import Base, engine, SessionLocal
from app.models import PriceSnapshot
from app.pipeline.run_pipeline import run_all
from app.pipeline.synthetic_seed_source import SyntheticSeedSource
from app.pipeline.manual_verified_source import ManualVerifiedSource

if __name__ == "__main__":
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    already_seeded = db.query(PriceSnapshot).count() > 0
    db.close()

    if already_seeded:
        print("Database already has data — skipping seed (safe to redeploy without duplicating rows).")
    else:
        print("Ingesting synthetic seed history...")
        run_all([SyntheticSeedSource()])

        print("Ingesting verified real listings...")
        run_all([ManualVerifiedSource()])

    print("Done. Run `uvicorn app.api.main:app --reload` to start the API.")
