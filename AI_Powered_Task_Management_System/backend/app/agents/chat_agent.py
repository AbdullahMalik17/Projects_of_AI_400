"""
Chat Agent for conversational task management.

Handles user conversations, interprets intent, and executes actions
on the task database (querying, creating, updating).
"""

import json
from typing import Dict, List, Optional, Any
from google.generativeai import GenerativeModel
import google.generativeai as genai
from sqlmodel import Session

from app.core.config import settings
from app.services.task_service import TaskService
from app.schemas.task import TaskStatus, Priority
from app.agents.context_manager import ContextManager

class ChatAgent:
    """
    AI agent for conversational interactions.
    """

    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = GenerativeModel(
            model_name=settings.GEMINI_MODEL_NAME,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "max_output_tokens": 1024,
            },
        )

    async def process_message(
        self,
        message: str,
        context_manager: ContextManager,
        task_service: TaskService,
        user_id: int
    ) -> str:
        """
        Process a user message and return a response.
        """
        # 1. Get Context
        history = context_manager.get_conversation_context()
        
        # 2. Get recent tasks for context
        recent_tasks = task_service.list_tasks(user_id=user_id, limit=5)
        task_context = "\n".join([f"- {t.title} ({t.status.value}, {t.priority.value})" for t in recent_tasks])
        
        system_prompt = f"""
        # ROLE & PERSONA
        You are 'TaskMaster AI', an intelligent, proactive, and friendly productivity assistant. Your goal is to help users organize their life, manage tasks, and boost productivity. You are professional but conversational.

        # CONTEXT
        ## Recent Tasks (from Database):
        {task_context if task_context else "No recent tasks found."}

        ## Conversation History:
        {history}

        # CAPABILITIES & GUIDELINES
        1. **Task Queries:** 
           - If the user asks "What do I have to do?", summarize their recent tasks by priority and status.
           - Highlight high-priority or overdue items first.
        
        2. **Task Creation:**
           - If the user wants to add a task (e.g., "Add buy milk"), acknowledge it and explicitly confirm you understand the details (Title, Priority, Due Date). 
           - *Note: You cannot directly write to the DB yet, so ask them to use the 'Natural Language' input above or confirm you would if you could.* (For this version, guide them to the UI).
           
        3. **Advice & Coaching:**
           - Provide productivity tips if asked.
           - If a user seems overwhelmed (many high-priority tasks), suggest breaking them down or taking a break.

        4. **Tone & Style:**
           - Be concise. Do not ramble.
           - Use formatting (bullet points) for lists.
           - Be encouraging.

        # USER INPUT
        "{message}"

        # RESPONSE
        Provide a helpful, context-aware response acting as TaskMaster AI.
        """

        # For a true agent, we'd use function calling (tools). 
        # For this enhancement, we'll start with a smart responder that has access to data.
        # If the user explicitly asks to create/update, we might need a more complex loop.
        # Let's keep it as a RAG-style chat for now: It sees the tasks and talks about them.
        
        response = await self.model.generate_content_async(system_prompt)
        return response.text

chat_agent = ChatAgent()

