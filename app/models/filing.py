# app/models/filing.py
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models import Base

class Filing(Base):
    __tablename__ = 'filings'

    id = Column(Integer, primary_key=True)
    ticker = Column(String, index=True)
    filing_type = Column(String, index=True)
    accession_number = Column(String, unique=True, index=True)
    filing_date = Column(DateTime, index=True)
    file_path = Column(String, unique=True)
    full_text = Column(String)
    processed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with metrics
    metrics = relationship("Metric", back_populates="filing", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Filing(ticker='{self.ticker}', type='{self.filing_type}', date='{self.filing_date}')>"
