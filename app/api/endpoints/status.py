from typing import Dict, List
from fastapi import APIRouter, HTTPException
from app.services.sql_storage import SQLStorage
from app.core.config import TICKERS, FILING_TYPES

router = APIRouter()

@router.get("/api/filing-status")
async def get_filing_status() -> Dict:
    """Get status of filings for all companies."""
    storage = SQLStorage()
    status = {}
    
    try:
        for ticker in TICKERS:
            ticker_stats = {
                'ticker': ticker,
                'filing_counts': {},
                'latest_filing_dates': {},
                'total_filings': 0,
                'download_stats': None,  # Will be populated from the scheduler
                'processing_stats': None  # Will be populated from the pipeline
            }
            
            for filing_type in FILING_TYPES:
                with storage.session_scope() as session:
                    # Get total count for this ticker and type
                    count = session.query(storage.Filing).filter(
                        storage.Filing.ticker == ticker,
                        storage.Filing.filing_type == filing_type
                    ).count()
                    
                    # Get latest filing date
                    latest = session.query(storage.Filing).filter(
                        storage.Filing.ticker == ticker,
                        storage.Filing.filing_type == filing_type
                    ).order_by(storage.Filing.filing_date.desc()).first()
                    
                    ticker_stats['filing_counts'][filing_type] = count
                    ticker_stats['latest_filing_dates'][filing_type] = latest.filing_date.strftime('%Y-%m-%d') if latest else None
                    ticker_stats['total_filings'] += count
            
            # Add downloader stats if available
            from app.services.scheduler import filing_scheduler
            if filing_scheduler and filing_scheduler.scanner and filing_scheduler.scanner.downloader:
                download_stats = filing_scheduler.scanner.downloader.get_download_stats()
                ticker_stats['download_stats'] = download_stats.get(ticker)
            
            # Add processing stats if available
            if filing_scheduler and filing_scheduler.processing_pipeline:
                processing_stats = filing_scheduler.processing_pipeline.processing_stats
                ticker_stats['processing_stats'] = processing_stats.get(ticker)
            
            status[ticker] = ticker_stats
        
        return {
            'status': 'success',
            'data': status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
