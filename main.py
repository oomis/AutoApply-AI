import yaml
import pandas as pd
import json
import os
import datetime
import time
from dotenv import load_dotenv

from scraper import linkedin_scraper
from filter import filter_jobs
from ai_engine import get_ai_client, tailor_resume_for_job, generate_cover_letter
from file_generator import save_job_materials
from application_bot import apply_to_job_agent

def load_config():
    """Loads the profile.yml configuration file."""
    try:
        with open('profile.yml', 'r') as file:
            config = yaml.safe_load(file)
        print("✅ Configuration loaded successfully!")
        return config
    except FileNotFoundError:
        print("❌ Error: profile.yml not found.")
        return None

def main():
    """Main function to run the job bot workflow."""
    load_dotenv()
    config = load_config()
    if not config: return

    # --- Main Menu ---
    print("\n" + "="*25)
    print("--- Job Application Bot ---")
    print("="*25)
    print("1. Run full process (Scrape, Filter, Apply)")
    print("2. Run from filter step (uses existing scraped_jobs.csv)")
    print("3. Exit")
    choice = input("Choose an option (1/2/3): ")

    if choice == '1':
        print("\n--- Phase 1: Scraping Jobs ---")
        linkedin_scraper(config)
    elif choice == '2':
        print("\nSkipping scraping. Using existing scraped_jobs.csv.")
    else:
        print("Exiting.")
        return

    # --- Phase 2: Filter ---
    print("\n--- Phase 2: Filtering Jobs ---")
    filtered_df = filter_jobs(config)
    if filtered_df is None or filtered_df.empty:
        print("\nNo jobs to proceed with after filtering. Exiting.")
        return
        
    # --- Filter for Easy Apply jobs ---
    easy_apply_jobs = filtered_df[filtered_df['is_easy_apply'].str.lower() == 'yes'].copy()
    print(f"\nFound {len(easy_apply_jobs)} 'Easy Apply' jobs to process.")
    
    if easy_apply_jobs.empty:
        print("No 'Easy Apply' jobs found in the filtered list. Exiting.")
        return

    # --- Phase 3 & 4 Loop ---
    try:
        ai_client = get_ai_client(config)
    except ValueError as e:
        print(e)
        return
        
    application_log = []
    your_name = f"{config['personal_info']['first_name']} {config['personal_info']['last_name']}"

    for index, job in easy_apply_jobs.iterrows():
        print("\n" + "="*50)
        print(f"Processing job {index + 1}/{len(easy_apply_jobs)}: '{job['title']}' at '{job['company']}'")
        print(f"URL: {job['url']}")
        
        user_input = input("Proceed with this job? (y/n/skip): ")
        if user_input.lower() == 'n':
            print("Exiting bot.")
            break
        if user_input.lower() == 'skip':
            print("Skipping job.")
            application_log.append(f"{datetime.datetime.now()},{job['title']},{job['company']},SKIPPED")
            continue

        # AI Processing
        print("\n--- AI & File Generation ---")
        tailored_resume = tailor_resume_for_job(ai_client, config['resume_data'], job['description'])
        if not tailored_resume:
            application_log.append(f"{datetime.datetime.now()},{job['title']},{job['company']},AI_RESUME_FAILED")
            continue
        
        cover_letter = generate_cover_letter(ai_client, tailored_resume, job['title'], job['company'], your_name)
        if not cover_letter:
            application_log.append(f"{datetime.datetime.now()},{job['title']},{job['company']},AI_COVER_LETTER_FAILED")
            continue

        save_job_materials(job['title'], job['company'], tailored_resume, cover_letter)
        
        # Application Phase with Error Handling
        print("\n--- Automated Application (AGENT MODE) ---")
        job_details_for_bot = {"url": job['url'], "title": job['title']}
        resume_to_upload = config['resume_path']
        
        try:
            success = apply_to_job_agent(config, job_details_for_bot, resume_to_upload)
            
            if success:
                print(f"✅ Successfully processed application for: {job['title']}")
                application_log.append(f"{datetime.datetime.now()},{job['title']},{job['company']},APPLIED_SUCCESSFULLY")
            else:
                print(f"⚠️  Application process for '{job['title']}' did not complete successfully.")
                application_log.append(f"{datetime.datetime.now()},{job['title']},{job['company']},APPLICATION_FAILED")

        except Exception as e:
            print(f"🚨 A critical error occurred while trying to apply to '{job['title']}': {e}")
            application_log.append(f"{datetime.datetime.now()},{job['title']},{job['company']},CRITICAL_FAILURE")
        
        print("\nWaiting 10 seconds before next job...")
        time.sleep(10)

    # --- Save Log ---
    if application_log:
        log_file = "application_log.csv"
        # Check if file exists to write header
        file_exists = os.path.isfile(log_file)
        with open(log_file, "a", newline='') as f:
            if not file_exists:
                f.write("Timestamp,JobTitle,Company,Status\n") # Write header
            for log_entry in application_log:
                f.write(log_entry + "\n")
        print("\n✅ Application log updated.")

if __name__ == '__main__':
    main()