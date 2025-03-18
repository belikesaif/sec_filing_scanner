# app/services/langgraph_chatbot.py
import os 
import openai
from typing import TypedDict
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import ToolNode, create_react_agent
from app.services.sql_storage import SQLStorage
from app.services.chatbot import ChatbotService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    logger.error("OPENAI_API_KEY is not set in the environment.")
    raise ValueError("OPENAI_API_KEY is required")
openai.api_key = openai_api_key

# Define the state used by the agent
class ChatState(TypedDict):
    question: str
    sql_result: str
    embedding_result: str
    combined_answer: str

# Define our tool functions

def sql_query_tool(question: str) -> str:
    """
    Tool to query the structured SEC filing data from the SQLite database.
    For simplicity, we assume the natural language question is a valid SQL query.
    In a real implementation, you might translate the question into SQL.
    """
    storage = SQLStorage()
    conn = storage.conn
    cursor = conn.cursor()
    try:
        cursor.execute(question)
        rows = cursor.fetchall()
        result = str(rows)
        logger.info(f"SQL query executed successfully. Result: {result}")
        return result
    except Exception as e:
        logger.error(f"SQL query error: {e}")
        return f"Error executing query: {e}"

def embedding_tool(question: str) -> str:
    """
    Tool to retrieve context from SEC filings embeddings stored in ChromaDB.
    This wraps our existing ChatbotService.
    """
    chatbot_service = ChatbotService()
    result = chatbot_service.get_answer(question)
    return str(result)

def combine_results(state: ChatState, llm: init_chat_model) -> str:
    """
    Combines the outputs from the SQL and embeddings tools using the LLM.
    """
    combined_input = (
        f"Question: {state.get('question', '')}\n"
        f"SQL Result: {state.get('sql_result', '')}\n"
        f"Embeddings Result: {state.get('embedding_result', '')}\n"
        "Based on the above, provide a final, concise answer."
    )
    try:
        final_answer = llm(combined_input)
        logger.info(f"Combined answer: {final_answer}")
        return final_answer
    except Exception as e:
        logger.error(f"Error combining results: {e}")
        return f"Error combining results: {e}"

class LangGraphChatbotService:
    def __init__(self):
        # Initialize the chat-based LLM; ensure OPENAI_API_KEY is set.
        self.llm = init_chat_model("gpt-4", model_provider="openai")
        # Build tool nodes without the description keyword argument.
        self.sql_tool_node = ToolNode(
            name="SQL Query Tool",
            tool_func=sql_query_tool,
            input_key="question",
            output_key="sql_result"
        )
        self.embedding_tool_node = ToolNode(
            name="Embeddings Retrieval Tool",
            tool_func=embedding_tool,
            input_key="question",
            output_key="embedding_result"
        )
        
        # Build the composite agent using create_react_agent.
        self.agent = create_react_agent(
            llm=self.llm,
            tools=[self.sql_tool_node, self.embedding_tool_node],
            combine_func=lambda state: combine_results(state, self.llm)
        )
        logger.info("LangGraph Chatbot Service initialized using the stateful graph approach.")

    def query(self, question: str) -> str:
        # Initialize the state with the incoming question.
        initial_state: ChatState = {
            "question": question,
            "sql_result": "",
            "embedding_result": "",
            "combined_answer": ""
        }
        try:
            # Run the agent workflow; the agent updates the state with tool outputs and a final answer.
            result_state: ChatState = self.agent.run(initial_state)
            return result_state.get("combined_answer", "No answer produced.")
        except Exception as e:
            logger.error(f"Error in LangGraph chatbot query: {e}")
            return f"Error: {e}"
