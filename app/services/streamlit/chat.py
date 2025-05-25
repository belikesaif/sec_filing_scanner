# app/services/streamlit/chat.py
import os
import re
from app.services.chatbot import ChatbotService
from app.services.sql_storage import SQLStorage
from app.services.streamlit.metrics import MetricsService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class ChatService:
    def __init__(self):
        """Initialize the chat service that combines SQL and vector search results."""
        self.chatbot_service = ChatbotService()
        self.sql_storage = SQLStorage()
        self.metrics_service = MetricsService()
        logger.info("ChatService initialized successfully.")
    
    def get_answer(self, question: str) -> dict:
        """Process a user question and return an answer with sources.
        
        Args:
            question: The user's question about SEC filings
            
        Returns:
            dict: Contains the answer and sources used
        """
        logger.info(f"Processing question: {question}")

        # Try to match metric questions
        metric_patterns = [
            (r"What was (.+)'s total revenue in the latest 10-K filing\?", "revenue", "10-K"),
            (r"What was (.+)'s net income in the latest 10-K filing\?", "net_income", "10-K"),
            (r"What are (.+)'s total assets and total liabilities in the latest 10-K filing\?", "assets_liabilities", "10-K"),
            (r"What is (.+)'s shareholders' equity in the latest 10-K filing\?", "shareholders_equity", "10-K"),
            (r"What was (.+)'s total revenue in the latest 10-Q filing\?", "revenue", "10-Q"),
            (r"What was (.+)'s net income in the latest 10-Q filing\?", "net_income", "10-Q"),
            (r"Show the trend of (.+)'s revenue over the last 4 quarters\.", "revenue_trend", None),
        ]
        for pattern, metric, filing_type in metric_patterns:
            m = re.match(pattern, question)
            if m:
                ticker = m.group(1)
                if metric == "revenue_trend":
                    # Get last 4 quarters' revenue
                    df = self.metrics_service.get_historical_metrics(ticker, "revenue")
                    if df.empty:
                        return {"answer": f"No revenue data found for {ticker}.", "sources": ["SQL metrics"]}
                    df = df.sort_values("filing_date", ascending=False).head(4)
                    trend = ", ".join([f"{row['filing_date'].strftime('%Y-%m-%d')}: ${row['value']:,.2f}" for _, row in df.iterrows()])
                    return {"answer": f"Revenue trend for {ticker} (last 4 quarters): {trend}", "sources": ["SQL metrics"]}
                else:
                    # Find the latest filing_id for the ticker and filing_type
                    cursor = self.sql_storage.conn.cursor()
                    cursor.execute("""
                        SELECT id, filing_id FROM filings
                        WHERE ticker = ? AND filing_type = ?
                        ORDER BY filing_date DESC LIMIT 1
                    """, (ticker, filing_type))
                    row = cursor.fetchone()
                    if not row:
                        return {"answer": f"No {filing_type} filing found for {ticker}.", "sources": ["SQL metrics"]}
                    filing_db_id, filing_id = row
                    metrics = self.metrics_service.get_filing_metrics(ticker, filing_type, filing_id)
                    if not metrics:
                        return {"answer": f"No metrics found for {ticker} in the latest {filing_type} filing.", "sources": ["SQL metrics"]}
                    if metric == "revenue":
                        return {"answer": f"{ticker}'s total revenue in the latest {filing_type} filing is {metrics.get('revenue', 'N/A')}", "sources": ["SQL metrics"]}
                    if metric == "net_income":
                        return {"answer": f"{ticker}'s net income in the latest {filing_type} filing is {metrics.get('net_income', 'N/A')}", "sources": ["SQL metrics"]}
                    if metric == "assets_liabilities":
                        return {"answer": f"{ticker}'s total assets: {metrics.get('total_assets', 'N/A')}, total liabilities: {metrics.get('total_liabilities', 'N/A')} (latest {filing_type})", "sources": ["SQL metrics"]}
                    if metric == "shareholders_equity":
                        return {"answer": f"{ticker}'s shareholders' equity in the latest {filing_type} filing is {metrics.get('shareholders_equity', 'N/A')}", "sources": ["SQL metrics"]}
        # Fallback: use the chatbot/LLM pipeline
        response = self.chatbot_service.query(question)
        if "answer" in response:
            response["sources"] = [
                "Retrieved from vector embeddings",
                "Based on SEC filing data"
            ]
            logger.info(f"Generated answer with sources")
        else:
            logger.error("Failed to generate answer")
            response = {"answer": "Sorry, I couldn't process your question.", "sources": []}
        return response