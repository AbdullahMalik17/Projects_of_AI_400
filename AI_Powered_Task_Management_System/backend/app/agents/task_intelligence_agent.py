"""
Task Intelligence Agent using OpenAI Agent SDK with Gemini.

Provides intelligent task analysis, priority suggestions, and
productivity insights using ReAct pattern with LiteLLM for Gemini integration.
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from openai_agents import Agent, function_tool

from app.core.config import settings
from app.models.task import Task, Priority, TaskStatus


class TaskIntelligenceAgent:
    """
    AI agent for task intelligence using OpenAI Agent SDK with Gemini via LiteLLM.

    Provides intelligent analysis of tasks, priority suggestions,
    productivity insights, and context-aware recommendations.
    """

    def __init__(self):
        """Initialize the Task Intelligence Agent with Gemini via LiteLLM."""
        # Configure LiteLLM for Gemini
        os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY

        # Define tools for the agent
        self.tools = [
            self._create_priority_analysis_tool(),
            self._create_time_estimation_tool(),
            self._create_productivity_insight_tool(),
        ]

        # Create agent with Gemini model via LiteLLM
        self.agent = Agent(
            model=settings.AGENT_MODEL,  # "litellm/gemini/gemini-2.0-flash-exp"
            instructions=self._get_agent_instructions(),
            tools=self.tools,
            temperature=settings.AGENT_TEMPERATURE,
        )

    def _get_agent_instructions(self) -> str:
        """Get system instructions for the agent."""
        return """You are an intelligent task management assistant specialized in analyzing tasks
        and providing actionable insights to improve productivity.

        Your capabilities:
        1. Analyze task attributes (title, description, due date) to suggest optimal priorities
        2. Estimate realistic time requirements for task completion
        3. Provide productivity insights based on task patterns and user behavior
        4. Identify task dependencies and suggest optimal scheduling

        Guidelines:
        - Be concise and actionable in your recommendations
        - Consider context like due dates, task complexity, and user patterns
        - Prioritize clarity over complexity
        - Base suggestions on logical reasoning about task attributes
        """

    def _create_priority_analysis_tool(self):
        """Create tool for priority analysis."""
        @function_tool
        def analyze_task_priority(
            task_title: str,
            task_description: str,
            due_date: Optional[str] = None,
            user_context: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Analyze task and suggest appropriate priority level.

            Args:
                task_title: Title of the task
                task_description: Detailed description
                due_date: ISO format due date (optional)
                user_context: Additional context about user patterns (optional)

            Returns:
                Dictionary with suggested priority and reasoning
            """
            reasoning = []

            # Analyze due date urgency
            if due_date:
                try:
                    due = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                    hours_until_due = (due - datetime.utcnow()).total_seconds() / 3600

                    if hours_until_due < 24:
                        reasoning.append("Due within 24 hours - urgent")
                        suggested_priority = "high"
                    elif hours_until_due < 72:
                        reasoning.append("Due within 3 days - moderately urgent")
                        suggested_priority = "medium"
                    else:
                        reasoning.append("Due date is not immediate")
                        suggested_priority = "medium"
                except:
                    suggested_priority = "medium"
                    reasoning.append("Unable to parse due date")
            else:
                suggested_priority = "medium"
                reasoning.append("No due date specified")

            # Analyze title and description for urgency keywords
            text = f"{task_title} {task_description}".lower()
            urgency_keywords = [
                "urgent", "asap", "immediately", "critical", "deadline",
                "emergency", "important", "priority"
            ]

            if any(keyword in text for keyword in urgency_keywords):
                reasoning.append("Contains urgency keywords")
                if suggested_priority != "high":
                    suggested_priority = "high"

            return {
                "suggested_priority": suggested_priority,
                "reasoning": reasoning,
                "confidence": "high" if len(reasoning) > 1 else "medium"
            }

        return analyze_task_priority

    def _create_time_estimation_tool(self):
        """Create tool for time estimation."""
        @function_tool
        def estimate_task_duration(
            task_title: str,
            task_description: str,
            task_type: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Estimate realistic time required to complete task.

            Args:
                task_title: Title of the task
                task_description: Detailed description
                task_type: Type of task (meeting, coding, writing, etc.)

            Returns:
                Dictionary with estimated duration and breakdown
            """
            # Simple heuristic-based estimation
            # In production, this would use ML models trained on historical data

            text = f"{task_title} {task_description}".lower()

            # Default estimates by task type
            type_estimates = {
                "meeting": 60,
                "call": 30,
                "email": 15,
                "report": 120,
                "analysis": 120,
                "research": 180,
                "review": 45,
                "planning": 60,
            }

            # Check for task type keywords
            estimated_minutes = 60  # default
            task_category = "general"

            for task_type, duration in type_estimates.items():
                if task_type in text:
                    estimated_minutes = duration
                    task_category = task_type
                    break

            # Adjust based on description length (proxy for complexity)
            if len(task_description) > 200:
                estimated_minutes = int(estimated_minutes * 1.5)
                complexity = "high"
            elif len(task_description) > 100:
                estimated_minutes = int(estimated_minutes * 1.2)
                complexity = "medium"
            else:
                complexity = "low"

            return {
                "estimated_duration_minutes": estimated_minutes,
                "task_category": task_category,
                "complexity": complexity,
                "breakdown": {
                    "preparation": int(estimated_minutes * 0.2),
                    "execution": int(estimated_minutes * 0.6),
                    "review": int(estimated_minutes * 0.2),
                }
            }

        return estimate_task_duration

    def _create_productivity_insight_tool(self):
        """Create tool for productivity insights."""
        @function_tool
        def generate_productivity_insight(
            completed_tasks: int,
            pending_tasks: int,
            overdue_tasks: int,
            avg_completion_time: Optional[float] = None
        ) -> Dict[str, Any]:
            """
            Generate productivity insights based on task statistics.

            Args:
                completed_tasks: Number of completed tasks
                pending_tasks: Number of pending tasks
                overdue_tasks: Number of overdue tasks
                avg_completion_time: Average time to complete tasks in minutes

            Returns:
                Dictionary with insights and recommendations
            """
            insights = []
            recommendations = []

            total_tasks = completed_tasks + pending_tasks + overdue_tasks

            if total_tasks == 0:
                return {
                    "insights": ["No tasks to analyze yet"],
                    "recommendations": ["Start by creating your first task!"],
                    "productivity_score": 0
                }

            # Calculate completion rate
            completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0

            # Analyze completion rate
            if completion_rate >= 80:
                insights.append(f"Excellent completion rate: {completion_rate:.1f}%")
                productivity_score = 90
            elif completion_rate >= 60:
                insights.append(f"Good completion rate: {completion_rate:.1f}%")
                productivity_score = 75
            elif completion_rate >= 40:
                insights.append(f"Moderate completion rate: {completion_rate:.1f}%")
                productivity_score = 60
                recommendations.append("Consider breaking down large tasks into smaller ones")
            else:
                insights.append(f"Low completion rate: {completion_rate:.1f}%")
                productivity_score = 40
                recommendations.append("Focus on completing existing tasks before adding new ones")

            # Analyze overdue tasks
            if overdue_tasks > 0:
                overdue_rate = (overdue_tasks / total_tasks) * 100
                insights.append(f"{overdue_tasks} overdue tasks ({overdue_rate:.1f}%)")

                if overdue_rate > 20:
                    recommendations.append("Review and reschedule overdue tasks")
                    productivity_score -= 15

            # Analyze pending workload
            if pending_tasks > completed_tasks * 2:
                insights.append("High pending task backlog")
                recommendations.append("Consider delegating or deferring lower-priority tasks")
                productivity_score -= 10

            return {
                "insights": insights,
                "recommendations": recommendations,
                "productivity_score": max(0, min(100, productivity_score)),
                "completion_rate": round(completion_rate, 1)
            }

        return generate_productivity_insight

    async def analyze_task(
        self,
        task: Task,
        user_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Analyze a task and provide intelligent insights.

        Args:
            task: Task to analyze
            user_context: Optional user context and patterns

        Returns:
            Dictionary with analysis results and recommendations
        """
        context_str = ""
        if user_context:
            context_str = f"\nUser Context: {user_context}"

        prompt = f"""Analyze this task and provide insights:

Task: {task.title}
Description: {task.description or 'No description'}
Current Priority: {task.priority.value}
Due Date: {task.due_date.isoformat() if task.due_date else 'Not set'}
{context_str}

Please:
1. Suggest appropriate priority using the analyze_task_priority tool
2. Estimate time required using the estimate_task_duration tool
3. Provide any additional recommendations
"""

        # Run agent
        result = await self.agent.run(prompt)

        return {
            "analysis": result.content,
            "suggested_priority": None,  # Extracted from tool calls
            "estimated_duration": None,  # Extracted from tool calls
        }

    async def get_productivity_insights(
        self,
        task_statistics: Dict[str, int]
    ) -> Dict[str, Any]:
        """
        Generate productivity insights from task statistics.

        Args:
            task_statistics: Dictionary with task counts

        Returns:
            Dictionary with insights and recommendations
        """
        prompt = f"""Analyze these task statistics and provide productivity insights:

Completed Tasks: {task_statistics.get('completed', 0)}
Pending Tasks: {task_statistics.get('todo', 0)} + {task_statistics.get('in_progress', 0)}
Overdue Tasks: {task_statistics.get('overdue', 0)}
Total Tasks: {task_statistics.get('total', 0)}

Use the generate_productivity_insight tool to analyze these metrics and provide:
1. Key insights about productivity patterns
2. Actionable recommendations for improvement
3. Overall productivity score
"""

        result = await self.agent.run(prompt)

        return {
            "insights": result.content,
            "tool_results": result.tool_calls if hasattr(result, 'tool_calls') else []
        }

    async def suggest_task_breakdown(
        self,
        task_title: str,
        task_description: str
    ) -> List[str]:
        """
        Suggest subtasks for breaking down a complex task.

        Args:
            task_title: Title of the task to break down
            task_description: Detailed description

        Returns:
            List of suggested subtask titles
        """
        prompt = f"""Break down this complex task into 3-7 manageable subtasks:

Task: {task_title}
Description: {task_description}

Provide a list of clear, actionable subtasks that:
- Are specific and measurable
- Follow a logical sequence
- Can be completed independently
- Cover all aspects of the main task

Format: Return each subtask as a simple bullet point.
"""

        result = await self.agent.run(prompt)

        # Parse subtasks from response
        # Simple parsing - in production, use structured output
        lines = result.content.split('\n')
        subtasks = []

        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                # Clean up the line
                clean_line = line.lstrip('-•0123456789. ').strip()
                if clean_line:
                    subtasks.append(clean_line)

        return subtasks[:7]  # Limit to 7 subtasks


# Singleton instance
task_intelligence_agent = TaskIntelligenceAgent()
