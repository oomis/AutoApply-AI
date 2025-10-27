# application_bot.py (Updated for Environment Variables)

import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import Select

from ai_engine import get_ai_client
from ai_agent import simplify_html, get_initial_page_action, get_ai_action_for_application, get_ai_answer_for_question

def apply_to_job_agent(config, job_details, resume_file_path):
    """
    Uses a reasoning AI agent to find the apply button and fill out the form.
    """
    print(f"🤖 Initializing AI Application Agent for '{job_details['title']}'...")
    
    driver = None
    try:
        # --- NEW: Get credentials from environment variables ---
        LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
        LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
        if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
            raise ValueError("❌ LinkedIn email or password not found in environment variables. Check your .env file.")
        # ----------------------------------------------------

        ai_client = get_ai_client(config)
        options = webdriver.ChromeOptions()
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()

        # --- 1. Login & Navigate ---
        print("Logging in and navigating to job page...")
        driver.get("https://www.linkedin.com/login")
        
        # --- UPDATED: Use the new variables ---
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(LINKEDIN_EMAIL)
        driver.find_element(By.ID, "password").send_keys(LINKEDIN_PASSWORD)
        # -------------------------------------

        driver.find_element(By.ID, "password").send_keys(Keys.RETURN)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "global-nav-search")))
        print("✅ Login successful.")
        driver.get(job_details['url'])
        print(f"Navigated to job page: {job_details['url']}")
        
        # --- 2. OODA Loop: Wait, Observe, Decide, Act ---
        print("Waiting for job page to stabilize...")
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobs-description-content")))
        print("✅ Job page appears loaded. Starting AI analysis.")

        page_html = driver.find_element(By.TAG_NAME, "body").get_attribute('outerHTML')
        simplified_page_html = simplify_html(page_html, for_application=True)
        
        # This debug block can be removed if you want, but it's helpful.
        # --- DEBUG BLOCK ---
        print("\n" + "*"*20 + " DEBUG START " + "*"*20)
        debug_filename = "debug_page_for_ai.html"
        with open(debug_filename, "w", encoding="utf-8") as f:
            f.write(simplified_page_html.prettify())
        print(f"🕵️  Wrote the HTML the AI will see to '{debug_filename}'")
        print("*"*20 + " DEBUG END " + "*"*20 + "\n")
        # ---------------------------
        
        raw_action_str = get_initial_page_action(ai_client, simplified_page_html)

        # --- ROBUST PARSING LOGIC ---
        command = None
        action_str = None
        for cmd in ["CLICK_EASY_APPLY", "CLICK_APPLY", "FAIL"]:
            if cmd in raw_action_str:
                start_index = raw_action_str.rfind(cmd)
                action_str = raw_action_str[start_index:]
                command = cmd
                break
        
        if not command:
            print(f"❌ AI returned an unparsable command: '{raw_action_str}'")
            return False
        
        print(f"🤖 Parsed command: '{action_str}'")
        parts = action_str.split(' ', 1)

        if command == "FAIL":
            reason = parts[1] if len(parts) > 1 else "No reason given."
            print(f"❌ AI concluded application is not possible. Reason: {reason}")
            return False
        
        if command == "CLICK_APPLY":
            print("ℹ️ AI found a regular 'Apply' button. This leads to an external site and is not supported. Aborting this job.")
            return False

        # NOTE: I noticed you added a new import `from ai_agent import click_easy_apply_button`.
        # This is not a function we've built, and it's better to keep the logic here.
        # I'm reverting to the previous, more robust logic.
        if command == "CLICK_EASY_APPLY":
            try:
                agent_id = parts[1]
                easy_apply_button = driver.find_element(By.CSS_SELECTOR, f"[agent-id='{agent_id}']")
                driver.execute_script("arguments[0].click();", easy_apply_button)
                print("✅ AI located and clicked 'Easy Apply'. Handing over to form-filling agent...")
                time.sleep(2)
            except Exception as e:
                print(f"❌ AI found a button, but could not click it. Error: {e}")
                return False
        else:
            print(f"❌ Logic error: Command was '{command}' but not handled.")
            return False

        # --- 3. The Form-Filling Agent Loop ---
        for i in range(15):
            print(f"\n--- Agent Application Cycle {i+1}/15 ---")
            modal_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobs-easy-apply-modal")))
            modal_html = modal_element.get_attribute('outerHTML')
            simplified_modal_html = simplify_html(modal_html, for_application=True)
            application_data = {"phone": config['personal_info']['phone'], "resume_path": os.path.abspath(resume_file_path)}
            action_str = get_ai_action_for_application(ai_client, simplified_modal_html, application_data)
            parts = action_str.split(' ', 2)
            command = parts[0].upper()
            if command == "DONE": print("✅ AI agent reports task is complete."); break
            if command == "FAIL": print(f"❌ AI agent failed. Reason: {' '.join(parts[1:])}"); return False
            try:
                agent_id = parts[1]
                target_element = driver.find_element(By.CSS_SELECTOR, f"[agent-id='{agent_id}']")
            except Exception: print(f"Could not find element with {agent_id}. Agent may be hallucinating. Aborting."); return False
            if command == "TYPE": target_element.clear(); target_element.send_keys(parts[2])
            elif command == "SELECT": Select(target_element).select_by_visible_text(parts[2])
            elif command == "CLICK": target_element.click()
            elif command == "UPLOAD": target_element.send_keys(parts[2])
            elif command == "ANSWER":
                answer = get_ai_answer_for_question(ai_client, parts[2], config['story_bank'])
                target_element.send_keys(answer)
            elif command == "SUBMIT": print("🤖 AI wants to submit. This is a simulated success."); print("✅ APPLICATION SUBMITTED (Simulated)."); break
            time.sleep(2)

    except TimeoutException:
        print("❌ TIMEOUT: A critical element was not found in time. The page may have a different layout or failed to load. Aborting this job.")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred in the agent process: {e}")
        return False
    finally:
        print("Application agent finished for this job. Closing browser.")
        if driver:
            driver.quit()
            
    return True