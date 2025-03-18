# app/models/filing.py
from pydantic import BaseModel

class Filing(BaseModel):
    ticker: str
    filing_type: str
    filing_date: str
    file_path: str
    full_text: str
