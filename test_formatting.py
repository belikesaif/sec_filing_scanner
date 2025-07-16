#!/usr/bin/env python3
"""
Test script to verify that the financial formatting changes work correctly.
"""

from app.services.streamlit.metrics import MetricsService
from app.services.streamlit.components.charts import format_currency

def test_formatting():
    """Test the new formatting functions."""
    
    # Test MetricsService format_value method
    metrics_service = MetricsService()
    
    # Test cases with different value ranges including units
    test_values = [
        ("1000000", "$1,000,000"),           # 1 million
        ("100000000", "$100,000,000"),       # 100 million  
        ("1000000000", "$1,000,000,000"),    # 1 billion
        ("1500.75", "$1,501"),               # Small number (rounded)
        ("0", "$0"),                         # Zero
        ("", "N/A"),                         # Empty string
        (None, "N/A"),                       # None value
        ("100 M", "$100,000,000"),           # With M unit
        ("100M", "$100,000,000"),            # With M unit (no space)
        ("1.5 B", "$1,500,000,000"),         # With B unit
        ("1.5B", "$1,500,000,000"),          # With B unit (no space)
        ("500 million", "$500,000,000"),     # Full word million
        ("2.5 billion", "$2,500,000,000"),   # Full word billion
        ("750 K", "$750,000"),               # With K unit
        ("$100 M", "$100,000,000"),          # Already has $ and M
        ("$1,500.75", "$1,501"),             # Already formatted currency
    ]
    
    print("Testing MetricsService.format_value():")
    print("-" * 50)
    
    for input_val, expected in test_values:
        try:
            result = metrics_service.format_value(input_val)
            status = "✓" if result == expected else "✗"
            print(f"{status} Input: {input_val!r:>15} -> Output: {result:>20} (Expected: {expected})")
        except Exception as e:
            print(f"✗ Input: {input_val!r:>15} -> Error: {e}")
    
    print("\n" + "=" * 60 + "\n")
    
    # Test format_currency function
    test_currency_values = [
        (1000000, "$1,000,000"),
        (100000000, "$100,000,000"),
        (1000000000, "$1,000,000,000"),
        (1500.75, "$1,501"),
        (0, "$0"),
        (750000, "$750,000"),
    ]
    
    print("Testing format_currency():")
    print("-" * 50)
    
    for input_val, expected in test_currency_values:
        try:
            result = format_currency(input_val)
            status = "✓" if result == expected else "✗"
            print(f"{status} Input: {input_val:>15} -> Output: {result:>20} (Expected: {expected})")
        except Exception as e:
            print(f"✗ Input: {input_val:>15} -> Error: {e}")

if __name__ == "__main__":
    test_formatting()
