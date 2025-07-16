"""Metrics validation and normalization service."""
from typing import Dict, Any, Optional
from datetime import datetime

class MetricsValidator:
    """Validates and normalizes financial metrics data."""
    
    REQUIRED_METRICS = {
        "revenue", 
        "net_income",
        "total_assets",
        "total_liabilities",
        "shareholders_equity"
    }
    
    @staticmethod
    def validate_and_normalize(metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize metrics data."""
        if not metrics:
            return {}
            
        normalized = {}
          # Convert string values to float where possible
        for key, value in metrics.items():
            if value is None:
                continue
                
            if isinstance(value, str):
                try:
                    # First check if it's already formatted (e.g. "$1.23B")
                    if value.startswith('$'):
                        value = value[1:]  # Remove dollar sign
                    
                    # Handle unit suffixes
                    if value.endswith('B'):
                        multiplier = 1_000_000_000
                        value = value[:-1]
                    elif value.endswith('M'):
                        multiplier = 1_000_000
                        value = value[:-1]
                    else:
                        multiplier = 1
                        
                    # Remove any remaining non-numeric characters except dots and minus signs
                    clean_value = ''.join(c for c in value if c.isdigit() or c in '.-')
                    normalized[key] = float(clean_value) * multiplier
                except ValueError:
                    continue
            elif isinstance(value, (int, float)):
                normalized[key] = float(value)
            else:
                # Skip non-numeric values
                continue
        
        return normalized
    
    @staticmethod
    def validate_filing_metrics(
        metrics: Dict[str, Any],
        filing_type: str,
        filing_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """Validate metrics for a specific filing."""
        if not metrics:
            return {}
            
        # Normalize the metrics first
        normalized = MetricsValidator.validate_and_normalize(metrics)
        
        # Ensure all required metrics have valid values
        for metric in MetricsValidator.REQUIRED_METRICS:
            if metric not in normalized or not isinstance(normalized[metric], (int, float)):
                normalized[metric] = None
        
        # Add metadata
        normalized["filing_type"] = filing_type
        if filing_date:
            normalized["filing_date"] = filing_date.strftime("%Y-%m-%d")
        
        return normalized
