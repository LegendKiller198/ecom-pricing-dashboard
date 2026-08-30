"""
Orchestrator: pulls listings from one or more BaseSource connectors,
validates them, and upserts into the database. Every run is logged to
PipelineRun for auditability — useful in an interview to show you thought
about observability, not just "does it work once."
"""

from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Platform, Category, Product, PriceSnapshot, PipelineRun
from app.pipeline.base_scraper import BaseSource, ScrapedListing


def _get_or_create_platform(db: Session, name: str) -> Platform:
    obj = db.query(Platform).filter_by(name=name).first()
    if not obj:
        obj = Platform(name=name)
        db.add(obj)
        db.flush()
    return obj


def _get_or_create_category(db: Session, name: str) -> Category:
    obj = db.query(Category).filter_by(name=name).first()
    if not obj:
        obj = Category(name=name)
        db.add(obj)
        db.flush()
    return obj


def _get_or_create_product(db: Session, name: str, brand: str, category: Category) -> Product:
    obj = db.query(Product).filter_by(name=name, brand=brand).first()
    if not obj:
        obj = Product(name=name, brand=brand, category=category)
        db.add(obj)
        db.flush()
    return obj


def _validate(listing: ScrapedListing) -> bool:
    """Basic sanity checks — reject obviously broken rows rather than
    poisoning the database with them."""
    if listing.mrp <= 0 or listing.selling_price <= 0:
        return False
    if listing.selling_price > listing.mrp * 1.05:
        # selling price shouldn't meaningfully exceed MRP; small slack for rounding
        return False
    if not listing.product_name or not listing.platform or not listing.category:
        return False
    return True


def ingest(db: Session, listings: List[ScrapedListing]) -> tuple[int, int]:
    ingested, failed = 0, 0
    for listing in listings:
        if not _validate(listing):
            failed += 1
            continue
        platform = _get_or_create_platform(db, listing.platform)
        category = _get_or_create_category(db, listing.category)
        product = _get_or_create_product(db, listing.product_name, listing.brand, category)

        snapshot = PriceSnapshot(
            product=product,
            platform=platform,
            mrp=listing.mrp,
            selling_price=listing.selling_price,
            rating=listing.rating,
            num_reviews=listing.num_reviews,
            stock_status=listing.stock_status,
            source=listing.source_url,
            is_verified_real=listing.is_verified_real,
            observed_at=listing.observed_at or datetime.utcnow(),
        )
        db.add(snapshot)
        ingested += 1
    db.commit()
    return ingested, failed


def run_source(source: BaseSource) -> PipelineRun:
    db = SessionLocal()
    started = datetime.utcnow()
    status, error_message = "success", None
    ingested, failed = 0, 0
    try:
        listings = source.fetch()
        ingested, failed = ingest(db, listings)
        if failed and ingested:
            status = "partial"
        elif failed and not ingested:
            status = "failed"
    except Exception as e:
        status = "failed"
        error_message = str(e)
    finished = datetime.utcnow()

    run = PipelineRun(
        source=source.name,
        started_at=started,
        finished_at=finished,
        rows_ingested=ingested,
        rows_failed=failed,
        status=status,
        error_message=error_message,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    db.close()
    print(f"[pipeline] {source.name}: {status} — ingested={ingested} failed={failed}")
    return run


def run_all(sources: List[BaseSource]) -> List[PipelineRun]:
    return [run_source(s) for s in sources]
