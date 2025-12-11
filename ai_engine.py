import openai
import json
import os
from typing import Any, Dict, Optional

MODEL_NAME = "gpt-4-turbo-preview"

def get_ai_client() -> openai.OpenAI:
    """Initializes and returns the OpenAI client from environment variables."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("❌ OpenAI API key not found in .env file. Make sure OPENAI_API_KEY is set.")
    return openai.OpenAI(api_key=api_key)

def tailor_resume_for_job(
    client: openai.OpenAI,
    resume_data: Dict[str, Any],
    job_description: str
) -> Optional[Dict[str, Any]]:
    """
    Uses OpenAI's API to tailor a resume for a specific job description.
    Returns the tailored resume as a dictionary, or None on failure.
    """
    print("🧠 Contacting AI to tailor resume...")

    tools = [
        {
            "type": "function",
            "function": {
                "name": "format_tailored_resume",
                "description": "Formats the tailored resume summary and work experience based on the job description.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tailored_summary": {
                            "type": "string",
                            "description": "A new, rewritten professional summary of 2-3 sentences, tailored to the job description."
                        },
                        "tailored_work_experience": {
                            "type": "array",
                            "description": "An array of work experience objects, with responsibilities rewritten to highlight skills relevant to the job description.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "company": {"type": "string"},
                                    "role": {"type": "string"},
                                    "dates": {"type": "string"},
                                    "rewritten_responsibilities": {
                                        "type": "array",
                                        "description": "An array of 2-4 rewritten responsibility bullet points emphasizing skills from the job description.",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": ["company", "role", "dates", "rewritten_responsibilities"]
                            }
                        }
                    },
                    "required": ["tailored_summary", "tailored_work_experience"]
                }
            }
        }
    ]

    resume_json_str = json.dumps(resume_data, indent=2)
    prompt = (
        f"Here is my resume data in JSON format:\n"
        f"--- RESUME DATA ---\n"
        f"{resume_json_str}\n\n"
        f"Here is the job description for a role I want to apply for:\n"
        f"--- JOB DESCRIPTION ---\n"
        f"{job_description}\n\n"
        "Please analyze the job description and my resume. Your task is to rewrite my 'summary' and the 'responsibilities' for each work experience to better align with the requirements and keywords found in the job description. "
        "Focus on creating impactful, results-oriented bullet points that mirror the language of the job description where appropriate.\n"
        "Use the `format_tailored_resume` function to return your answer."
    )

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            tools=tools,
            tool_choice={"type": "function", "function": {"name": "format_tailored_resume"}}
        )
        tool_call = response.choices[0].message.tool_calls[0]
        arguments = json.loads(tool_call.function.arguments)
        print("✅ AI has successfully tailored the resume.")
        return arguments
    except Exception as e:
        print(f"❌ Error while contacting the AI for resume tailoring: {e}")
        return None

def generate_cover_letter(
    client: openai.OpenAI,
    tailored_resume: Dict[str, Any],
    job_title: str,
    company_name: str,
    your_name: str
) -> Optional[str]:
    """
    Uses the AI to generate a cover letter based on the tailored resume.
    Returns the cover letter as a string, or None on failure.
    """
    print("🧠 Contacting AI to generate cover letter...")
    resume_context = json.dumps(tailored_resume, indent=2)
    prompt = (
        f"My name is {your_name}. I am applying for the {job_title} role at {company_name}.\n"
        f"Here is my resume, which has already been tailored for this specific job:\n"
        f"--- TAILORED RESUME CONTEXT ---\n"
        f"{resume_context}\n\n"
        "Please write a compelling, professional, and concise cover letter. It should have three paragraphs:\n"
        "1.  Introduction: State the position I'm applying for and my enthusiasm for the company.\n"
        "2.  Body: Highlight 2-3 key qualifications from my tailored resume that make me a perfect fit for the role. Use some of the language from my rewritten responsibilities.\n"
        "3.  Conclusion: Reiterate my interest and include a call to action (e.g., \"I am eager to discuss how my skills can contribute to your team's success\").\n\n"
        "Do not use placeholders like \"[Your Name]\". Write the letter as if I am the one writing it. Be confident but not arrogant."
    )

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}]
        )
        cover_letter_text = response.choices[0].message.content
        print("✅ AI has successfully generated the cover letter.")
        return cover_letter_text
    except Exception as e:
        print(f"❌ Error while generating the cover letter: {e}")
        return None