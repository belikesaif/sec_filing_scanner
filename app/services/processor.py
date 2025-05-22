# app/services/processor.py
import re
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class FilingProcessor:
    # Common financial metrics to extract
    METRIC_MAPPINGS = {
        'revenue': ['revenue', 'net revenue', 'total revenue', 'net sales'],
        'net_income': ['net income', 'net earnings', 'net profit'],
        'operating_income': ['operating income', 'income from operations'],
        'total_assets': ['total assets'],
        'total_liabilities': ['total liabilities'],
        'cash_and_equivalents': ['cash and cash equivalents', 'cash and equivalents'],
        'eps': ['earnings per share', 'basic eps', 'diluted eps']
    }

    def normalize_number(self, value: str) -> Optional[float]:
        """Normalize numeric values to a standard format."""
        try:
            # Remove common artifacts
            value = value.strip().replace('$', '').replace(',', '')
            
            # Handle parentheses for negative numbers
            if '(' in value and ')' in value:
                value = '-' + value.replace('(', '').replace(')', '')

            # Handle scale indicators
            scale_multipliers = {
                'million': 1_000_000,
                'millions': 1_000_000,
                'm': 1_000_000,
                'billion': 1_000_000_000,
                'billions': 1_000_000_000,
                'b': 1_000_000_000,
                'k': 1_000,
                'thousand': 1_000,
                'thousands': 1_000
            }

            value_lower = value.lower()
            multiplier = 1
            for scale, mult in scale_multipliers.items():
                if scale in value_lower:
                    multiplier = mult
                    value = value_lower.replace(scale, '').strip()
                    break

            # Convert to float and apply multiplier
            return float(value) * multiplier
        except:
            return None

    def extract_accession_number(self, text: str) -> str:
        """Extract SEC accession number from filing text."""
        pattern = r'ACCESSION NUMBER:\s*(\d{10}-\d{2}-\d{6})'
        match = re.search(pattern, text)
        if match:
            return match.group(1)
        return ""

    def extract_filing_date(self, text: str) -> str:
        """Extract filing date from document."""
        # Try common date formats in SEC filings
        patterns = [
            r'FILED AS OF DATE:\s*(\d{8})',
            r'CONFORMED PERIOD OF REPORT:\s*(\d{8})',
            r'FILED:\s*(\d{4}-\d{2}-\d{2})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1)
                try:
                    if len(date_str) == 8:  # YYYYMMDD format
                        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
                    return date_str  # Already in YYYY-MM-DD format
                except Exception:
                    continue
        
        return datetime.now().strftime("%Y-%m-%d")  # Fallback to current date

    def extract_tables(self, html_content: str) -> List[pd.DataFrame]:
        """Extract tables from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        tables = []
        
        for table in soup.find_all('table'):
            try:
                # Convert table to list of lists
                data = []
                max_cols = 0
                
                # First pass to determine max columns and clean data
                for row in table.find_all('tr'):
                    cols = row.find_all(['td', 'th'])
                    if cols:  # Skip empty rows
                        # Clean and normalize cell text
                        row_data = []
                        for col in cols:
                            cell_text = col.get_text(strip=True)
                            # Handle colspan if present
                            colspan = int(col.get('colspan', 1))
                            if colspan > 1:
                                row_data.extend([cell_text] + [None] * (colspan - 1))
                            else:
                                row_data.append(cell_text)
                        
                        if any(cell for cell in row_data):  # Only include non-empty rows
                            max_cols = max(max_cols, len(row_data))
                            data.append(row_data)
                
                if not data or max_cols == 0:
                    continue
                
                # Pad rows to ensure consistent column count
                padded_data = []
                for row in data:
                    if len(row) < max_cols:
                        row.extend([None] * (max_cols - len(row)))
                    elif len(row) > max_cols:
                        # Trim excess columns but log a warning
                        logger.warning(f"Row had {len(row)} columns but expected {max_cols}")
                        row = row[:max_cols]
                    padded_data.append(row)
                
                # Determine if first row contains headers
                potential_headers = padded_data[0] if padded_data else []
                is_header_row = False
                if potential_headers:
                    # Check if first row has more text cells than numeric cells
                    text_cells = sum(1 for cell in potential_headers if cell and not any(c.isdigit() for c in str(cell)))
                    is_header_row = text_cells > len(potential_headers) / 2
                
                # Create DataFrame
                if is_header_row:
                    df = pd.DataFrame(padded_data[1:], columns=potential_headers)
                else:
                    df = pd.DataFrame(padded_data)
                
                # Clean up the DataFrame
                df = df.replace({'': None, 'None': None})
                df = df.dropna(how='all')  # Drop rows that are all NA
                df = df.dropna(axis=1, how='all')  # Drop columns that are all NA
                
                if not df.empty and df.shape[1] > 1:  # Only keep tables with at least 2 columns
                    tables.append(df)
                
            except Exception as e:
                logger.warning(f"Failed to parse table: {str(e)}")
                continue
            
        return tables

    def process_tables(self, tables: List[pd.DataFrame]) -> Dict[str, float]:
        """Process extracted tables to find relevant financial metrics."""
        metrics = {}
        
        for table in tables:
            if table.empty:
                continue
                
            # Convert table to string for easier searching
            table_str = table.to_string().lower()
            
            # Search for each metric in the table
            for metric_name, variations in self.METRIC_MAPPINGS.items():
                if metric_name in metrics:  # Skip if we already found this metric
                    continue
                    
                for variation in variations:
                    # Look for rows containing the metric name
                    matching_rows = table[table.apply(lambda x: x.astype(str).str.contains(variation, case=False, na=False)).any(axis=1)]
                    
                    if not matching_rows.empty:
                        # Try to find the value in the same row
                        for row in matching_rows.values:
                            # Look for potential numeric values
                            for cell in row:
                                if cell and isinstance(cell, str):
                                    # Try to normalize and convert to number
                                    value = self.normalize_number(str(cell))
                                    if value is not None:
                                        metrics[metric_name] = value
                                        break
                            if metric_name in metrics:
                                break
                    
                    if metric_name in metrics:
                        break

        return metrics

    def extract_metrics_from_text(self, text: str) -> Dict[str, float]:
        """Extract metrics from text using regex patterns."""
        metrics = {}
        
        # Look for each metric in the text
        for metric_name, variations in self.METRIC_MAPPINGS.items():
            if metric_name in metrics:  # Skip if already found in tables
                continue
                
            for variation in variations:
                # Pattern to match metric followed by numeric value
                pattern = fr'{variation}\s*(?:of|:|\s)\s*[\$]?\s*([\(\-]?\d[\d\,\.]*\d[\)\s]*(?:million|billion|m|b|k)?)'
                matches = re.finditer(pattern, text.lower())
                
                for match in matches:
                    value = self.normalize_number(match.group(1))
                    if value is not None:
                        metrics[metric_name] = value
                        break
                
                if metric_name in metrics:
                    break
        
        return metrics

    def _try_different_encodings(self, content: str) -> str:
        """Try to fix encoding issues in the content."""
        encodings = ['utf-8', 'latin1', 'cp1252', 'ascii']
        for encoding in encodings:
            try:
                if isinstance(content, str):
                    # If it's already a string, try to encode and decode
                    return content.encode(encoding, errors='ignore').decode(encoding)
                else:
                    # If it's bytes, try to decode
                    return content.decode(encoding, errors='ignore')
            except (UnicodeError, AttributeError):
                continue
        return content  # Return original if no encoding works

    def process(self, content: str) -> Dict[str, float]:
        """Process a filing and extract key metrics."""
        try:
            # Try to fix encoding issues
            content = self._try_different_encodings(content)
            
            # Try different parsers if one fails
            for parser in ['lxml', 'html.parser', 'html5lib']:
                try:
                    soup = BeautifulSoup(content, parser)
                    break
                except Exception as e:
                    logger.warning(f"Parser {parser} failed: {e}")
                    continue
            else:
                logger.error("All parsers failed")
                return {}

            # First try to extract from tables
            tables = self.extract_tables(content)
            metrics = self.process_tables(tables)
            
            # Then try to find missing metrics in text
            text_metrics = self.extract_metrics_from_text(content)
            
            # Combine metrics, preferring table values over text values
            for metric, value in text_metrics.items():
                if metric not in metrics:
                    metrics[metric] = value
            
            return metrics
        except Exception as e:
            logger.error(f"Error processing filing: {e}")
            return {}
