# app/models/metric.py
from pydantic import BaseModel

class Metric(BaseModel):
    filing_id: int
    revenue: str = None
    net_income: str = None
    total_assets: str = None
    total_liabilities: str = None
    shareholders_equity: str = None
