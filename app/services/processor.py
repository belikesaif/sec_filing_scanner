# app/services/processor.py
import re
from bs4 import BeautifulSoup
from app.utils.logger import setup_logger
from datetime import datetime

logger = setup_logger(__name__)

class FilingProcessor:
    def __init__(self, file_path: str):
        self.file_path = file_path    
        
    def load_file(self) -> str:
        """Load the content of the filing from disk."""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read()
            logger.info(f"Successfully loaded file: {self.file_path}")
            return content
        except Exception as e:
            logger.error(f"Error reading file {self.file_path}: {e}")
            return ""

    def parse_html(self, html_content: str) -> str:
        """Parse HTML content and extract clean text."""
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            text = soup.get_text(separator=" ", strip=True)
            logger.info(f"Extracted text from file: {self.file_path}")
            return text
        except Exception as e:
            logger.error(f"Error parsing HTML content in {self.file_path}: {e}")
            return ""    
    
    def extract_quantitative_data(self, text: str) -> dict:
        """Extract key quantitative metrics from the filing text using regex."""
        data = {}
        try:
            def convert_to_standard_units(value: str, unit: str = None) -> str:
                """Convert numbers to standard form based on their units."""
                try:
                    value = float(value.replace(',', ''))
                    if unit:
                        unit = unit.lower()
                        if unit in ['billion', 'b', 'bn']:
                            value *= 1_000_000_000
                        elif unit in ['million', 'm', 'mil']:
                            value *= 1_000_000
                    return f"{value:.2f}"
                except (ValueError, TypeError):
                    return None

            # Define number patterns that handle various formats including unit multipliers
            number_pattern = r'(?:[\$]?\s?)(?:\()?([\d,\.]+)(?:\))?\s*(?:(billion|million|M|B|bn|mil))?'
            table_row_pattern = r'[\|\s]*(?:Total |Net |Consolidated )?{}\s*[\|\s]*' + number_pattern
            statement_pattern = r'(?:Total |Net |Consolidated )?{}\s*(?:was |of |:)?\s*' + number_pattern

            # Mapping of metrics to their various text representations
            metric_patterns = {
                "revenue": [
                    "Revenue",
                    "Revenues",
                    "Net Sales",
                    "Net Revenue",
                    "Total Revenue",
                    "Total Net Revenue",
                    "Net Operating Revenue"
                ],
                "net_income": [
                    "Net Income",
                    "Net Earnings",
                    "Net Profit",
                    "Net Loss",
                    "Net Income \\(Loss\\)",
                    "Net Income Attributable to.{0,50}Shareholders",
                    "Net Income Available to Common"
                ],
                "total_assets": [
                    "Total Assets",
                    "Assets, Total",
                    "Consolidated Total Assets",
                    "Total Consolidated Assets"
                ],
                "total_liabilities": [
                    "Total Liabilities",
                    "Liabilities, Total",
                    "Total Consolidated Liabilities",
                    "Consolidated Total Liabilities"
                ],
                "shareholders_equity": [
                    "Shareholders[\'']? Equity",
                    "Stockholders[\'']? Equity",
                    "Total Equity",
                    "Total Shareholders[\'']? Equity",
                    "Total Stockholders[\'']? Equity"
                ]
            }   
            
            # Extract values for each metric
            for metric_key, pattern_list in metric_patterns.items():
                for base_pattern in pattern_list:
                    # Try both table-like format and statement format
                    full_patterns = [
                        table_row_pattern.format(base_pattern),
                        statement_pattern.format(base_pattern)
                    ]
                    
                    for pattern in full_patterns:
                        matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                        for match in matches:
                            try:
                                # Extract the number and unit if present
                                value = match.group(1)
                                unit = match.group(2) if len(match.groups()) > 1 else None
                                normalized_value = convert_to_standard_units(value, unit)
                                
                                if normalized_value is not None:
                                    data[metric_key] = normalized_value
                                    break  # Take the first valid match
                            except (ValueError, IndexError):
                                continue
                    
                    if metric_key in data:
                        break  # Move to next metric if we found a value

            logger.info(f"Extracted quantitative data from {self.file_path}: {data}")
            
        except Exception as e:
            logger.error(f"Error extracting quantitative data from {self.file_path}: {e}")
        
        return data

    def extract_filing_date(self, text: str) -> str:
        """Extract the filing date from the SEC filing text."""
        try:            # Try to find date in standard formats
            date_patterns = [
                r'FILED\s*:\s*(\d{4}-\d{2}-\d{2})',
                r'FILED AS OF DATE\s*:\s*(\d{8})',
                r'CONFORMED PERIOD OF REPORT\s*:\s*(\d{8})',
                r'FILED DATE\s*:\s*(\d{2}/\d{2}/\d{4})',
                r'FILED\s*:\s*(\d{2}/\d{2}/\d{4})',
                r'PERIOD OF REPORT\s*:\s*(\d{4}-\d{2}-\d{2})',
                r'PERIOD OF REPORT\s*:\s*(\d{8})',
                r'CONFORMED PERIOD\s*:\s*(\d{8})',
                r'DATE OF REPORT\s*:\s*(\d{2}/\d{2}/\d{4})',
                r'(?:For the (?:quarterly|fiscal) period ended|PERIOD-END)\s*:?\s*(\w+ \d{1,2},? \d{4})',
                r'REPORT\s+FOR\s+PERIOD\s+ENDING\s*:?\s*(\w+ \d{1,2},? \d{4})',
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    date_str = match.group(1)
                    
                    # Handle different date formats
                    try:
                        if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                            return date_str
                        elif re.match(r'\d{8}', date_str):
                            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
                        elif re.match(r'\d{2}/\d{2}/\d{4}', date_str):
                            month, day, year = date_str.split('/')
                            return f"{year}-{month}-{day}"
                        else:
                            # Handle month name format
                            date_obj = datetime.strptime(date_str, '%B %d, %Y')
                            return date_obj.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
            
            logger.warning(f"Could not extract filing date from {self.file_path}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting filing date from {self.file_path}: {e}")
            return None

    def process(self) -> dict:
        """Run the complete processing pipeline: load, parse, and extract data."""
        raw_content = self.load_file()
        if not raw_content:
            return {}
            
        text_content = self.parse_html(raw_content)
        filing_date = self.extract_filing_date(raw_content)  # Try to extract from raw content
        quantitative_data = self.extract_quantitative_data(text_content)
        
        return {
            "full_text": text_content,
            "quantitative_data": quantitative_data,
            "filing_date": filing_date
        }
