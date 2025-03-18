# app/services/processor.py
import re
from bs4 import BeautifulSoup
from app.utils.logger import setup_logger
#=====================================================================================================================================================
logger = setup_logger(__name__)
#=====================================================================================================================================================
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
        # Note: The regex patterns here are simple and may need refinement based on filing formats.
        data = {}
        try:
            revenue_pattern = re.compile(r"Revenue[\s:]*\$\s?([\d,\.]+)", re.IGNORECASE)
            net_income_pattern = re.compile(r"Net Income[\s:]*\$\s?([\d,\.]+)", re.IGNORECASE)
            assets_pattern = re.compile(r"Total Assets[\s:]*\$\s?([\d,\.]+)", re.IGNORECASE)
            liabilities_pattern = re.compile(r"Total Liabilities[\s:]*\$\s?([\d,\.]+)", re.IGNORECASE)
            equity_pattern = re.compile(r"Shareholders' Equity[\s:]*\$\s?([\d,\.]+)", re.IGNORECASE)

            revenue_match = revenue_pattern.search(text)
            net_income_match = net_income_pattern.search(text)
            assets_match = assets_pattern.search(text)
            liabilities_match = liabilities_pattern.search(text)
            equity_match = equity_pattern.search(text)

            data["revenue"] = revenue_match.group(1) if revenue_match else None
            data["net_income"] = net_income_match.group(1) if net_income_match else None
            data["total_assets"] = assets_match.group(1) if assets_match else None
            data["total_liabilities"] = liabilities_match.group(1) if liabilities_match else None
            data["shareholders_equity"] = equity_match.group(1) if equity_match else None

            logger.info(f"Extracted quantitative data from {self.file_path}: {data}")
        except Exception as e:
            logger.error(f"Error extracting quantitative data from {self.file_path}: {e}")
        return data

    def process(self) -> dict:
        """Run the complete processing pipeline: load, parse, and extract data."""
        raw_content = self.load_file()
        if not raw_content:
            return {}
        text_content = self.parse_html(raw_content)
        quantitative_data = self.extract_quantitative_data(text_content)
        return {
            "full_text": text_content,
            "quantitative_data": quantitative_data
        }
