import os
import json
from groq import Groq

class AIService:

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL") or "llama-3.3-70b-versatile"
        print(f"DEBUG: AIService initialized. API Key found: {'Yes' if self.api_key else 'No'}")

        if not self.api_key:
            self.client = None
            return

        self.client = Groq(api_key=self.api_key)

    def generate_project_plan(
        self,
        project_title,
        project_description,
        team_members,
        project_deadline
    ):
        """
        Generates a structured project plan using Groq AI.
        """
        if not self.api_key or not self.client:
            return {
                "error": "GROQ_API_KEY not configured. Please add it to your .env file."
            }

        prompt = (
            "Create a project plan as JSON only.\n\n"
            f"Project: {project_title}\n"
            f"Description: {project_description}\n"
            f"Deadline: {project_deadline}\n\n"
            "Team:\n"
            f"{json.dumps(team_members, ensure_ascii=False)}\n\n"
            'Rules:\n'
            '- Output must be a JSON object: {"tasks": [...]}.\n'
            "- Create 5-10 realistic tasks.\n"
            '- Each task: title, description, priority (High/Medium/Low/Critical), assigned_to (member id), estimate_hours (number), due_date (YYYY-MM-DD <= deadline).\n'
            "- Distribute workload evenly.\n"
            "- Prioritize critical path items.\n"
            "Return JSON only."
        )

        try:
            print(f"DEBUG: Generating content with Groq model: {self.model}")
            chat_completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional project manager AI. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1600,
                response_format={"type": "json_object"},
            )

            response_content = chat_completion.choices[0].message.content
            print(f"DEBUG: Groq raw response: {response_content[:200]}...")
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

        except json.JSONDecodeError:
            return {
                "error": "AI returned invalid JSON format."
            }

        except Exception as e:
            err = str(e)
            print(f"AI Generation Error: {err}")
            if "401" in err or "invalid_api_key" in err or "Authentication" in err:
                return {"error": "Invalid or expired Groq API key. Please update GROQ_API_KEY in your .env file."}
            if "429" in err or "rate_limit" in err:
                return {"error": "Groq API rate limit reached. Please wait a moment and try again."}
            return {"error": f"AI generation failed: {err}"}


ai_service = AIService()
