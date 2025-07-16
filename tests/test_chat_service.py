import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.streamlit.chat import ChatService
from app.services.chatbot import ChatbotService

class TestChatService(unittest.TestCase):
    def setUp(self):
        # Create test directories if they don't exist
        os.makedirs('data/db', exist_ok=True)
        os.makedirs('embeddings/chromadb', exist_ok=True)
        
        # Mock the ChatbotService to avoid actual API calls
        self.chatbot_service_patcher = patch('app.services.streamlit.chat.ChatbotService')
        self.mock_chatbot_service = self.chatbot_service_patcher.start()
        
        # Configure the mock to return a predefined response
        mock_instance = MagicMock()
        mock_instance.query.return_value = {"answer": "This is a test answer"}
        self.mock_chatbot_service.return_value = mock_instance
        
        # Initialize the chat service with the mocked dependencies
        self.chat_service = ChatService()
    
    def tearDown(self):
        self.chatbot_service_patcher.stop()
    
    def test_get_answer(self):
        """Test that the get_answer method returns the expected response"""
        response = self.chat_service.get_answer("Test question")
        
        # Verify the response structure
        self.assertIn("answer", response)
        self.assertEqual(response["answer"], "This is a test answer")
        self.assertIn("sources", response)
        self.assertTrue(isinstance(response["sources"], list))
    
    def test_error_handling(self):
        """Test error handling in the get_answer method"""
        # Configure the mock to raise an exception
        self.chat_service.chatbot_service.query.side_effect = Exception("Test error")
        
        # The method should handle the exception and return an error message
        response = self.chat_service.get_answer("Test question")
        self.assertIn("answer", response)
        self.assertIn("Sorry", response["answer"])
        self.assertIn("sources", response)
        self.assertEqual(len(response["sources"]), 0)

if __name__ == '__main__':
    unittest.main()