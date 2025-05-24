# app/services/streamlit/metrics.py
import os
import pandas as pd
from app.services.sql_storage import SQLStorage
from app.utils.logger import setup_logger
from datetime import datetime

logger = setup_logger(__name__)

class MetricsService:
    def __init__(self):
        """Initialize the metrics service for retrieving financial data from SQLite."""
        self.sql_storage = SQLStorage()
        logger.info("MetricsService initialized successfully.")
    
    def reload(self):
        """Reload the database connection to pick up new data."""
        self.sql_storage = SQLStorage()
        logger.info("MetricsService reloaded.")

    def format_value(self, value: str) -> str:
        """Format numeric values for display."""
        if not value:
            return "N/A"
            
        try:
            value = float(value)
            # Format large numbers with commas and 2 decimal places
            if abs(value) >= 1_000_000_000:  # Billions
                return f"${value/1_000_000_000:.2f}B"
            elif abs(value) >= 1_000_000:  # Millions
                return f"${value/1_000_000:.2f}M"
            else:
                return f"${value:,.2f}"
        except (ValueError, TypeError):
            return str(value)

    def get_filing_metrics(self, ticker: str, filing_type: str, filing_id: str) -> dict:
        """Get metrics for a specific filing.
        
        Args:
            ticker: The stock ticker symbol
            filing_type: The type of filing (10-K, 10-Q, etc.)
            filing_id: The SEC accession number or filing date
            
        Returns:
            dict: Financial metrics for the filing
        """
        try:
            cursor = self.sql_storage.conn.cursor()
            
            # First try to find the filing record with better matching
            cursor.execute("""
                SELECT 
                    f.id, 
                    f.filing_date, 
                    f.processing_status,
                    f.filing_id
                FROM filings f
                WHERE f.ticker = ? 
                AND f.filing_type = ? 
                AND (f.filing_id = ? OR f.filing_date = ? OR f.id = ?)
            """, (ticker, filing_type, filing_id, filing_id, filing_id))
            
            filing = cursor.fetchone()
            if not filing:
                logger.warning(f"No filing found for {ticker} {filing_type} {filing_id}")
                return {}
            
            filing_db_id, filing_date, status, actual_filing_id = filing
            logger.debug(f"Found filing record: id={filing_db_id}, filing_id={actual_filing_id}")
            
            # Then get the metrics with COALESCE to handle NULL values
            cursor.execute("""
                SELECT 
                    COALESCE(revenue, '') as revenue,
                    COALESCE(net_income, '') as net_income,
                    COALESCE(total_assets, '') as total_assets,
                    COALESCE(total_liabilities, '') as total_liabilities,
                    COALESCE(shareholders_equity, '') as shareholders_equity,
                    created_at,
                    updated_at
                FROM metrics 
                WHERE filing_id = ?
            """, (filing_db_id,))
            
            metrics = cursor.fetchone()
            if not metrics:
                logger.warning(f"No metrics found for filing ID {filing_id} (db_id={filing_db_id})")
                return {}
                
            # Convert to dictionary with metadata and formatted values
            metrics_dict = {
                "revenue": self.format_value(metrics[0]),
                "net_income": self.format_value(metrics[1]),
                "total_assets": self.format_value(metrics[2]),
                "total_liabilities": self.format_value(metrics[3]),
                "shareholders_equity": self.format_value(metrics[4]),
                "filing_type": filing_type,
                "filing_date": filing_date,
                "metrics_created": metrics[5],
                "metrics_updated": metrics[6],
                "processing_status": status
            }
            
            # Log actual metric values for debugging
            logger.debug(f"Raw metrics for {ticker} {filing_type} {filing_id}: {metrics}")
            logger.info(f"Retrieved metrics for {ticker} {filing_type} {filing_id}")
            return metrics_dict
            
        except Exception as e:
            logger.error(f"Error retrieving metrics: {e}")
            return {}
    
    def get_historical_metrics(self, ticker: str, metric_name: str) -> pd.DataFrame:
        """Get historical metric data for a company.

        Args:
            ticker: The stock ticker symbol
            metric_name: Name of the metric column (e.g., 'revenue', 'net_income')

        Returns:
            pd.DataFrame: DataFrame with filing_date and metric value columns
        """
        try:
            cursor = self.sql_storage.conn.cursor()
            
            # Get historical data for the metric
            cursor.execute(f"""
                SELECT 
                    f.filing_date,
                    COALESCE(m.{metric_name}, '') as value
                FROM filings f
                LEFT JOIN metrics m ON f.id = m.filing_id
                WHERE f.ticker = ?
                    AND m.{metric_name} IS NOT NULL 
                    AND m.{metric_name} != ''
                ORDER BY f.filing_date ASC
            """, (ticker,))
            
            rows = cursor.fetchall()
            
            if not rows:
                logger.warning(f"No historical {metric_name} data found for {ticker}")
                return pd.DataFrame(columns=['filing_date', 'value'])

            df = pd.DataFrame(rows, columns=['filing_date', 'value'])
            
            # Convert filing dates to datetime
            df['filing_date'] = pd.to_datetime(df['filing_date'])
            
            # Clean numeric values
            df['value'] = df['value'].replace('', None)
            df = df.dropna()

            logger.info(f"Retrieved {len(df)} historical {metric_name} records for {ticker}")
            logger.debug(f"Historical data for {ticker} {metric_name}: {df.to_dict()}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving historical {metric_name} data: {e}")
            return pd.DataFrame(columns=['filing_date', 'value'])