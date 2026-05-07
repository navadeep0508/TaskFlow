import os
import json
from openai import OpenAI
from datetime import datetime, timedelta

class AIService:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            # If missing, the UI will report the issue.
            self.client = None
            return
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )

    def generate_project_plan(self, project_title, project_description, team_members, project_deadline):
        """
        Generates a structured project plan using OpenRouter AI.
        team_members is a list of dicts: {"name": str, "skills": str, "id": int}
        """
        if not self.api_key or not self.client:
            return {"error": "OPENROUTER_API_KEY not configured. Please add it to your .env file."}

        prompt = f"""
        You are a professional project manager AI.
        Create a detailed project plan for the following:
        Project: {project_title}
        Description: {project_description}
        Deadline: {project_deadline}
        
        Team Members and their Skills:
        {json.dumps(team_members, indent=2)}
        
        Requirements:
        1. Break the project into 5-10 realistic tasks.
        2. Each task must have:
           - Title
           - Detailed description
           - Priority (High, Medium, Low, Critical)
           - Assignee ID (select the best person from the team based on skills)
           - Estimated effort (hours)
           - Due date (YYYY-MM-DD, must be before project deadline)
        3. Distribute workload evenly.
        4. Prioritize critical path items.
        
        Output MUST be a valid JSON object with a key "tasks" containing an array of task objects.
        Example format:
        {{
          "tasks": [
            {{
              "title": "Task Title",
              "description": "Task description",
              "priority": "High",
              "assigned_to": 1,
              "estimate_hours": 8,
              "due_date": "2024-05-10"
            }}
          ]
        }}
        
        Only return the JSON object. No other text.
        """

        try:
            # Use OpenRouter to generate the plan
            chat_completion = self.client.chat.completions.create(
                model="baidu/cobuddy:free",
                messages=[
                    {"role": "system", "content": "You are a professional project manager AI. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )

            response_content = chat_completion.choices[0].message.content
            data = json.loads(response_content)

            if isinstance(data, dict):
                if "tasks" in data and isinstance(data["tasks"], list):
                    return data["tasks"]
                for key in ["plan", "project_plan"]:
                    if key in data and isinstance(data[key], list):
                        return data[key]
                if len(data) == 1:
                    first_val = list(data.values())[0]
                    if isinstance(first_val, list):
                        return first_val

            return data if isinstance(data, list) else []
        except Exception as e:
            err = str(e)
            print(f"AI Generation Error: {err}")
            if "401" in err or "invalid_api_key" in err or "Authentication" in err:
                return {"error": "Invalid or expired OpenRouter API key. Please update OPENROUTER_API_KEY in your .env file and restart the server. Get a free key at https://openrouter.ai/keys"}
            if "429" in err or "rate_limit" in err:
                return {"error": "OpenRouter API rate limit reached. Please wait a moment and try again."}
            return {"error": f"AI generation failed: {err}"}

ai_service = AIService()
