# app/models/metric.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models import Base

class Metric(Base):
    __tablename__ = 'metrics'

    id = Column(Integer, primary_key=True)
    filing_id = Column(Integer, ForeignKey('filings.id', ondelete='CASCADE'), nullable=False)
    metric_name = Column(String, index=True)
    value = Column(Float)
    unit = Column(String)  # e.g., USD
    scale = Column(String)  # e.g., million, billion
    raw_value = Column(String)  # Original value before normalization
    extracted_from = Column(String)  # e.g., 'table', 'text'
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship with filing
    filing = relationship("Filing", back_populates="metrics")

    def __repr__(self):
        return f"<Metric(name='{self.metric_name}', value={self.value}, unit='{self.unit}')>"
