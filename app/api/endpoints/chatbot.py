from pydantic import BaseModel
from app.utils.logger import setup_logger
from fastapi import APIRouter, HTTPException
from app.services.chatbot import ChatbotService

router = APIRouter()
logger = setup_logger(__name__)

class ChatRequest(BaseModel):
    question: str

# Service instance holder
_chatbot_service = None

def get_chatbot_service():
    global _chatbot_service
    if _chatbot_service is None:
        _chatbot_service = ChatbotService()
    return _chatbot_service

@router.post("/")
async def ask_chatbot(request: ChatRequest):
    try:
        service = get_chatbot_service()
        result = service.query(request.question)
        logger.info(f"Answered question: {request.question}")
        return result
    except Exception as e:
        logger.error(f"Error in chatbot endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
