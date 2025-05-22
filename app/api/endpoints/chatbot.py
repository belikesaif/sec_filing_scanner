from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, validator
from typing import Optional
from app.services.langgraph_chatbot import EnhancedChatbotService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

# Singleton instance of the chatbot service
_chatbot_service = None

def get_chatbot_service():
    global _chatbot_service
    if _chatbot_service is None:
        _chatbot_service = EnhancedChatbotService()
    return _chatbot_service

class Question(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    ticker: Optional[str] = Field(None, pattern="^[A-Z]{1,5}$")
    
    @validator('text')
    def validate_question(cls, v):
        if not v.strip():
            raise ValueError("Question cannot be empty or just whitespace")
        return v.strip()

class Answer(BaseModel):
    answer: str
    sources: Optional[list] = None

@router.post("/ask", response_model=Answer)
async def ask_question(
    question: Question,
    chatbot: EnhancedChatbotService = Depends(get_chatbot_service)
):
    """
    Ask a question about SEC filings.
    The question will be processed using a hybrid retrieval system that combines:
    - Structured financial metrics from the SQL database
    - Relevant text passages from the vector store
    
    Parameters:
    - text: The question text
    - ticker: Optional stock ticker to filter results (e.g., "AAPL")
    """
    try:
        response = chatbot.query(
            question.text,
            ticker=question.ticker
        )
        
        if "error" in response:
            error_msg = response["error"]
            if "rate limit" in error_msg.lower():
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            elif "invalid api key" in error_msg.lower():
                raise HTTPException(status_code=401, detail="Authentication failed")
            else:
                raise HTTPException(status_code=500, detail=error_msg)
                
        return Answer(
            answer=response["answer"],
            sources=response.get("sources")
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing question: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while processing your request"
        )
