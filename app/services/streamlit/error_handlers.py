"""Error handlers for Streamlit app components."""
from functools import wraps
import streamlit as st

def handle_torch_path_error(func):
    """Decorator to handle torch path errors in Streamlit."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except RuntimeError as e:
            if "no running event loop" in str(e) or "Tried to instantiate class '__path__._path'" in str(e):
                # Ignore known torch path errors that don't affect functionality
                pass
            else:
                raise
    return wrapper
