import pytest
import pandas as pd
from app.services.processor import FilingProcessor

def test_normalize_number():
    processor = FilingProcessor("dummy_path")
    
    # Test different formats
    assert processor.normalize_number("$1,234.56") == 1234.56
    assert processor.normalize_number("1,234.56 million") == 1234560000.0
    assert processor.normalize_number("$5.67B") == 5670000000.0
    assert processor.normalize_number("(123.45)") == -123.45
    assert processor.normalize_number("") is None
    assert processor.normalize_number(None) is None

def test_process_tables():
    processor = FilingProcessor("dummy_path")
    
    # Create a test DataFrame
    data = {
        'Item': ['Revenue', 'Net Income', 'Total Assets'],
        'Value': ['$1,234.56M', '$567.89M', '$2,345.67B']
    }
    df = pd.DataFrame(data)
    
    # Test table processing
    result = processor.process_tables([df])
    
    assert 'revenue' in result
    assert result['revenue'] == 1234560000.0
    assert 'net_income' in result
    assert result['net_income'] == 567890000.0
    assert 'total_assets' in result
    assert result['total_assets'] == 2345670000000.0

def test_process_tables_with_variations():
    processor = FilingProcessor("dummy_path")
    
    # Test different metric variations
    data = {
        'Item': ['Net Sales', 'Net Earnings', "Stockholders' Equity"],
        'Value': ['$1,234.56M', '$567.89M', '$789.01B']
    }
    df = pd.DataFrame(data)
    
    result = processor.process_tables([df])
    
    assert 'revenue' in result  # Should match 'Net Sales'
    assert result['revenue'] == 1234560000.0
    assert 'net_income' in result  # Should match 'Net Earnings'
    assert result['net_income'] == 567890000.0
    assert 'shareholders_equity' in result  # Should match "Stockholders' Equity"
    assert result['shareholders_equity'] == 789010000000.0

def test_extract_tables_from_html():
    processor = FilingProcessor("dummy_path")
    
    # Create a simple HTML table
    html_content = """
    <html>
        <table>
            <tr><th>Item</th><th>Value</th></tr>
            <tr><td>Revenue</td><td>$1,234.56M</td></tr>
            <tr><td>Net Income</td><td>$567.89M</td></tr>
        </table>
    </html>
    """
    
    tables = processor.extract_tables_from_html(html_content)
    assert len(tables) == 1
    assert not tables[0].empty

def test_regex_fallback():
    processor = FilingProcessor("dummy_path")
    
    # Test text without tables
    text = """
    Financial Results:
    Revenue: $1,234.56 million
    Net Income: $567.89 billion
    """
    
    result = processor.extract_quantitative_data(text)
    assert 'revenue' in result
    assert '1,234.56 million' in result['revenue']
    assert 'net_income' in result
    assert '567.89 billion' in result['net_income']
