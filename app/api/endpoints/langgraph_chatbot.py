# app/api/endpoints/langgraph_chatbot.py
from pydantic import BaseModel
from app.utils.logger import setup_logger
from fastapi import APIRouter, HTTPException
from app.services.langgraph_chatbot import LangGraphChatbotService
#=====================================================================================================================================================
logger = setup_logger(__name__)
router = APIRouter()
#=====================================================================================================================================================
# Instantiate the LangGraphChatbotService
langgraph_service = LangGraphChatbotService()
#=====================================================================================================================================================
class LangGraphChatRequest(BaseModel):
    question: str
#=====================================================================================================================================================
@router.post("/")
async def ask_langgraph_chatbot(request: LangGraphChatRequest):
    try:
        response = langgraph_service.query(request.question)
        return {"response": response}
    except Exception as e:
        logger.error(f"Error in LangGraph chatbot endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
