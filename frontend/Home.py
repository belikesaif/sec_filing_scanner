import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import sys
import time
import threading
import requests
from datetime import datetime
from sqlalchemy import text

# Add the app directory to the path so we can import our modules
app_path = str(Path(__file__).parent.parent)
if app_path not in sys.path:
    sys.path.append(app_path)

from app.services.sql_storage import SQLStorage
from app.services.langgraph_chatbot import EnhancedChatbotService
from app.services.sec_scanner import SecFilingScanner
from app.services.processing_pipeline import ProcessingPipeline

# Page config
st.set_page_config(
    page_title="SEC Filing Scanner",
    page_icon="📊",
    layout="wide"
)

# Initialize services
@st.cache_resource
def get_sql_storage():
    return SQLStorage()

@st.cache_resource
def get_chatbot():
    return EnhancedChatbotService()

@st.cache_resource
def initialize_background_services():
    # Initialize scanner and processing pipeline
    scanner = SecFilingScanner()
    pipeline = ProcessingPipeline()
    scanner.start()
    
    # Create a background thread for processing
    def process_filings():
        while True:
            try:
                pipeline.process_all_new_filings()
                time.sleep(300)  # Wait 5 minutes between scans
            except Exception as e:
                st.error(f"Error in processing pipeline: {e}")
                time.sleep(60)  # Wait a minute before retrying on error
    
    thread = threading.Thread(target=process_filings, daemon=True)
    thread.start()
    return scanner, pipeline

# Start background services
scanner, pipeline = initialize_background_services()

# Health check function
def check_system_health():
    health_status = {
        "api_status": "Unknown",
        "database": "Unknown",
        "embeddings": "Unknown",
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Check API status
    try:
        # Assuming the API is running on localhost:8000
        response = requests.get("http://localhost:8000/filings/status", timeout=2)
        if response.status_code == 200:
            health_status["api_status"] = "✅ Online"
        else:
            health_status["api_status"] = f"⚠️ Error (Status: {response.status_code})"
    except Exception as e:
        health_status["api_status"] = f"❌ Offline ({str(e)})"
    
    # Check database status
    try:
        sql_storage = get_sql_storage()
        with sql_storage.session_scope() as session:
            # Simple query to check if database is responsive
            result = session.execute(text("SELECT 1")).scalar()
            if result == 1:
                health_status["database"] = "✅ Connected"
            else:
                health_status["database"] = "⚠️ Error"
    except Exception as e:
        health_status["database"] = f"❌ Disconnected ({str(e)})"
    
    # Check embeddings status
    try:
        response = requests.get("http://localhost:8000/filings/debug/embeddings", timeout=2)
        if response.status_code == 200:
            data = response.json()
            count = data.get("collection_info", {}).get("count", 0)
            health_status["embeddings"] = f"✅ Available ({count} embeddings)"
        else:
            health_status["embeddings"] = f"⚠️ Error (Status: {response.status_code})"
    except Exception as e:
        health_status["embeddings"] = f"❌ Unavailable ({str(e)})"
    
    return health_status

# Title and description
st.title("📊 SEC Filing Scanner Dashboard")
st.markdown("""
This application helps you analyze SEC filings (10-K and 10-Q) for major companies.
You can:
- Chat with AI about company financials
- View key metrics and trends
- Access and analyze filing contents
""")

# System Health Check Panel
with st.sidebar:
    st.header("🔍 System Health")
    if st.button("Check System Health"):
        with st.spinner("Checking system health..."):
            health_status = check_system_health()
            
            st.subheader("Component Status")
            st.info(f"Last checked: {health_status['last_update']}")
            
            # Display health status
            st.metric("API Service", health_status["api_status"])
            st.metric("Database", health_status["database"])
            st.metric("Embeddings", health_status["embeddings"])
            
            # Add refresh button
            st.button("Refresh", key="refresh_health")
    else:
        st.info("Click the button above to check system health")


# Get available tickers
sql_storage = get_sql_storage()
with sql_storage.session_scope() as session:
    tickers = session.query(sql_storage.Filing.ticker).distinct().all()
    tickers = [t[0] for t in tickers]

# Key metrics overview
st.header("📈 Key Metrics Overview")
col1, col2 = st.columns(2)

with col1:
    selected_ticker = st.selectbox("Select Company", tickers)
    
with col2:
    metric_type = st.selectbox(
        "Select Metric",
        ["revenue", "net_income", "total_assets", "total_liabilities", "shareholders_equity"]
    )

if selected_ticker and metric_type:
    # Get metric data
    metrics = sql_storage.get_filing_metrics(
        ticker=selected_ticker,
        metric_names=[metric_type]
    )
    
    if metrics:
        # Create DataFrame
        df = pd.DataFrame(metrics)
        df['filing_date'] = pd.to_datetime(df['filing_date'])
        df = df.sort_values('filing_date')
        
        # Create trend chart
        fig = px.line(
            df,
            x='filing_date',
            y='value',
            title=f"{selected_ticker} - {metric_type.replace('_', ' ').title()}",
            labels={'filing_date': 'Date', 'value': 'Value (USD)'},
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Show recent values
        st.subheader("Recent Values")
        recent_df = df.tail(5).sort_values('filing_date', ascending=False)
        st.dataframe(
            recent_df[['filing_date', 'filing_type', 'value']],
            hide_index=True
        )
    else:
        st.info(f"No {metric_type} data available for {selected_ticker}")

# Quick Chat
st.header("💬 Quick Chat")
st.markdown("Ask questions about the selected company's financials")

question = st.text_input("Your question:")
if question:
    chatbot = get_chatbot()
    with st.spinner("Processing your question..."):
        response = chatbot.get_response(question, ticker=selected_ticker) # Changed 'query' to 'get_response'
        
        if "error" in response:
            st.error(response["error"])
        else:
            st.success(response["answer"])
            
            # Show sources if available
            if "sources" in response and response["sources"]:
                with st.expander("Sources"):
                    for source in response["sources"]:
                        if source["type"] == "metric":
                            st.write(f"📊 {source['filing_type']} ({source['filing_date']})")
                        else:
                            st.write(f"📄 {source['source']}")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit • [GitHub](https://github.com)")
