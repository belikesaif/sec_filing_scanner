import os
import openai
from app.services.embedding import EmbeddingService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class ChatbotService:
    def __init__(self, collection_name: str = "filings_embeddings"):
        # Initialize the EmbeddingService to access our Chroma collection.
        self.embedding_service = EmbeddingService()
        self.collection = self.embedding_service.collection
        
        # Ensure the OpenAI API key is set (e.g., via environment variable)
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.error("OPENAI_API_KEY is not set in the environment.")
            raise ValueError("OPENAI_API_KEY is required")
        openai.api_key = openai_api_key
        
        logger.info("Simple ChatbotService initialized successfully without LangChain.")

    def query(self, question: str) -> dict:
        logger.info(f"Received query: {question}")
        # Generate an embedding for the question
        question_embedding = self.embedding_service.generate_embedding(question)
        if not question_embedding:
            logger.error("Failed to generate embedding for the question.")
            return {"answer": "Error generating question embedding."}
        logger.info("Generated embedding for question.")

        # Query the Chroma collection for similar documents
        try:
            results = self.collection.query(query_embeddings=[question_embedding], n_results=3)
            logger.info(f"Retrieved documents from vector store: {results}")
        except Exception as e:
            logger.error(f"Error querying vector store: {e}")
            results = {}

        # Construct context from retrieved documents
        context = ""
        if results and "documents" in results and results["documents"]:
            # results["documents"] is a list of lists (one per query), use the first query's results
            for doc in results["documents"][0]:
                context += doc + "\n\n"
        else:
            logger.warning("No documents retrieved from vector store; proceeding with empty context.")

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Using the following context, answer the question concisely.\n\nContext:\n{context}\nQuestion: {question}"}
        ]
        logger.info(f"Generated messages for API call.")


        # Call OpenAI API to generate an answer
        try:
            completion = openai.chat.completions.create(
                model="gpt-4o-2024-08-06", 
                messages=messages
            )
            response = completion.choices[0].message.content
            logger.info(f"Generated answer: {response}")
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            response = f"Error: {e}"
        
        return {"answer": response}