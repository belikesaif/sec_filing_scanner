# app/services/streamlit/components/charts.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from app.services.streamlit.metrics import MetricsService

def create_revenue_chart(ticker: str, metrics_service: MetricsService) -> go.Figure:
    """Create a revenue trend chart for a company."""
    # Get historical revenue data
    df = metrics_service.get_historical_metrics(ticker, "revenue")
    if df.empty:
        return None

    # Convert to numeric and sort by date
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df = df.sort_values('filing_date')
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=df['filing_date'],
            y=df['value'],
            name="Revenue",
            line=dict(color='blue', width=2)
        )
    )

    fig.update_layout(
        title=f"{ticker} Historical Revenue",
        xaxis_title="Filing Date",
        yaxis_title="Revenue ($)",
        template="plotly_white",
        hovermode="x",
        showlegend=True
    )

    return fig

def create_metric_chart(ticker: str, metric_name: str, metrics_service: MetricsService) -> go.Figure:
    """Create a chart for any metric over time."""
    # Get historical data
    df = metrics_service.get_historical_metrics(ticker, metric_name)
    if df.empty:
        return None

    # Convert to numeric and sort by date
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df = df.sort_values('filing_date')
    
    # Create figure
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=df['filing_date'],
            y=df['value'],
            name=metric_name.replace('_', ' ').title(),
            line=dict(color='blue', width=2)
        )
    )

    fig.update_layout(
        title=f"{ticker} Historical {metric_name.replace('_', ' ').title()}",
        xaxis_title="Filing Date",
        yaxis_title=f"{metric_name.replace('_', ' ').title()} ($)",
        template="plotly_white",
        hovermode="x",
        showlegend=True
    )

    return fig

def create_financial_comparison_chart(ticker: str, metrics_service):
    """
    Create a comparison chart of key financial metrics.
    
    Args:
        ticker: The stock ticker symbol
        metrics_service: Instance of MetricsService
        
    Returns:
        plotly.graph_objects.Figure: A plotly chart object
    """
    # Get the most recent filing metrics
    cursor = metrics_service.sql_storage.conn.cursor()
    cursor.execute("""
        SELECT f.filing_date, m.revenue, m.net_income, m.total_assets, m.total_liabilities, m.shareholders_equity
        FROM filings f
        JOIN metrics m ON f.id = m.filing_id
        WHERE f.ticker = ?
        ORDER BY f.filing_date DESC
        LIMIT 1
    """, (ticker,))
    
    result = cursor.fetchone()
    if not result:
        return None
    
    # Extract the data
    filing_date, revenue, net_income, total_assets, total_liabilities, shareholders_equity = result
    
    # Convert to numeric values
    metrics = {
        "Revenue": float(revenue.replace("$", "").replace(",", "")) if revenue else 0,
        "Net Income": float(net_income.replace("$", "").replace(",", "")) if net_income else 0,
        "Total Assets": float(total_assets.replace("$", "").replace(",", "")) if total_assets else 0,
        "Total Liabilities": float(total_liabilities.replace("$", "").replace(",", "")) if total_liabilities else 0,
        "Shareholders' Equity": float(shareholders_equity.replace("$", "").replace(",", "")) if shareholders_equity else 0
    }
    
    # Create a DataFrame
    df = pd.DataFrame({
        "Metric": list(metrics.keys()),
        "Value": list(metrics.values())
    })
    
    # Create a bar chart
    fig = px.bar(
        df,
        x="Metric",
        y="Value",
        title=f"{ticker} Financial Overview ({filing_date})",
        labels={"Metric": "Financial Metric", "Value": "Amount ($)"}
    )
    
    # Customize the layout
    fig.update_layout(
        xaxis_title="Financial Metric",
        yaxis_title="Amount ($)",
        height=400
    )
    
    return fig

def format_currency(value: float) -> str:
    """Format large numbers into B/M notation."""
    if value >= 1_000_000_000:
        return f"${value/1_000_000_000:.1f}B"
    elif value >= 1_000_000:
        return f"${value/1_000_000:.1f}M"
    else:
        return f"${value:,.0f}"