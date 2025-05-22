import streamlit as st
import pandas as pd
from pathlib import Path
import sys
from datetime import datetime

# Add the app directory to the path so we can import our modules
app_path = str(Path(__file__).parent.parent.parent)
if app_path not in sys.path:
    sys.path.append(app_path)

from app.services.langgraph_chatbot import EnhancedChatbotService
from app.services.sql_storage import SQLStorage

# Initialize services
@st.cache_resource
def get_chatbot():
    return EnhancedChatbotService()

@st.cache_resource
def get_sql_storage():
    return SQLStorage()

st.title("🤖 AI Filing Assistant")

# Get available tickers
sql_storage = get_sql_storage()
with sql_storage.session_scope() as session:
    tickers = session.query(sql_storage.Filing.ticker).distinct().all()
    tickers = [t[0] for t in tickers]

# Sidebar configuration
st.sidebar.header("Settings")
selected_ticker = st.sidebar.selectbox("Company", ["All Companies"] + tickers)
show_sources = st.sidebar.checkbox("Show Sources", value=True)
enable_context = st.sidebar.checkbox("Enable Context Window", value=True)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
chatbot = get_chatbot()
if prompt := st.chat_input("Ask me anything about SEC filings..."):
    # Display user message
    st.chat_message("user").markdown(prompt)
    
    # Add user message to state
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Get bot response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = chatbot.get_response(prompt)
            st.markdown(response)
            
            # Add assistant response to state
            st.session_state.messages.append({"role": "assistant", "content": response})

# Sidebar controls
st.sidebar.markdown("---")
if st.sidebar.button("Clear Chat History"):
    st.session_state.messages = []
    st.rerun()

# Example questions
st.sidebar.markdown("### Example Questions")
examples = [
    "What was Apple's revenue in the last quarter?",
    "Compare Microsoft and Google's R&D spending",
    "What are the main risks mentioned in Tesla's latest 10-K?",
    "Show me Meta's year-over-year growth in total assets",
]
for example in examples:
    if st.sidebar.button(example):
        # Simulate clicking the chat input with the example
        st.session_state.messages.append({"role": "user", "content": example})
        with st.chat_message("user"):
            st.markdown(example)
        
        chatbot = get_chatbot()
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = chatbot.get_response(example)
                st.markdown(response)
                
                st.session_state.messages.append({"role": "assistant", "content": response})
