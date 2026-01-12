"""
Database Agent using ReAct pattern to interact with the database.
"""

import json
import re
from typing import List, Dict, Any, Optional
from google.generativeai import GenerativeModel
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, GoogleAPIError
from app.core.config import settings
from app.agents.tools import AgentTools

class DatabaseAgent:
    def __init__(self, tools: AgentTools):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = GenerativeModel(
            model_name=settings.GEMINI_MODEL_NAME,
            generation_config={
                "temperature": 0.1, # Low temperature for precise tool use
                "max_output_tokens": 1024,
            }
        )
        self.tools = tools
        self.tool_definitions = self._get_tool_definitions()

    def _get_tool_definitions(self) -> str:
        return """
        Available Tools:
        - list_tasks(status: str = None, limit: int = 10): List tasks. status can be 'todo', 'in_progress', 'completed'.
        - create_task(title: str, description: str = None, priority: str = 'medium', due_date: str = None): Create a task.
        - delete_task(task_id: int): Delete a task by ID.
        - complete_task(task_id: int): Mark a task as completed.
        - search_tasks(query: str): Search tasks by text.
        """

    async def run(self, user_input: str, history: Optional[List[Any]] = None) -> str:
        """
        Run the ReAct loop with conversation history.
        """
        # Convert history to format expected by Gemini
        messages = []
        if history:
            for msg in history:
                messages.append({
                    "role": "user" if msg.role == "user" else "model",
                    "parts": [msg.content]
                })
        
        # Add current user prompt
        messages.append({"role": "user", "parts": [self._build_system_prompt(user_input)]})
        
        max_turns = 5
        current_turn = 0

        while current_turn < max_turns:
            try:
                # Generate response from Gemini
                response = await self.model.generate_content_async(messages)
                response_text = response.text
            except ResourceExhausted:
                return "I'm currently hitting my rate limit with the AI provider. Please wait a minute and try again."
            except GoogleAPIError as e:
                return f"I encountered an error communicating with the AI service: {str(e)}"
            except Exception as e:
                return f"An unexpected error occurred: {str(e)}"
            
            # Print for debugging
            print(f"Agent Step {current_turn}: {response_text}")

            # Check if Agent wants to perform an Action via JSON block
            json_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
            
            if json_match:
                try:
                    action_data = json.loads(json_match.group(1))
                    tool_name = action_data.get("tool")
                    tool_args = action_data.get("args", {})
                    
                    if tool_name == "final_answer":
                        return tool_args.get("message", response_text)

                    # Execute Tool
                    observation = self._execute_tool(tool_name, tool_args)
                    
                    # Append observation to history
                    messages.append({"role": "model", "parts": [response_text]})
                    messages.append({"role": "user", "parts": [f"Observation: {observation}"]})
                    
                except Exception as e:
                    messages.append({"role": "model", "parts": [response_text]})
                    messages.append({"role": "user", "parts": [f"Observation: Error executing tool: {str(e)}"]})
            else:
                # No action detected, return response as is (assuming it's a direct answer or conversation)
                return response_text

            current_turn += 1
        
        return "I tried to help but reached my limit of steps."

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        try:
            method = getattr(self.tools, tool_name)
            result = method(**args)
            return json.dumps(result, default=str)
        except AttributeError:
            return f"Tool {tool_name} not found."
        except Exception as e:
            return f"Error: {str(e)}"

    def _build_system_prompt(self, user_input: str) -> str:
        return f"""
        You are a helpful task management assistant. You can access the user's database directly.
        
        {self.tool_definitions}
        
        To use a tool, output a JSON block like this:
        ```json
        {{
            "tool": "create_task",
            "args": {{
                "title": "Buy milk",
                "priority": "high"
            }}
        }}
        ```
        
        When you have completed the request or need to reply to the user, use the 'final_answer' tool:
        ```json
        {{
            "tool": "final_answer",
            "args": {{
                "message": "I have created the task for you."
            }}
        }}
        ```
        
        User Request: "{user_input}"
        """
