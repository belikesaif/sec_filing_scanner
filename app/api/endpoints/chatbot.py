from pydantic import BaseModel
from app.utils.logger import setup_logger
from fastapi import APIRouter, HTTPException
from app.services.chatbot import ChatbotService

router = APIRouter()
logger = setup_logger(__name__)

# Instantiate the updated ChatbotService
chatbot_service = ChatbotService()

class ChatRequest(BaseModel):
    question: str

@router.post("/")
async def ask_chatbot(request: ChatRequest):
    try:
        result = chatbot_service.query(request.question)
        logger.info(f"Answered question: {request.question}")
        return result
    except Exception as e:
        logger.error(f"Error in chatbot endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
