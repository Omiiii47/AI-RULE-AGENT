import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-2.0-flash"  # fast + cheap, good for this use case


def call_llm_json(system_prompt: str, user_prompt: str) -> dict:
    """Calls Gemini and forces JSON output."""
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=system_prompt,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0,
        },
    )
    response = model.generate_content(user_prompt)
    return json.loads(response.text)


def call_llm_text(system_prompt: str, user_prompt: str) -> str:
    """Calls Gemini for plain text generation (used by Response Node)."""
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=system_prompt,
        generation_config={
            "temperature": 0.3,
        },
    )
    response = model.generate_content(user_prompt)
    return response.text.strip()
