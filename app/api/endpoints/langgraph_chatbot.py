# app/api/endpoints/langgraph_chatbot.py
from pydantic import BaseModel
from app.utils.logger import setup_logger
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.services.langgraph_chatbot import EnhancedChatbotService
#=====================================================================================================================================================
logger = setup_logger(__name__)
router = APIRouter()
#=====================================================================================================================================================
# Instantiate the EnhancedChatbotService
chatbot_service = EnhancedChatbotService()
#=====================================================================================================================================================
class ChatRequest(BaseModel):
    question: str
#=====================================================================================================================================================
@router.post("/")
async def ask_chatbot(request: ChatRequest):
    try:
        response = chatbot_service.get_response(request.question)
        return {"response": response}
    except Exception as e:
        logger.error(f"Error in chatbot endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
