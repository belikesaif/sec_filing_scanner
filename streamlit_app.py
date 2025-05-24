import os
from dotenv import load_dotenv
from app.utils.logger import setup_logger
from app.services.streamlit.error_handlers import handle_torch_path_error
from app.services.streamlit.filing_browser import FilingBrowser

# Set up logger
logger = setup_logger(__name__)

# Load environment variables from .env file
load_dotenv()

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import datetime
import numpy as np
from app.services.streamlit.metrics_validator import MetricsValidator

# Import services
from app.services.streamlit.chat import ChatService
from app.services.streamlit.metrics import MetricsService
from app.services.streamlit.vector_search import VectorSearchService
from app.services.streamlit.components.metric_table import display_metric_table
from app.services.streamlit.components.charts import create_revenue_chart, create_metric_chart

# Set page configuration
st.set_page_config(
    page_title="SEC Filing Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_filing_id_from_path(path: str) -> str:
    """Extract the SEC accession number from a filing path."""
    parts = os.path.normpath(path).split(os.sep)
    try:
        # Find the component that looks like an SEC accession number (e.g., 0000320193-17-000070)
        filing_id = next(p for p in parts if p.count('-') >= 2)
        return filing_id
    except Exception:
        return os.path.basename(path)  # Fallback to the directory name

def refresh_data():
    """Refresh all services and data."""
    try:
        if "metrics_service" in st.session_state:
            st.session_state.metrics_service.reload()
            logger.info("MetricsService reloaded successfully")
            
        if "vector_service" in st.session_state:
            st.session_state.vector_service.reload()
            logger.info("VectorSearchService reloaded successfully")
            
        # Re-initialize services if they don't exist        if not all(service in st.session_state for service in ["metrics_service", "vector_service", "chat_service"]):
            chat_service, metrics_service, vector_service = init_services()
            st.session_state.chat_service = chat_service
            st.session_state.metrics_service = metrics_service
            st.session_state.vector_service = vector_service
            
        st.sidebar.success("Data refreshed successfully!")
        # Use the new rerun method
        st.rerun()
    except Exception as e:
        logger.error(f"Error refreshing data: {e}")
        st.sidebar.error(f"Error refreshing data: {str(e)}")

# Initialize services
@handle_torch_path_error
def init_services():
    chat_service = ChatService()
    metrics_service = MetricsService()
    vector_service = VectorSearchService()
    logger.info("All services initialized successfully")
    return chat_service, metrics_service, vector_service

try:
    chat_service, metrics_service, vector_service = init_services()
    # Store services in session state for access across reruns
    st.session_state.chat_service = chat_service
    st.session_state.metrics_service = metrics_service
    st.session_state.vector_service = vector_service
except Exception as e:
    st.error(f"Error initializing services: {str(e)}")
    st.stop()

# App title
st.title("SEC Filing Assistant")

# Add refresh button in sidebar
if st.sidebar.button("🔄 Refresh Data"):
    refresh_data()

# Sidebar for file browser
st.sidebar.title("File Browser")

# Initialize filing browser
filings_dir = Path(os.getenv("FILINGS_DIR", "sec-edgar-filings"))
filing_browser = FilingBrowser(filings_dir)

# Get list of tickers from the filings directory
tickers = [d.name for d in filings_dir.iterdir() if d.is_dir()]

# Ticker selection
selected_ticker = st.sidebar.selectbox(
    "Select Ticker",
    options=tickers if tickers else ["No tickers found"],
    key="ticker_selector_main"
)

# If a ticker is selected, show available filings
if selected_ticker and selected_ticker != "No tickers found":
    filings = filing_browser.get_filings(selected_ticker)
    
    # Display filings in a dataframe with date information
    if filings:
        filings_df = pd.DataFrame(filings)
        
        # Format filing date for display
        filings_df['display_date'] = filings_df['filing_date'].apply(
            lambda x: x.strftime("%Y-%m-%d") if x else "Unknown Date"
        )
        
        # Add metrics status indicator
        filings_df['metrics_status'] = filings_df['has_metrics'].apply(
            lambda x: "✅" if x else "⏳"
        )
        
        # Create formatted selection options
        filing_options = filings_df.apply(
            lambda x: f"{x['metrics_status']} {x['filing_type']} - {x['display_date']} ({x['filing_id']})", 
            axis=1
        ).tolist()
        
        # Add a header option
        filing_options.insert(0, "Select a filing")
        
        selected_filing = st.sidebar.selectbox(
            "Select Filing",
            options=filing_options,
            key="filing_selector"
        )
        
        # If a filing is selected (not the header option)
        if selected_filing and selected_filing != "Select a filing":
            # Find the selected filing in the dataframe
            filing_idx = filings_df.apply(
                lambda x: f"{x['metrics_status']} {x['filing_type']} - {x['display_date']} ({x['filing_id']})", 
                axis=1
            ) == selected_filing
            
            selected_filing_data = filings_df[filing_idx].iloc[0]
            
            # Get and validate metrics for the selected filing
            raw_metrics = metrics_service.get_filing_metrics(
                selected_filing_data["ticker"],
                selected_filing_data["filing_type"],
                selected_filing_data["filing_id"]
            )
            
            # Create tabs for different views
            tab1, tab2, tab3 = st.tabs(["📊 Metrics", "📄 Text", "📈 Charts"])
            
            with tab1:
                st.subheader(f"Financial Metrics")
                st.caption(f"{selected_filing_data['ticker']} {selected_filing_data['filing_type']} - {selected_filing_data['display_date']}")
                if selected_filing_data["has_metrics"]:
                    # Format and filter metrics for display
                    metrics = {}
                    for k, v in raw_metrics.items():
                        if k not in ["filing_type", "filing_date", "metrics_created", "metrics_updated", "processing_status"]:
                            try:
                                if v and str(v).strip():  # Check if value exists and is not just whitespace
                                    if isinstance(v, str) and v.startswith('$'):
                                        metrics[k] = v  # Already formatted
                                    else:
                                        # Convert to float and format
                                        value = float(str(v).replace('$', '').replace(',', ''))
                                        if abs(value) >= 1_000_000_000:
                                            metrics[k] = f"${value/1_000_000_000:.2f}B"
                                        elif abs(value) >= 1_000_000:
                                            metrics[k] = f"${value/1_000_000:.2f}M"
                                        else:
                                            metrics[k] = f"${value:,.2f}"
                            except (ValueError, TypeError) as e:
                                st.error(f"Error formatting {k}: {str(e)}")
                                continue
                    
                    if metrics:
                        display_metric_table(metrics)
                        
                        # Add option to view more details
                        with st.expander("ℹ️ Metric Details"):
                            st.text(f"Last Updated: {raw_metrics.get('metrics_updated', 'Unknown')}")
                            st.text(f"Status: {raw_metrics.get('processing_status', 'Completed')}")
                            
                            # Show raw values for debugging
                            with st.expander("🔍 Debug Raw Values"):
                                st.json(raw_metrics)
                    else:
                        st.warning("⚠️ No valid metrics found in this filing")
                else:
                    st.info("⏳ This filing is still being processed...")
                    if st.button("🔄 Check Again"):
                        st.rerun()
            
            with tab2:
                st.subheader("Filing Text")
                # Get a snippet of the filing text
                text_preview = metrics_service.sql_storage.get_filing_text(
                    selected_filing_data["ticker"],
                    selected_filing_data["filing_type"],
                    selected_filing_data["filing_id"]
                )
                if text_preview:
                    with st.expander("📄 View Filing Text", expanded=False):
                        st.text_area("Content", text_preview, height=400)
                else:
                    st.warning("⚠️ Filing text not available")
            with tab3:
                st.subheader("Historical Charts")
                if selected_filing_data["has_metrics"]:
                    metric_options = ["revenue", "net_income", "total_assets", "total_liabilities", "shareholders_equity"]
                    selected_metric = st.selectbox("Select Metric", metric_options)
                    
                    chart = create_metric_chart(
                        ticker=selected_filing_data["ticker"],
                        metric_name=selected_metric,
                        metrics_service=metrics_service
                    )
                    
                    if chart:
                        st.plotly_chart(chart)
                    else:
                        st.info("No historical data available for this metric")
                else:
                    st.info("⏳ Charts will be available once metrics are processed")

# Add predefined questions
PREDEFINED_QUESTIONS = [
    "What was Apple's total revenue in their latest 10-K filing?",
    "How has Microsoft's net income changed over the last 3 quarterly reports?",
    "Compare the total assets of Google and Amazon in their most recent filings.",
    "What are the key financial metrics for Meta's latest quarterly report?",
    "Show me the shareholders' equity trend for Apple over the past year.",
    "What risks did Microsoft mention in their latest annual report?",
    "How much did Amazon spend on R&D according to their latest filing?",
    "What are Google's main sources of revenue?",
    "Summarize Meta's business strategy from their latest 10-K.",
    "What were the major acquisitions mentioned in Microsoft's recent filings?"
]

# Main area - Chat interface
st.header("Chat with SEC Filings")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Display predefined questions
if not st.session_state.messages:  # Only show when chat is empty
    st.write("Try these example questions:")
    cols = st.columns(2)
    for i, question in enumerate(PREDEFINED_QUESTIONS):
        if i % 2 == 0:
            if cols[0].button(f"❓ {question}", key=f"q_{i}"):
                response = chat_service.get_answer(question)
                st.session_state.messages.append({"role": "user", "content": question})
                st.session_state.messages.append({"role": "assistant", "content": response["answer"]})
                st.rerun()
        else:
            if cols[1].button(f"❓ {question}", key=f"q_{i}"):
                response = chat_service.get_answer(question)
                st.session_state.messages.append({"role": "user", "content": question})
                st.session_state.messages.append({"role": "assistant", "content": response["answer"]})
                st.rerun()

# Chat input
if prompt := st.chat_input("Ask a question about SEC filings..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("Thinking..."):
            response = chat_service.get_answer(prompt)
            
            # Display the response
            message_placeholder.markdown(response["answer"])
            
            # Display sources if available
            if "sources" in response and response["sources"]:
                st.markdown("**Sources:**")
                for source in response["sources"]:
                    st.markdown(f"- {source}")
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response["answer"]})

st.sidebar.title("Stock Tickers")

# Clear chat button
if st.sidebar.button("🗑️ Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# Get the list of available stock tickers
ticker_dirs = [d for d in filings_dir.iterdir() if d.is_dir()]