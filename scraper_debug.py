# scraper_debug.py (Secure Version using Environment Variables)

import time
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- LOAD ENVIRONMENT VARIABLES ---
# This line reads the .env file and loads the variables into the environment
load_dotenv()

# --- CONFIGURATION FROM ENVIRONMENT ---
# Get the credentials using os.getenv(). The second argument is a default value if not found.
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
SEARCH_KEYWORDS = "Software Engineer"
SEARCH_LOCATION = "Remote"

def debug_scraper():
    print("🚀 Starting DEBUG Scraper...")
    
    # --- Check if credentials were loaded ---
    if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
        print("❌ Error: LINKEDIN_EMAIL or LINKEDIN_PASSWORD not found in .env file.")
        print("Please make sure your .env file is set up correctly.")
        return # Stop the script

    driver = webdriver.Chrome()
    driver.maximize_window()

    try:
        # --- 1. Login ---
        print("Navigating to login page...")
        driver.get("https://www.linkedin.com/login")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(LINKEDIN_EMAIL)
        driver.find_element(By.ID, "password").send_keys(LINKEDIN_PASSWORD)
        driver.find_element(By.ID, "password").send_keys(Keys.RETURN)
        print("Waiting for login verification...")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "global-nav-search")))
        print("✅ Login successful.")

        # --- 2. Search ---
        print("Navigating to jobs page and searching...")
        search_url = f"https://www.linkedin.com/jobs/search/?f_WT=2&keywords={SEARCH_KEYWORDS}&location={SEARCH_LOCATION}&refresh=true"
        driver.get(search_url)
        print(f"✅ Searching at: {search_url}")
        time.sleep(5)

        # --- 3. Find Cards and Print Their Text ---
        print("Attempting to find and print job card text...")
        
        for i in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            print(f"📜 Scrolling... ({i+1}/5)")
            time.sleep(3)

        job_cards = driver.find_elements(By.CSS_SELECTOR, "div[data-job-id]")
        print(f"Found {len(job_cards)} job cards.")

        if not job_cards:
            print("❌ Could not find any job cards with selector 'div[data-job-id]'.")
        else:
            print("\n--- PRINTING RAW TEXT FROM EACH CARD ---")
            for i, card in enumerate(job_cards):
                try:
                    card_text = card.text
                    print(f"\n--- CARD {i+1} ---")
                    print(card_text)
                    print("-----------------")
                except Exception as e:
                    print(f"\n--- CARD {i+1} ---")
                    print(f"Could not get text from this card. Error: {e}")
                    print("-----------------")

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
    finally:
        print("\nDebug scraper finished. Closing browser.")
        if 'driver' in locals() and driver:
            driver.quit()

if __name__ == '__main__':
    debug_scraper()