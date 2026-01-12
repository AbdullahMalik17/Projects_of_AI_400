"""
Task Intelligence Agent using Google Gemini API directly.

Provides intelligent task analysis, priority suggestions, and
productivity insights using Gemini's natural language capabilities.
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from google.generativeai import GenerativeModel
import google.generativeai as genai

from app.core.config import settings
from app.models.task import Task, Priority, TaskStatus


class TaskIntelligenceAgent:
    """
    AI agent for task intelligence using Google Gemini API.

    Provides intelligent analysis of tasks, priority suggestions,
    productivity insights, and context-aware recommendations.
    """

    def __init__(self):
        """Initialize the Task Intelligence Agent with Gemini."""
        genai.configure(api_key=settings.GEMINI_API_KEY)

        self.model = GenerativeModel(
            model_name=settings.GEMINI_MODEL_NAME,
            generation_config={
                "temperature": settings.AI_TEMPERATURE,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": settings.AI_MAX_TOKENS,
                "response_mime_type": "application/json",
            },
        )

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
        prompt = f"""Analyze this task and provide insights:

Task Title: {task.title}
Description: {task.description or 'No description'}
Current Priority: {task.priority.value}
Due Date: {task.due_date.isoformat() if task.due_date else 'Not set'}
Status: {task.status.value}

Provide a JSON response with:
- suggested_priority: "low", "medium", or "high"
- estimated_duration_minutes: estimated time to complete (number)
- complexity: "low", "medium", or "high"
- recommendations: array of 2-3 actionable recommendations
- reasoning: brief explanation of your analysis

Be concise and practical."""

        try:
            response = await self.model.generate_content_async(prompt)
            analysis = json.loads(response.text)

            return {
                "analysis": analysis,
                "suggested_priority": analysis.get("suggested_priority"),
                "estimated_duration": analysis.get("estimated_duration_minutes"),
            }
        except Exception as e:
            print(f"Analysis failed: {e}. Using fallback.")
            return self._fallback_analysis(task)

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

Statistics:
- Total Tasks: {task_statistics.get('total', 0)}
- Completed: {task_statistics.get('completed', 0)}
- In Progress: {task_statistics.get('in_progress', 0)}
- Todo: {task_statistics.get('todo', 0)}
- Overdue: {task_statistics.get('overdue', 0)}
- Completion Rate: {task_statistics.get('completion_rate', 0)}%

Provide a JSON response with:
- productivity_score: number between 0-100
- insights: array of 2-3 key observations
- recommendations: array of 2-3 actionable suggestions
- trend: "improving", "stable", or "declining"

Be encouraging but honest."""

        try:
            response = await self.model.generate_content_async(prompt)
            insights = json.loads(response.text)

            return {
                "insights": insights.get("insights", []),
                "recommendations": insights.get("recommendations", []),
                "productivity_score": insights.get("productivity_score", 50),
                "trend": insights.get("trend", "stable")
            }
        except Exception as e:
            print(f"Insights generation failed: {e}. Using fallback.")
            return self._fallback_insights(task_statistics)

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

Provide a JSON array of subtask titles. Each subtask should be:
- Specific and actionable
- Independent (can be done separately)
- Clear and concise (max 10 words)
- Following a logical sequence

Example format: ["Research requirements", "Create draft outline", "Write first section"]

Return only the JSON array, nothing else."""

        try:
            response = await self.model.generate_content_async(prompt)
            subtasks = json.loads(response.text)

            if isinstance(subtasks, list):
                return subtasks[:7]  # Limit to 7
            return []
        except Exception as e:
            print(f"Task breakdown failed: {e}. Using fallback.")
            return self._fallback_breakdown(task_title)

    def _fallback_analysis(self, task: Task) -> Dict[str, Any]:
        """Fallback analysis when AI fails."""
        # Simple rule-based analysis
        priority = "medium"
        if task.due_date:
            days_until_due = (task.due_date - datetime.utcnow()).days
            if days_until_due <= 1:
                priority = "high"
            elif days_until_due > 7:
                priority = "low"

        return {
            "analysis": {
                "suggested_priority": priority,
                "estimated_duration_minutes": 60,
                "complexity": "medium",
                "recommendations": [
                    "Break down into smaller subtasks",
                    "Set a specific due date if not set"
                ],
                "reasoning": "Based on due date analysis"
            },
            "suggested_priority": priority,
            "estimated_duration": 60
        }

    def _fallback_insights(self, stats: Dict[str, int]) -> Dict[str, Any]:
        """Fallback insights when AI fails."""
        completion_rate = stats.get('completion_rate', 0)

        if completion_rate >= 70:
            score = 80
            insights = ["Good task completion rate"]
            recommendations = ["Keep up the good work"]
        elif completion_rate >= 40:
            score = 60
            insights = ["Moderate completion rate"]
            recommendations = ["Focus on completing existing tasks"]
        else:
            score = 40
            insights = ["Low completion rate"]
            recommendations = ["Consider reducing task load", "Break tasks into smaller pieces"]

        return {
            "insights": insights,
            "recommendations": recommendations,
            "productivity_score": score,
            "trend": "stable"
        }

    def _fallback_breakdown(self, task_title: str) -> List[str]:
        """Fallback task breakdown when AI fails."""
        return [
            f"Plan {task_title}",
            f"Execute {task_title}",
            f"Review {task_title}"
        ]


# Singleton instance
task_intelligence_agent = TaskIntelligenceAgent()
