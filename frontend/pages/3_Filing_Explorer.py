import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import os

# Add the app directory to the path so we can import our modules
app_path = str(Path(__file__).parent.parent.parent)
if app_path not in sys.path:
    sys.path.append(app_path)

from app.services.sql_storage import SQLStorage

# Initialize services
@st.cache_resource
def get_sql_storage():
    return SQLStorage()

st.title("📁 Filing Explorer")

# Get SQL storage
sql_storage = get_sql_storage()

# Get available tickers
with sql_storage.session_scope() as session:
    tickers = session.query(sql_storage.Filing.ticker).distinct().all()
    tickers = [t[0] for t in tickers]

# Sidebar filters
st.sidebar.header("Filters")
selected_ticker = st.sidebar.selectbox("Select Company", tickers)
filing_type = st.sidebar.selectbox("Filing Type", ["10-K", "10-Q"])

if selected_ticker and filing_type:
    # Get filings from database
    with sql_storage.session_scope() as session:
        filings = session.query(sql_storage.Filing).filter(
            sql_storage.Filing.ticker == selected_ticker,
            sql_storage.Filing.filing_type == filing_type
        ).order_by(sql_storage.Filing.filing_date.desc()).all()
    
    if filings:
        st.header(f"{selected_ticker} - {filing_type} Filings")
        
        # Create tabs for different views
        tab1, tab2 = st.tabs(["List View", "Details View"])
        
        with tab1:
            # Create a DataFrame for the filings
            filings_data = []
            for filing in filings:
                filings_data.append({
                    "Filing Date": filing.filing_date,
                    "Accession Number": filing.accession_number,
                    "File Path": filing.file_path
                })
            
            df = pd.DataFrame(filings_data)
            st.dataframe(df, hide_index=True)
        
        with tab2:
            # Create an expander for each filing
            for filing in filings:
                with st.expander(f"{filing.filing_type} - {filing.filing_date.strftime('%Y-%m-%d')}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Filing Details**")
                        st.write(f"Accession: {filing.accession_number}")
                        st.write(f"Processed: {filing.processed_at}")
                    
                    with col2:
                        st.markdown("**Key Metrics**")
                        # Get metrics for this filing
                        metrics = session.query(sql_storage.Metric).filter(
                            sql_storage.Metric.filing_id == filing.id
                        ).all()
                        
                        for metric in metrics:
                            st.write(f"{metric.metric_name}: ${metric.value:,.2f}")
                    
                    # Show file path and preview button
                    st.markdown("**File Location**")
                    st.code(filing.file_path)
                    
                    if os.path.exists(filing.file_path):
                        if st.button(f"Preview Content", key=filing.id):
                            try:
                                with open(filing.file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                st.text_area("File Content Preview", content, height=300)
                            except Exception as e:
                                st.error(f"Error reading file: {e}")
                    else:
                        st.warning("File not found on disk")
    else:
        st.info(f"No {filing_type} filings found for {selected_ticker}")
else:
    st.info("Please select a company and filing type to explore")
