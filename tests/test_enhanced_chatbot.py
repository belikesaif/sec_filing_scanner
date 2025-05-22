import pytest
from unittest.mock import MagicMock, patch
from app.services.langgraph_chatbot import EnhancedChatbotService, SQLRetriever
from langchain_core.documents import Document

@pytest.fixture
def mock_sql_storage():
    storage = MagicMock()
    storage.get_filing_metrics.return_value = [
        {
            "filing_id": 1,
            "filing_type": "10-K",
            "filing_date": "2025-01-01",
            "metric_name": "revenue",
            "value": 1000000000.0,
            "unit": "USD",
            "scale": "normalized"
        }
    ]
    return storage

@pytest.fixture
def mock_vector_store():
    store = MagicMock()
    store.as_retriever.return_value.get_relevant_documents.return_value = [
        Document(
            page_content="Sample filing content about revenue growth.",
            metadata={"source": "test_filing.html"}
        )
    ]
    return store

def test_sql_retriever(mock_sql_storage):
    """Test the SQL retriever's document conversion."""
    retriever = SQLRetriever(mock_sql_storage)
    docs = retriever.get_relevant_documents("What was the revenue?")
    
    assert len(docs) == 1
    assert "revenue was 1000000000.0 USD" in docs[0].page_content
    assert docs[0].metadata["filing_type"] == "10-K"

@patch('app.services.langgraph_chatbot.Chroma')
@patch('app.services.langgraph_chatbot.ChatOpenAI')
@patch('app.services.langgraph_chatbot.SQLStorage')
def test_enhanced_chatbot(mock_sql_storage_cls, mock_chat_openai, mock_chroma, mock_vector_store):
    """Test the enhanced chatbot's query processing."""
    # Set up mocks
    mock_sql_storage_cls.return_value = mock_sql_storage()
    mock_chroma.return_value = mock_vector_store
    mock_chat_openai.return_value.invoke.return_value = "Test answer about revenue."
    
    # Create chatbot instance
    chatbot = EnhancedChatbotService()
    
    # Test query
    response = chatbot.query("What was the company's revenue?")
    
    assert "answer" in response
    assert isinstance(response["answer"], str)
    assert "error" not in response

@patch('app.services.langgraph_chatbot.Chroma')
@patch('app.services.langgraph_chatbot.ChatOpenAI')
@patch('app.services.langgraph_chatbot.SQLStorage')
def test_enhanced_chatbot_error_handling(mock_sql_storage_cls, mock_chat_openai, mock_chroma):
    """Test error handling in the enhanced chatbot."""
    # Set up mocks to raise an exception
    mock_chat_openai.return_value.invoke.side_effect = Exception("Test error")
    
    # Create chatbot instance
    chatbot = EnhancedChatbotService()
    
    # Test query
    response = chatbot.query("What was the revenue?")
    
    assert "error" in response
    assert "Test error" in response["error"]

def test_context_combination():
    """Test the combination of SQL and vector store results."""
    # Create a chatbot instance with mocked components
    chatbot = EnhancedChatbotService()
    
    # Replace retrievers with mocks
    chatbot.sql_retriever = MagicMock()
    chatbot.vector_store.as_retriever = MagicMock()
    
    # Set up mock returns
    chatbot.sql_retriever.get_relevant_documents.return_value = [
        Document(page_content="SQL Metric: Revenue $100M")
    ]
    chatbot.vector_store.as_retriever.return_value.get_relevant_documents.return_value = [
        Document(page_content="Filing text about revenue growth")
    ]
    
    # Get combined context
    context = chatbot._get_context("test query")
    
    # Verify both sources are included
    assert "Financial Metrics:" in context
    assert "Filing Content:" in context
    assert "Revenue $100M" in context
    assert "revenue growth" in context
