import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add the app directory to the path so we can import our modules
app_path = str(Path(__file__).parent.parent.parent)
if app_path not in sys.path:
    sys.path.append(app_path)

from app.services.sql_storage import SQLStorage

# Initialize services
@st.cache_resource
def get_sql_storage():
    return SQLStorage()

st.title("📈 Financial Metrics Analysis")

# Get SQL storage
sql_storage = get_sql_storage()

# Get available tickers
with sql_storage.session_scope() as session:
    tickers = session.query(sql_storage.Filing.ticker).distinct().all()
    tickers = [t[0] for t in tickers]

# Sidebar filters
st.sidebar.header("Filters")
selected_tickers = st.sidebar.multiselect(
    "Select Companies",
    tickers,
    default=tickers[:2] if len(tickers) > 1 else tickers
)

metric_types = [
    "revenue",
    "net_income",
    "total_assets",
    "total_liabilities",
    "shareholders_equity"
]

selected_metrics = st.sidebar.multiselect(
    "Select Metrics",
    metric_types,
    default=["revenue", "net_income"]
)

time_period = st.sidebar.selectbox(
    "Time Period",
    ["Last 3 Years", "Last 5 Years", "Last 10 Years", "All Time"]
)

# Calculate date range
now = datetime.now()
if time_period == "Last 3 Years":
    start_date = str(now.year - 3)
elif time_period == "Last 5 Years":
    start_date = str(now.year - 5)
elif time_period == "Last 10 Years":
    start_date = str(now.year - 10)
else:
    start_date = None

# Get data and create visualizations
if selected_tickers and selected_metrics:
    st.header("Comparative Analysis")
    
    # Create tabs for different visualizations
    tab1, tab2 = st.tabs(["Trend Analysis", "Company Comparison"])
    
    # Get all metrics data
    all_data = []
    for ticker in selected_tickers:
        for metric in selected_metrics:
            metrics = sql_storage.get_filing_metrics(
                ticker=ticker,
                metric_names=[metric],
                start_date=start_date
            )
            for m in metrics:
                m['ticker'] = ticker
                m['metric'] = metric
                all_data.append(m)
    
    if all_data:
        df = pd.DataFrame(all_data)
        df['filing_date'] = pd.to_datetime(df['filing_date'])
        df = df.sort_values('filing_date')
        
        with tab1:
            # Create trend lines for each metric
            for metric in selected_metrics:
                metric_df = df[df['metric'] == metric]
                if not metric_df.empty:
                    fig = px.line(
                        metric_df,
                        x='filing_date',
                        y='value',
                        color='ticker',
                        title=f"{metric.replace('_', ' ').title()} Trend",
                        labels={'filing_date': 'Date', 'value': 'Value (USD)'},
                        template="plotly_white"
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            # Create bar charts comparing latest values
            latest_data = df.sort_values('filing_date').groupby(['ticker', 'metric']).last().reset_index()
            
            for metric in selected_metrics:
                metric_latest = latest_data[latest_data['metric'] == metric]
                if not metric_latest.empty:
                    fig = px.bar(
                        metric_latest,
                        x='ticker',
                        y='value',
                        title=f"Latest {metric.replace('_', ' ').title()} Comparison",
                        labels={'ticker': 'Company', 'value': 'Value (USD)'},
                        template="plotly_white"
                    )
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for the selected criteria")
else:
    st.info("Please select at least one company and metric to analyze")
