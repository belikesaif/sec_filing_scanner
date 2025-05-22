# app/services/langgraph_chatbot.py
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

import os
from typing import Dict, List, Any, Optional, TypedDict
from datetime import datetime
import re
from functools import lru_cache

import openai
from sqlalchemy import text

from app.services.sql_storage import SQLStorage
from app.services.chatbot import ChatbotService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Debug log to check environment variables
logger.info("Current environment variables:")
logger.info(f"OPENAI_API_KEY exists: {bool(os.getenv('OPENAI_API_KEY'))}")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f".env file exists: {os.path.exists(os.path.join(os.getcwd(), '.env'))}")

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    logger.error("OPENAI_API_KEY is not set in the environment.")
    raise ValueError("OPENAI_API_KEY is required")
openai.api_key = openai_api_key

def sql_query_tool(question: str) -> str:
    """
    Tool to query the structured SEC filing data from the SQLite database.
    For simplicity, we assume the natural language question is a valid SQL query.
    In a real implementation, you might translate the question into SQL.
    """
    storage = SQLStorage()
    with storage.session_scope() as session:
        try:
            result = session.execute(text(question))
            rows = result.fetchall()
            result = "\n".join([str(row) for row in rows])
            logger.info(f"SQL query executed successfully. Result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error executing SQL query: {str(e)}")
            return f"Error: {str(e)}"

class EnhancedChatbotService:
    def __init__(self):
        self.storage = SQLStorage()

    def get_response(self, question: str, ticker: Optional[str] = None) -> Dict[str, Any]:
        """Get a response from the chatbot by converting NL to SQL, executing, then summarizing."""
        try:
            # Step 1: Convert Natural Language to SQL query using LLM
            nl_to_sql_system_prompt = """
Given the database schema and a user question, generate an SQLite query to answer the question. If the question cannot be answered with SQL or is unclear, respond with 'NO_SQL_POSSIBLE'.
Database Schema:
- Table: Filing (columns: id INTEGER PRIMARY KEY, ticker TEXT, filing_type TEXT, filing_date TIMESTAMP, accession_number TEXT, file_path TEXT, full_text TEXT, processed_at TIMESTAMP)
  Description: Stores information about SEC filings.
- Table: Metric (columns: id INTEGER PRIMARY KEY, filing_id INTEGER, metric_name TEXT, value REAL, unit TEXT, scale TEXT, raw_value TEXT, extracted_from TEXT, FOREIGN KEY(filing_id) REFERENCES Filing(id))
  Description: Stores extracted financial metrics for each filing.

Common metric_name values: 'revenue', 'net_income', 'total_assets', 'total_liabilities', 'shareholders_equity'.
filing_type is typically '10-K' (annual) or '10-Q' (quarterly).
filing_date is a TIMESTAMP, query it like a string 'YYYY-MM-DD HH:MM:SS.ffffff' or use SQLite date functions.
For "last quarter" or "latest quarter", typically look for the most recent '10-Q' filing.
For "last year" or "latest annual", typically look for the most recent '10-K' filing.
Always try to provide the most recent data unless specified otherwise.
Ensure the SQL is valid SQLite syntax.
"""
            user_prompt_for_sql = f"User Question: \"{question}\""
            if ticker:
                user_prompt_for_sql += f"\nFocus on ticker: {ticker}. Ensure the SQL query filters by this ticker (e.g., f.ticker = '{ticker}')."
            user_prompt_for_sql += "\nGenerated SQLite Query:"

            messages_for_sql = [
                {"role": "system", "content": nl_to_sql_system_prompt},
                {"role": "user", "content": user_prompt_for_sql}
            ]

            logger.info(f"Attempting to generate SQL for question: {question}, ticker: {ticker}")
            sql_generation_response = openai.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages_for_sql,
                temperature=0.0,
                max_tokens=300 # Allow enough tokens for a complex query
            )
            generated_sql = sql_generation_response.choices[0].message.content.strip()
            logger.info(f"Generated SQL: {generated_sql}")

            if "NO_SQL_POSSIBLE" in generated_sql or not generated_sql.upper().startswith("SELECT"):
                logger.warning(f"LLM indicated no SQL possible or invalid SQL for question: {question}. Generated: {generated_sql}")
                # Fallback to a general LLM response if SQL is not appropriate or generation failed
                general_response_messages = [
                    {"role": "system", "content": "You are a helpful AI assistant. If you cannot answer a question using provided context, say so clearly."},
                    {"role": "user", "content": question}
                ]
                general_response = openai.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=general_response_messages,
                    temperature=0.1
                )
                return {"answer": general_response.choices[0].message.content, "sources": []}

            # Step 2: Execute the generated SQL query
            sql_result_str = sql_query_tool(generated_sql)
            logger.info(f"SQL execution result: {sql_result_str}")

            # Step 3: Summarize the SQL result using LLM
            summarize_system_prompt = """
You are an AI assistant. Given a user's question, the SQL query used to answer it, and the result of that SQL query, provide a concise, natural language answer to the user.
If the SQL result indicates an error or is empty, state that the information could not be found or there was an issue retrieving it.
Do not show the SQL query in your answer unless the question was about the query itself.
"""
            user_prompt_for_summary = f"Original Question: \"{question}\"\nExecuted SQL Query: \n```sql\n{generated_sql}\n```\nSQL Query Result:\n```\n{sql_result_str}\n```\nProvide a natural language answer:"

            messages_for_summary = [
                {"role": "system", "content": summarize_system_prompt},
                {"role": "user", "content": user_prompt_for_summary}
            ]

            summary_response = openai.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages_for_summary,
                temperature=0.1
            )
            final_answer = summary_response.choices[0].message.content

            # Basic source attribution if data was found
            sources = []
            if sql_result_str and not sql_result_str.startswith("Error:") and sql_result_str.lower() != "none" and sql_result_str.strip() != "":
                sources.append({"type": "database_query", "query": generated_sql, "details": "Retrieved from SEC filing data"})

            return {"answer": final_answer, "sources": sources}

        except openai.APIError as e:
            logger.error(f"OpenAI API error in chatbot service: {str(e)}")
            return {"error": f"There was an issue with the AI service (API Error): {str(e)}"}
        except Exception as e:
            logger.error(f"Error getting chatbot response: {str(e)}", exc_info=True)
            return {"error": f"I encountered an unexpected error in the chatbot service: {str(e)}"}
