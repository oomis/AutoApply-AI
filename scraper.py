# scraper.py

import time
import csv
import re
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- NEW IMPORTS FOR THE AI AGENT ---
from ai_agent import simplify_html, get_ai_action_for_scrolling
from ai_engine import get_ai_client

def parse_card_text(card_text):
    """
    Parses the raw text block from a job card to extract details.
    This function remains unchanged.
    """
    lines = [line.strip() for line in card_text.split('\n') if line.strip()]
    if not lines: return None
    title = lines[0]
    company = "N/A"
    for i, line in enumerate(lines):
        if line != title and not re.search(r'viewed|promoted|alumni|applicants', line, re.IGNORECASE):
             company = line
             if i + 1 < len(lines):
                 location = lines[i+1]
                 if re.search(r',', location):
                     break
    location = "N/A"
    for line in lines:
        if re.search(r', \w{2,}, United Kingdom|\(Remote\)', line, re.IGNORECASE):
            location = line
            break
    return {"title": title, "company": company, "location": location}


def linkedin_scraper(config):
    """
    Scrapes LinkedIn jobs using an AI agent for dynamic scrolling and interaction.
    """
    print("🚀 Starting LinkedIn Scraper (AI Agent Method)...")
    
    # Get credentials from environment variables
    LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
    LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
    
    if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
        raise ValueError("❌ LinkedIn email or password not found in .env file.")

    # Get search criteria from the config object (this is not secret)
    SEARCH_KEYWORDS = config['job_search_criteria']['keywords']
    SEARCH_LOCATION = config['job_search_criteria']['location']

    
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    
    try:
        # --- 1. Login ---
        print("Logging in...")
        driver.get("https://www.linkedin.com/login")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(LINKEDIN_EMAIL)
        driver.find_element(By.ID, "password").send_keys(LINKEDIN_PASSWORD)
        driver.find_element(By.ID, "password").send_keys(Keys.RETURN)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "global-nav-search")))
        print("✅ Login successful.")

        # --- 2. Search ---
        search_url = f"https://www.linkedin.com/jobs/search/?f_WT=2&keywords={SEARCH_KEYWORDS}&location={SEARCH_LOCATION}&refresh=true"
        driver.get(search_url)
        print(f"✅ Searching at: {search_url}")
        time.sleep(5)

        # --- 3. AI-Driven Scrolling ---
        print("\n--- Initializing AI Scrolling Agent ---")
        ai_client = get_ai_client(config)
        previous_actions = []
        
        for i in range(10): # Limit to 10 agent actions to prevent infinite loops/runaway costs
            print(f"\n--- Agent Action Cycle {i+1}/10 ---")
            
            # 1. Observe
            page_html = driver.page_source
            simplified_page = simplify_html(page_html)
            current_job_count = len(driver.find_elements(By.CSS_SELECTOR, "div[data-job-id]"))
            
            # 2. Think
            action_str = get_ai_action_for_scrolling(ai_client, simplified_page, previous_actions, current_job_count)
            
            # 3. Act
            if "STOP" in action_str.upper():
                print("✅ AI decided to stop scrolling.")
                break
            elif "SCROLL_WINDOW" in action_str.upper():
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                previous_actions.append("SCROLL_WINDOW")
            elif "CLICK" in action_str.upper():
                try:
                    selector = action_str.split(' ', 1)[1]
                    print(f"Attempting to click '{selector}'...")
                    driver.find_element(By.CSS_SELECTOR, selector).click()
                    previous_actions.append(f"CLICK {selector}")
                except Exception as e:
                    print(f"AI tried to click, but failed: {e}. Stopping agent.")
                    break
            else:
                print(f"AI returned an unknown command: '{action_str}'. Stopping agent.")
                break
            
            time.sleep(3) # Wait for page to react
        
        # --- 4. Final Data Extraction ---
        print("\nAI-driven scrolling complete. Collecting all found jobs...")
        job_cards = driver.find_elements(By.CSS_SELECTOR, "div[data-job-id]")
        print(f"Found a total of {len(job_cards)} job cards. Now extracting details...")
        
        jobs = []
        for card in job_cards:
            parsed_data = parse_card_text(card.text)
            if not parsed_data: continue
            
            parsed_data['url'] = "N/A"
            parsed_data['is_easy_apply'] = "No"
            parsed_data['description'] = "Description could not be loaded."
            
            try:
                parsed_data['url'] = card.find_element(By.TAG_NAME, "a").get_attribute("href").split('?')[0]
                if "easy apply" in card.text.lower():
                    parsed_data["is_easy_apply"] = "Yes"
                
                driver.execute_script("arguments[0].click();", card)
                time.sleep(1.5)
                description_pane = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-details__main-content")))
                parsed_data['description'] = description_pane.text.strip()
                
                jobs.append(parsed_data)
                print(f"  -> Scraped: {parsed_data['title']} (Easy Apply: {parsed_data['is_easy_apply']})")
            except Exception:
                continue
                
    except Exception as e:
        print(f"❌ An unexpected error occurred in the main process: {e}")
    finally:
        # --- 5. Save and Quit ---
        if 'jobs' in locals() and jobs:
            filename = 'scraped_jobs.csv'
            print(f"\nSaving {len(jobs)} jobs to {filename}...")
            unique_jobs = list({job['url']: job for job in jobs if job['url'] != "N/A"}.values())
            print(f"Found {len(unique_jobs)} unique jobs.")
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=["title", "company", "location", "url", "is_easy_apply", "description"])
                writer.writeheader()
                writer.writerows(unique_jobs)
            print(f"✅ Scraped data saved to {filename}")
        else:
            print("\nNo jobs were successfully scraped.")
        print("Scraper finished. Closing browser.")
        if 'driver' in locals() and driver:
            driver.quit()