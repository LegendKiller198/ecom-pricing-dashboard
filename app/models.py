from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db import Base


class Platform(Base):
    __tablename__ = "platforms"
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)

    snapshots = relationship("PriceSnapshot", back_populates="platform")


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    brand = Column(String(128))
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    category = relationship("Category", back_populates="products")
    snapshots = relationship("PriceSnapshot", back_populates="product")

    __table_args__ = (UniqueConstraint("name", "brand", name="uq_product_name_brand"),)


class PriceSnapshot(Base):
    """One observed price point for a product on a platform at a point in time."""
    __tablename__ = "price_snapshots"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)

    mrp = Column(Float, nullable=False)
    selling_price = Column(Float, nullable=False)
    rating = Column(Float)
    num_reviews = Column(Integer)
    stock_status = Column(String(32))

    source = Column(String(255))          # URL or "verified-manual" / "synthetic-seed"
    is_verified_real = Column(Boolean, default=False)  # hand-verified real listing vs synthetic/scraped
    observed_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="snapshots")
    platform = relationship("Platform", back_populates="snapshots")

    @property
    def discount_pct(self):
        if not self.mrp:
            return 0.0
        return max(0.0, (self.mrp - self.selling_price) / self.mrp)


class PipelineRun(Base):
    """Audit log of every pipeline execution, per source."""
    __tablename__ = "pipeline_runs"
    id = Column(Integer, primary_key=True)
    source = Column(String(64), nullable=False)
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime, nullable=False)
    rows_ingested = Column(Integer, default=0)
    rows_failed = Column(Integer, default=0)
    status = Column(String(16), default="success")  # success | partial | failed
    error_message = Column(String(1024), nullable=True)
