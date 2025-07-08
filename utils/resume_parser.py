import os
import openai
from typing import Dict, Any, Optional

class ResumeParser:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the resume parser with OpenAI API key.

        Args:
            api_key (Optional[str]): OpenAI API key. If not provided, will try to get from environment variable.
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY environment variable")
        
        self.client = openai.OpenAI(api_key=self.api_key)

    def parse_resume(self, text: str) -> Dict[str, Any]:
        """Extract structured information from resume text using OpenAI.

        Args:
            text (str): Raw text extracted from resume

        Returns:
            Dict[str, Any]: Structured resume information
        """
        try:
            # Create a prompt for GPT to extract structured information
            prompt = f"""Extract the following information from the resume text in JSON format:
            - Full Name
            - Email Address
            - Phone Number
            - Skills (as a list)
            - Work Experience (as a list of dictionaries with company, position, duration, and responsibilities)
            - Education (as a list of dictionaries with institution, degree, and graduation year)

Resume text:
{text}

Provide the information in the following JSON structure:
{{
    "full_name": "",
    "email": "",
    "phone": "",
    "skills": [],
    "work_experience": [
        {{
            "company": "",
            "position": "",
            "duration": "",
            "responsibilities": []
        }}
    ],
    "education": [
        {{
            "institution": "",
            "degree": "",
            "graduation_year": ""
        }}
    ]
}}
"""

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # or gpt-3.5-turbo
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured information from resumes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # Keep it deterministic
                max_tokens=1000
            )

            # Extract the response
            parsed_data = response.choices[0].message.content
            if not parsed_data:
                print("OpenAI API returned empty content:", response)
                return {"error": "OpenAI API returned empty content"}
            # Remove markdown code block if present
            if parsed_data.strip().startswith("```json"):
                parsed_data = parsed_data.strip().removeprefix("```json").removesuffix("```")
            elif parsed_data.strip().startswith("```"):
                parsed_data = parsed_data.strip().removeprefix("```").removesuffix("```")
            import json
            try:
                return json.loads(parsed_data)
            except json.JSONDecodeError as e:
                print("Failed to decode OpenAI response as JSON:", parsed_data)
                return {"error": f"Failed to decode OpenAI response as JSON: {str(e)}", "raw_response": parsed_data}

        except Exception as e:
            return {
                "error": f"Failed to parse resume: {str(e)}",
                "raw_text": text
            }