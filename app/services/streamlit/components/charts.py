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
        showlegend=True,
        yaxis=dict(tickformat="$,.0f")
    )
    
    # Add hover template for better formatting
    fig.update_traces(hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.0f}<extra></extra>")

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
        showlegend=True,
        yaxis=dict(tickformat="$,.0f")
    )
    
    # Add hover template for better formatting
    metric_display = metric_name.replace('_', ' ').title()
    fig.update_traces(hovertemplate=f"<b>%{{x}}</b><br>{metric_display}: $%{{y:,.0f}}<extra></extra>")

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
    
    # Convert to numeric values, handling potential unit abbreviations
    def parse_financial_value(value_str):
        """Parse financial values that might contain unit abbreviations."""
        if not value_str:
            return 0
        
        # Clean the string
        clean_str = str(value_str).replace("$", "").replace(",", "").strip()
        
        # Handle unit abbreviations (with and without spaces)
        multiplier = 1
        if ' million' in clean_str.lower() or clean_str.lower().endswith('million'):
            clean_str = clean_str.lower().replace(' million', '').replace('million', '').strip()
            multiplier = 1_000_000
        elif ' billion' in clean_str.lower() or clean_str.lower().endswith('billion'):
            clean_str = clean_str.lower().replace(' billion', '').replace('billion', '').strip()
            multiplier = 1_000_000_000
        elif ' thousand' in clean_str.lower() or clean_str.lower().endswith('thousand'):
            clean_str = clean_str.lower().replace(' thousand', '').replace('thousand', '').strip()
            multiplier = 1_000
        elif clean_str.lower().endswith((' m', 'm', ' mil', 'mil')):
            clean_str = clean_str.lower().replace(' m', '').replace('m', '').replace(' mil', '').replace('mil', '').strip()
            multiplier = 1_000_000
        elif clean_str.lower().endswith((' b', 'b', ' bn', 'bn')):
            clean_str = clean_str.lower().replace(' b', '').replace('b', '').replace(' bn', '').replace('bn', '').strip()
            multiplier = 1_000_000_000
        elif clean_str.lower().endswith((' k', 'k')):
            clean_str = clean_str.lower().replace(' k', '').replace('k', '').strip()
            multiplier = 1_000
        
        try:
            return float(clean_str) * multiplier
        except (ValueError, TypeError):
            return 0
    
    metrics = {
        "Revenue": parse_financial_value(revenue),
        "Net Income": parse_financial_value(net_income),
        "Total Assets": parse_financial_value(total_assets),
        "Total Liabilities": parse_financial_value(total_liabilities),
        "Shareholders' Equity": parse_financial_value(shareholders_equity)
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
        height=400,
        yaxis=dict(tickformat="$,.0f")
    )
    
    # Add hover template for better formatting
    fig.update_traces(hovertemplate="<b>%{x}</b><br>Amount: $%{y:,.0f}<extra></extra>")
    
    return fig

def format_currency(value: float) -> str:
    """Format numbers as full dollar amounts."""
    if not value or value == 0:
        return "$0"
    return f"${value:,.0f}"