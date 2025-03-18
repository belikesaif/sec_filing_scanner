# tests/test_services.py
import time
from app.services.sec_scanner import SecFilingScanner

def test_scanner_start_stop():
    # Use a short polling interval for testing purposes
    scanner = SecFilingScanner(polling_interval=2)
    scanner.start()
    # Allow the scanner to run for a short period
    time.sleep(3)
    scanner.stop()
    assert not scanner.thread.is_alive()
