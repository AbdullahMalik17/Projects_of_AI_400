"""
Gemini AI Agent for natural language task parsing.

Parses user input in natural language and extracts structured task information
including title, description, due date, priority, and tags.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from google.generativeai import GenerativeModel
import google.generativeai as genai
from app.schemas.task import TaskCreate
from app.core.config import settings


class TaskParserAgent:
    """
    AI agent that uses Google Gemini to parse natural language task descriptions
    and extract structured task information.
    """

    def __init__(self):
        """Initialize the Gemini model for task parsing."""
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = GenerativeModel(
            model_name=settings.GEMINI_MODEL_NAME,
            generation_config={
                "temperature": 0.3,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 512,
                "response_mime_type": "application/json",
            },
        )

    async def parse_natural_language_task(self, user_input: str, user_context: Optional[Dict] = None) -> TaskCreate:
        """
        Parse natural language input and return a structured TaskCreate object.

        Args:
            user_input: Natural language description of the task
            user_context: Optional user context for personalized parsing

        Returns:
            TaskCreate object with extracted task information

        Example:
            Input: "Remind me to call John tomorrow at 2pm about the project"
            Output: TaskCreate(
                title="Call John about the project",
                description="Call John tomorrow at 2pm about the project",
                due_date=datetime(...),
                priority="medium",
                tags=["communication", "project"]
            )
        """
        # Prepare the prompt for Gemini
        prompt = self._build_parsing_prompt(user_input, user_context)

        try:
            response = await self.model.generate_content_async(prompt)

            # Parse the JSON response from Gemini
            parsed_data = self._parse_gemini_response(response.text)

            # Create and return TaskCreate object
            return TaskCreate(**parsed_data)

        except Exception as e:
            # Fallback to rule-based parsing if Gemini fails
            print(f"Gemini parsing failed: {e}. Falling back to rule-based parsing.")
            return self._rule_based_parse(user_input)

    def _build_parsing_prompt(self, user_input: str, user_context: Optional[Dict]) -> str:
        """
        Build the prompt for Gemini with context and examples.
        """
        context_str = ""
        if user_context:
            context_str = f"""
            User Context:
            - Work Hours: {user_context.get('work_hours', 'N/A')}
            - Preferred Priority: {user_context.get('default_priority', 'medium')}
            - Common Categories: {user_context.get('common_task_categories', [])}
            """

        prompt = f"""
        You are an intelligent task parsing assistant. Your job is to extract structured task information from natural language input.

        {context_str}

        Extract the following information:
        - title: Main task title (concise, actionable)
        - description: Full task description
        - due_date: ISO format date string (YYYY-MM-DDTHH:MM:SS) or null if no specific date mentioned
        - priority: "low", "medium", or "high" (default to "medium" if unclear)
        - tags: Array of relevant tags (2-5 tags max)
        - estimated_duration: Estimated duration in minutes (null if not specified)

        Examples:
        Input: "Remind me to call John tomorrow at 2pm about the project"
        Output: {{
            "title": "Call John about the project",
            "description": "Remind to call John tomorrow at 2pm about the project",
            "due_date": "{(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT14:00:00')}",
            "priority": "medium",
            "tags": ["communication", "project"],
            "estimated_duration": 30
        }}

        Input: "Finish the quarterly report by Friday"
        Output: {{
            "title": "Finish the quarterly report",
            "description": "Finish the quarterly report by Friday",
            "due_date": "{(datetime.now() + timedelta(days=(4-datetime.now().weekday()) % 7)).strftime('%Y-%m-%dT23:59:59')}",
            "priority": "high",
            "tags": ["work", "report", "deadline"],
            "estimated_duration": 240
        }}

        Input: "Buy groceries on the way home"
        Output: {{
            "title": "Buy groceries",
            "description": "Buy groceries on the way home",
            "due_date": null,
            "priority": "medium",
            "tags": ["errand", "shopping"],
            "estimated_duration": 60
        }}

        Now parse this input: "{user_input}"
        """

        return prompt

    def _parse_gemini_response(self, response_text: str) -> Dict:
        """
        Parse the JSON response from Gemini and return a dictionary.
        """
        import json

        try:
            # Clean up the response if it contains markdown code blocks
            cleaned_response = response_text.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]  # Remove ```json
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]  # Remove ```

            parsed = json.loads(cleaned_response)
            return parsed
        except json.JSONDecodeError:
            # If JSON parsing fails, return a minimal structure
            return {
                "title": "Parsed Task",
                "description": response_text[:200],
                "due_date": None,
                "priority": "medium",
                "tags": ["general"],
                "estimated_duration": None
            }

    def _rule_based_parse(self, user_input: str) -> TaskCreate:
        """
        Fallback rule-based parsing when Gemini fails.
        """
        # Extract due dates using regex patterns
        due_date = self._extract_due_date(user_input)

        # Determine priority based on urgency keywords
        priority = self._determine_priority(user_input)

        # Extract title (first part of the sentence)
        title = self._extract_title(user_input)

        # Generate tags based on keywords
        tags = self._generate_tags(user_input)

        return TaskCreate(
            title=title,
            description=user_input,
            due_date=due_date,
            priority=priority,
            tags=tags,
            estimated_duration=self._estimate_duration(user_input)
        )

    def _extract_due_date(self, text: str) -> Optional[datetime]:
        """
        Extract due date using regex patterns.
        """
        # Patterns for different date formats
        patterns = [
            r'today',
            r'tomorrow',
            r'in (\d+) (hour|hours|day|days|week|weeks|month|months)',
            r'on (\d{1,2}[/-]\d{1,2}(?:/\d{2,4})?)',
            r'by (\d{1,2}[/-]\d{1,2}(?:/\d{2,4})?)',
            r'at (\d{1,2}:\d{2}\s?(?:AM|PM|am|pm)?)',
            r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)(?:\s+(this|next))?',
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})'
        ]

        text_lower = text.lower()

        # Handle "today" and "tomorrow"
        if 'today' in text_lower:
            return datetime.combine(datetime.now().date(), datetime.min.time())
        elif 'tomorrow' in text_lower:
            return datetime.combine((datetime.now() + timedelta(days=1)).date(), datetime.min.time())

        # Handle days of the week
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for i, day in enumerate(days):
            if day in text_lower:
                current_weekday = datetime.now().weekday()  # Monday is 0
                days_ahead = (i - current_weekday) % 7
                if days_ahead == 0:  # Today
                    days_ahead = 7  # Next occurrence
                return datetime.combine((datetime.now() + timedelta(days=days_ahead)).date(), datetime.min.time())

        # Handle "in X days/hours" patterns
        in_pattern = r'in (\d+) (hour|hours|day|days|week|weeks|month|months)'
        match = re.search(in_pattern, text_lower)
        if match:
            num = int(match.group(1))
            unit = match.group(2)
            if 'hour' in unit:
                return datetime.now() + timedelta(hours=num)
            elif 'day' in unit:
                return datetime.combine((datetime.now() + timedelta(days=num)).date(), datetime.min.time())
            elif 'week' in unit:
                return datetime.combine((datetime.now() + timedelta(weeks=num)).date(), datetime.min.time())
            elif 'month' in unit:
                # Approximate: add 30 days per month
                return datetime.combine((datetime.now() + timedelta(days=num*30)).date(), datetime.min.time())

        return None

    def _determine_priority(self, text: str) -> str:
        """
        Determine task priority based on urgency keywords.
        """
        text_lower = text.lower()

        high_priority_keywords = [
            'urgent', 'asap', 'immediately', 'now', 'today', 'deadline',
            'important', 'critical', 'emergency', 'crucial', 'priority'
        ]

        low_priority_keywords = [
            'later', 'whenever', 'eventually', 'maybe', 'someday',
            'when convenient', 'at leisure'
        ]

        high_count = sum(1 for keyword in high_priority_keywords if keyword in text_lower)
        low_count = sum(1 for keyword in low_priority_keywords if keyword in text_lower)

        if high_count > low_count:
            return "high"
        elif low_count > high_count:
            return "low"
        else:
            return "medium"

    def _extract_title(self, text: str) -> str:
        """
        Extract the main task title from the text.
        """
        # Remove time/duration indicators and return the main action
        # This is a simplified version - in practice, you'd want more sophisticated NLP
        cleaned = re.sub(r'\b(at|on|by|in)\s+\d+(:\d+)?\s*(am|pm|hours?|days?|weeks?)?\b', '', text, flags=re.IGNORECASE)
        cleaned = re.sub(r'\b(tomorrow|today|tonight|yesterday)\b', '', cleaned, flags=re.IGNORECASE)

        # Find the main verb phrase
        # This is a very basic approach - real implementation would use NLP
        sentences = cleaned.split('.')
        main_sentence = sentences[0].strip()

        # Extract the imperative part
        words = main_sentence.split()
        if len(words) > 3:
            # Take the first 3-5 words as title
            return ' '.join(words[:min(5, len(words))]).strip()
        else:
            return main_sentence

    def _generate_tags(self, text: str) -> List[str]:
        """
        Generate relevant tags based on keywords in the text.
        """
        text_lower = text.lower()
        tags = set()

        # Work-related tags
        if any(word in text_lower for word in ['meeting', 'email', 'project', 'report', 'presentation', 'work', 'office']):
            tags.add('work')

        # Communication tags
        if any(word in text_lower for word in ['call', 'email', 'message', 'contact', 'phone', 'text']):
            tags.add('communication')

        # Errand/shopping tags
        if any(word in text_lower for word in ['buy', 'shop', 'grocery', 'store', 'purchase', 'errand']):
            tags.add('errands')

        # Health/wellness tags
        if any(word in text_lower for word in ['doctor', 'appointment', 'exercise', 'workout', 'health', 'medical']):
            tags.add('health')

        # Personal tags
        if any(word in text_lower for word in ['personal', 'home', 'family', 'friend']):
            tags.add('personal')

        # Add a default tag if none were identified
        if not tags:
            tags.add('general')

        return list(tags)[:5]  # Limit to 5 tags

    def _estimate_duration(self, text: str) -> Optional[int]:
        """
        Estimate task duration based on keywords.
        """
        text_lower = text.lower()

        # Look for explicit duration indicators
        duration_match = re.search(r'(\d+)\s*(hour|hours|min|minutes?)', text_lower)
        if duration_match:
            num = int(duration_match.group(1))
            unit = duration_match.group(2)
            if 'hour' in unit:
                return num * 60  # Convert hours to minutes
            else:
                return num  # Already in minutes

        # Estimate based on task type
        if any(word in text_lower for word in ['meeting', 'call', 'interview']):
            return 60  # 1 hour
        elif any(word in text_lower for word in ['email', 'message', 'reply']):
            return 15  # 15 minutes
        elif any(word in text_lower for word in ['report', 'analysis', 'research']):
            return 120  # 2 hours
        elif any(word in text_lower for word in ['shopping', 'errand']):
            return 90  # 1.5 hours
        elif any(word in text_lower for word in ['exercise', 'workout']):
            return 60  # 1 hour

        return None  # Unknown duration


# Singleton instance
task_parser_agent = TaskParserAgent()