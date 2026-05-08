import os
import json
import google.generativeai as genai

class AIService:

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = "gemini-2.5-flash"

        if not self.api_key:
            self.client = None
            return

        genai.configure(api_key=self.api_key)
        self.client = genai.GenerativeModel(self.model)

    def generate_project_plan(
        self,
        project_title,
        project_description,
        team_members,
        project_deadline
    ):
        """
        Generates a structured project plan using Gemini AI.
        """
        if not self.api_key or not self.client:
            return {
                "error": "GEMINI_API_KEY not configured. Please add it to your .env file."
            }

        prompt = f"""
Create a project plan as valid JSON only.

Project: {project_title}

Description:
{project_description}

Deadline:
{project_deadline}

Team:
{json.dumps(team_members, ensure_ascii=False)}

Rules:

* Output must be valid JSON only

* Structure:
  {{
  "tasks": [
  {{
  "title": "",
  "description": "",
  "priority": "",
  "assigned_to": 1,
  "estimate_hours": 5,
  "due_date": "2026-05-10"
  }}
  ]
  }}

* Create 5-10 realistic tasks

* Priority values:
  High
  Medium
  Low
  Critical

* Distribute workload evenly

* Prioritize important tasks

* due_date must not exceed project deadline
"""

        try:
            print(f"DEBUG: Generating content with prompt: {prompt[:100]}...")
            response = self.client.generate_content(prompt)
            print(f"DEBUG: Gemini raw response: {response.text[:200]}...")
            response_text = response.text.strip()

            # Remove markdown formatting
            response_text = response_text.replace(
                "```json", ""
            ).replace(
                "```", ""
            ).strip()

            data = json.loads(response_text)

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

            if "API_KEY" in err or "authentication" in err.lower():
                return {
                    "error": "Invalid Gemini API key. Please update GEMINI_API_KEY in your .env file."
                }

            if "429" in err or "quota" in err.lower():
                return {
                    "error": "Gemini API rate limit reached. Please try again later."
                }

            return {
                "error": f"AI generation failed: {err}"
            }


ai_service = AIService()
