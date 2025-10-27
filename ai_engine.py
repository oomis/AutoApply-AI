# ai_engine.py

import openai
import json
import os

def get_ai_client(config): # config is no longer needed but we can leave it for consistency
    """Initializes and returns the OpenAI client from environment variables."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("❌ OpenAI API key not found in .env file. Make sure OPENAI_API_KEY is set.")
    return openai.OpenAI(api_key=api_key)

def tailor_resume_for_job(client, resume_data, job_description):
    """
    Uses OpenAI's API to tailor a resume for a specific job description.
    """
    print("🧠 Contacting AI to tailor resume...")

    # We are using a structured format (JSON) to get a reliable response.
    # This is a powerful technique called "Function Calling" or "Tool Use" in modern LLMs.
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

    # Convert your resume data to a string for the prompt
    resume_json_str = json.dumps(resume_data, indent=2)

    prompt = f"""
    Here is my resume data in JSON format:
    --- RESUME DATA ---
    {resume_json_str}
    
    Here is the job description for a role I want to apply for:
    --- JOB DESCRIPTION ---
    {job_description}

    Please analyze the job description and my resume. Your task is to rewrite my 'summary' and the 'responsibilities' for each work experience to better align with the requirements and keywords found in the job description. 
    Focus on creating impactful, results-oriented bullet points that mirror the language of the job description where appropriate.
    Use the `format_tailored_resume` function to return your answer.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",  # A powerful and cost-effective model
            messages=[{"role": "user", "content": prompt}],
            tools=tools,
            tool_choice={"type": "function", "function": {"name": "format_tailored_resume"}}
        )

        # The response will contain the structured JSON we asked for
        tool_call = response.choices[0].message.tool_calls[0]
        arguments = json.loads(tool_call.function.arguments)
        
        print("✅ AI has successfully tailored the resume.")
        return arguments

    except Exception as e:
        print(f"❌ An error occurred while contacting the AI: {e}")
        return None

# --- NEW FUNCTION TO ADD ---
def generate_cover_letter(client, tailored_resume, job_title, company_name, your_name):
    """
    Uses the AI to generate a cover letter based on the tailored resume.
    """
    print("🧠 Contacting AI to generate cover letter...")
    
    # Convert the tailored resume JSON to a string for the AI's context
    resume_context = json.dumps(tailored_resume, indent=2)

    prompt = f"""
    My name is {your_name}. I am applying for the {job_title} role at {company_name}.
    Here is my resume, which has already been tailored for this specific job:
    --- TAILORED RESUME CONTEXT ---
    {resume_context}

    Please write a compelling, professional, and concise cover letter. It should have three paragraphs:
    1.  Introduction: State the position I'm applying for and my enthusiasm for the company.
    2.  Body: Highlight 2-3 key qualifications from my tailored resume that make me a perfect fit for the role. Use some of the language from my rewritten responsibilities.
    3.  Conclusion: Reiterate my interest and include a call to action (e.g., "I am eager to discuss how my skills can contribute to your team's success").
    
    Do not use placeholders like "[Your Name]". Write the letter as if I am the one writing it. Be confident but not arrogant.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}]
        )
        
        cover_letter_text = response.choices[0].message.content
        print("✅ AI has successfully generated the cover letter.")
        return cover_letter_text

    except Exception as e:
        print(f"❌ An error occurred while generating the cover letter: {e}")
        return None