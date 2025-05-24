# app/services/streamlit/components/metric_table.py
import streamlit as st
import pandas as pd

METRIC_DESCRIPTIONS = {
    "revenue": "Total revenue from sales and operations",
    "net_income": "Net profit or loss after all expenses",
    "total_assets": "Total value of all assets owned",
    "total_liabilities": "Total amount of debts and obligations",
    "shareholders_equity": "Total equity held by shareholders"
}

def display_metric_table(metrics: dict):
    """
    Display financial metrics in a formatted table.
    
    Args:
        metrics: Dictionary containing financial metrics
    """
    # Convert metrics to a more readable format
    formatted_metrics = {}
    
    # Format each metric with proper labels and formatting
    for key in ["revenue", "net_income", "total_assets", "total_liabilities", "shareholders_equity"]:
        if key in metrics and metrics[key]:
            formatted_metrics[key] = {
                "Label": key.replace("_", " ").title(),
                "Value": metrics[key],
                "Description": METRIC_DESCRIPTIONS.get(key, "")
            }
    
    # Create a DataFrame for display
    if formatted_metrics:
        # Display each metric in its own container
        for metric, data in formatted_metrics.items():
            col1, col2 = st.columns([1, 2])
            with col1:
                st.metric(
                    label=data["Label"],
                    value=data["Value"]
                )
            with col2:
                st.caption(data["Description"])
            st.divider()
    else:
        st.info("No metrics available for display.")