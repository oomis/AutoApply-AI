# file_generator.py

def save_job_materials(job_title, company_name, tailored_resume_json, cover_letter_text):
    """
    Saves the tailored resume and cover letter to text files.
    """
    # Sanitize company name for use in filenames
    safe_company_name = "".join(x for x in company_name if x.isalnum())
    
    resume_filename = f"output/{safe_company_name}_{job_title.split(' ')[0]}_Resume.txt"
    cover_letter_filename = f"output/{safe_company_name}_{job_title.split(' ')[0]}_Cover_Letter.txt"

    print(f"\n💾 Saving materials...")
    try:
        # Create an 'output' directory if it doesn't exist
        import os
        os.makedirs("output", exist_ok=True)
        
        # Save tailored resume JSON to a file
        with open(resume_filename, 'w') as f:
            f.write(f"Tailored Resume for {job_title} at {company_name}\n\n")
            f.write("--- SUMMARY ---\n")
            f.write(tailored_resume_json['tailored_summary'] + "\n\n")
            f.write("--- WORK EXPERIENCE ---\n")
            for exp in tailored_resume_json['tailored_work_experience']:
                f.write(f"Company: {exp['company']}\n")
                f.write(f"Role: {exp['role']}\n")
                f.write(f"Dates: {exp['dates']}\n")
                f.write("Responsibilities:\n")
                for resp in exp['rewritten_responsibilities']:
                    f.write(f"- {resp}\n")
                f.write("\n")
        print(f"  -> Saved tailored resume to {resume_filename}")

        # Save cover letter to a file
        with open(cover_letter_filename, 'w') as f:
            f.write(cover_letter_text)
        print(f"  -> Saved cover letter to {cover_letter_filename}")
        
        return resume_filename, cover_letter_filename

    except Exception as e:
        print(f"❌ Error saving files: {e}")
        return None, None