from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ListingOut(BaseModel):
    id: int
    product: str
    brand: Optional[str] = None
    category: str
    platform: str
    mrp: float
    selling_price: float
    discount_pct: float
    rating: Optional[float] = None
    is_verified_real: bool
    observed_at: datetime
    source: Optional[str] = None

    class Config:
        from_attributes = True


class PlatformSummaryOut(BaseModel):
    platform: str
    listings: int
    avg_mrp: float
    avg_selling_price: float
    avg_discount_pct: float
    avg_rating: Optional[float] = None


class CategorySummaryOut(BaseModel):
    category: str
    listings: int
    avg_mrp: float
    avg_selling_price: float
    avg_discount_pct: float
    avg_rating: Optional[float] = None


class WeeklyTrendOut(BaseModel):
    week: str
    avg_discount_pct: float
    listings: int


class PipelineRunOut(BaseModel):
    started_at: datetime
    finished_at: datetime
    source: str
    rows_ingested: int
    rows_failed: int
    status: str
