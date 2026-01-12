from fastapi import APIRouter, Depends, Body
from app.services.task_service import TaskService, get_task_service
from app.services.conversation_service import ConversationService
from app.core.database import get_session
from app.agents.tools import AgentTools
from app.agents.database_agent import DatabaseAgent
from app.schemas.response import APIResponse
from sqlmodel import Session

router = APIRouter(prefix="/chat", tags=["Chat"])

DEFAULT_USER_ID = 1

@router.post("", response_model=APIResponse[str])
async def chat_with_agent(
    message: str = Body(..., embed=True),
    task_service: TaskService = Depends(get_task_service),
    db_session: Session = Depends(get_session)
):
    """
    Chat with the Database Agent with multi-turn memory.
    """
    conv_service = ConversationService(db_session)
    
    # 1. Fetch recent history
    history = conv_service.get_history(DEFAULT_USER_ID, limit=10)
    
    # 2. Run Agent
    tools = AgentTools(task_service, DEFAULT_USER_ID)
    agent = DatabaseAgent(tools)
    response = await agent.run(message, history=list(history))
    
    # 3. Save conversation to DB
    conv_service.save_message(DEFAULT_USER_ID, "user", message)
    conv_service.save_message(DEFAULT_USER_ID, "assistant", response)
    
    return APIResponse(
        success=True,
        data=response,
        message="Agent processed request"
    )
