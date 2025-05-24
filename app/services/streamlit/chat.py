# app/services/streamlit/chat.py
import os
from app.services.chatbot import ChatbotService
from app.services.sql_storage import SQLStorage
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class ChatService:
    def __init__(self):
        """Initialize the chat service that combines SQL and vector search results."""
        self.chatbot_service = ChatbotService()
        self.sql_storage = SQLStorage()
        logger.info("ChatService initialized successfully.")
    
    def get_answer(self, question: str) -> dict:
        """Process a user question and return an answer with sources.
        
        Args:
            question: The user's question about SEC filings
            
        Returns:
            dict: Contains the answer and sources used
        """
        logger.info(f"Processing question: {question}")
        
        # Get answer from the chatbot service (which uses vector search)
        response = self.chatbot_service.query(question)
        
        # Extract filing information from the SQL database if needed
        # This is a simplified implementation - in a real system, we would use
        # a more sophisticated approach to determine when to query SQL vs. vector search
        
        # For demonstration purposes, we'll just add some source information
        if "answer" in response:
            # Add sources information (in a real implementation, this would come from the vector search results)
            response["sources"] = [
                "Retrieved from vector embeddings",
                "Based on SEC filing data"
            ]
            
            logger.info(f"Generated answer with sources")
        else:
            logger.error("Failed to generate answer")
            response = {"answer": "Sorry, I couldn't process your question.", "sources": []}
        
        return response