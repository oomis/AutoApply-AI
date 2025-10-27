import openai
from bs4 import BeautifulSoup
import json

def simplify_html(html_content, for_application=False):
    """
    Cleans up HTML and adds agent-ids to interactive elements.
    """
    soup = BeautifulSoup(html_content, 'lxml')
    for tag in soup.find_all(['script', 'style', 'meta', 'link', 'header', 'footer', 'nav']):
        tag.decompose()
    if for_application:
        interactive_tags = soup.find_all(['input', 'button', 'select', 'textarea', 'a'])
        for i, tag in enumerate(interactive_tags):
            tag['agent-id'] = f"agent-{i}"
    return soup

def get_ai_action_for_scrolling(client, simplified_html, previous_actions, job_count):
    """
    Asks the AI what to do next to find more jobs on a search results page.
    """
    print("🤖 AI is thinking about how to scroll...")
    prompt = f"""
    You are an expert web scraping agent. Your goal is to scroll a LinkedIn job search page to reveal all possible job listings.
    The current simplified text view of the page is:
    --- PAGE STATE (first 4000 chars) ---
    {simplified_html.get_text(separator='\\n', strip=True)[:4000]}
    So far, you have found {job_count} jobs.
    The previous actions you have taken are: {', '.join(previous_actions) if previous_actions else 'None'}.
    Based on this, what is the best action to take next to find more jobs?
    Your available actions are:
    1. "SCROLL_WINDOW": Scroll the main window down. This is the most common action.
    2. "CLICK <CSS_SELECTOR>": Click a 'load more' button. You must provide a valid CSS selector for the button.
    3. "STOP": If you believe all jobs have been loaded, you are stuck, or you see text like "you've seen all jobs".
    Analyze the page state. If you see a "See more jobs" or "Load more" button, choose CLICK. Otherwise, SCROLL_WINDOW is the default safe action.
    Your response must be ONLY ONE of the actions listed above. For example: `SCROLL_WINDOW` or `CLICK button.jobs-search-results__load-more-button`.
    """
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[{"role": "user", "content": prompt}]
    )
    action = response.choices[0].message.content.strip()
    print(f"🤖 AI chose scroll action: {action}")
    return action

def get_initial_page_action(client, simplified_html):
    """
    Finds the 'Easy Apply' button and returns the agent action.
    """
    print("🤖 AI is performing a two-step page analysis...")

    # Step 0: Python pre-check for 'Easy Apply' text
    print("  -> Step 0: Python pre-check for 'Easy Apply' text...")
    all_text = simplified_html.get_text(separator=' ', strip=True)
    if "Easy Apply" not in all_text:
        print("  -> Step 0 Result: 'Easy Apply' not found in page text.")
        return "FAIL 'Easy Apply' text not found on page."

    # Step 1: Python search for 'Easy Apply' button agent-id
    print("  -> Step 1: Python search for 'Easy Apply' button agent-id...")
    for button in simplified_html.find_all(['button', 'a']):
        if 'Easy Apply' in button.get_text(strip=True):
            agent_id = button.get('agent-id')
            if agent_id:
                print(f"  -> Step 1 Result: Found agent-id: {agent_id}")
                return f"CLICK_EASY_APPLY {agent_id}"
    print("  -> Step 1 Result: Could not isolate agent-id")
    return "FAIL Could not isolate agent-id"

def get_ai_action_for_application(client, simplified_html, application_data):
    """
    Asks the AI to decide the next step in filling out an application form.
    """
    print("🤖 AI is thinking about how to fill this form...")
    prompt = f"""
    You are an expert robotic process automation (RPA) agent. Your goal is to fill out and submit this job application form.
    Here is your personal data for the application:
    --- PERSONAL DATA ---
    {json.dumps(application_data, indent=2)}
    Here is the current state of the application form's HTML. Interactive elements have a unique `agent-id` attribute.
    --- FORM HTML (first 6000 chars) ---
    {simplified_html.prettify()[:6000]}
    Based on the HTML and your personal data, what is the single next action you should take?
    Your available actions are:
    1.  `TYPE <agent-id> <text_to_type>`
    2.  `SELECT <agent-id> <option_text>`
    3.  `CLICK <agent-id>`
    4.  `UPLOAD <agent-id> <file_path>`
    5.  `ANSWER <agent-id> <question_text>`
    6.  `SUBMIT <agent-id>`
    7.  `DONE`
    8.  `FAIL <reason>`
    Your response must be a single line in the format `COMMAND agent-id value`. Do not explain.
    """
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[{"role": "user", "content": prompt}]
    )
    action = response.choices[0].message.content.strip()
    print(f"🤖 AI chose form action: {action}")
    return action

def get_ai_answer_for_question(client, question, story_bank):
    """
    Uses the AI and story bank to answer a custom application question.
    """
    print(f"🤖 AI is thinking of an answer for: '{question}'...")
    prompt = f"""
    You are a career coach helping me answer a job application question.
    The question is: "{question}"
    Here is my "Story Bank" with my key career experiences:
    --- STORY BANK ---
    {json.dumps(story_bank, indent=2)}
    Please generate a concise, professional answer to the question. The answer should be a single block of text. Do not add any conversational filler.
    """
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response.choices[0].message.content.strip()
    print(f"🤖 AI generated answer: '{(answer[:70] + '...') if len(answer) > 70 else answer}'")
    return answer

# --- Selenium Helper Function ---

def click_easy_apply_button(driver, timeout=10):
    """
    Clicks the real 'Easy Apply' button on a LinkedIn job page using Selenium.
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    print("🔎 Looking for the real 'Easy Apply' button in the browser...")
    easy_apply_button = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((
            By.XPATH,
            "//button[contains(@class, 'jobs-apply-button') and contains(., 'Easy Apply')]"
        ))
    )
    easy_apply_button.click()
    print("✅ Clicked the real 'Easy Apply' button.")



# # ai_agent.py (Complete with ALL agent functions)

# import openai
# from bs4 import BeautifulSoup
# import json

# def simplify_html(html_content, for_application=False):
#     """
#     Cleans up HTML and adds agent-ids to interactive elements.
#     """
#     soup = BeautifulSoup(html_content, 'lxml')
#     for tag in soup.find_all(['script', 'style', 'meta', 'link', 'header', 'footer', 'nav']):
#         tag.decompose()
#     if for_application:
#         interactive_tags = soup.find_all(['input', 'button', 'select', 'textarea', 'a'])
#         for i, tag in enumerate(interactive_tags):
#             tag['agent-id'] = f"agent-{i}"
#     return soup

# def get_ai_action_for_scrolling(client, simplified_html, previous_actions, job_count):
#     """
#     Asks the AI what to do next to find more jobs on a search results page.
#     """
#     print("🤖 AI is thinking about how to scroll...")
#     prompt = f"""
#     You are an expert web scraping agent. Your goal is to scroll a LinkedIn job search page to reveal all possible job listings.
#     The current simplified text view of the page is:
#     --- PAGE STATE (first 4000 chars) ---
#     {simplified_html.get_text(separator='\\n', strip=True)[:4000]}
#     So far, you have found {job_count} jobs.
#     The previous actions you have taken are: {', '.join(previous_actions) if previous_actions else 'None'}.
#     Based on this, what is the best action to take next to find more jobs?
#     Your available actions are:
#     1. "SCROLL_WINDOW": Scroll the main window down. This is the most common action.
#     2. "CLICK <CSS_SELECTOR>": Click a 'load more' button. You must provide a valid CSS selector for the button.
#     3. "STOP": If you believe all jobs have been loaded, you are stuck, or you see text like "you've seen all jobs".
#     Analyze the page state. If you see a "See more jobs" or "Load more" button, choose CLICK. Otherwise, SCROLL_WINDOW is the default safe action.
#     Your response must be ONLY ONE of the actions listed above. For example: `SCROLL_WINDOW` or `CLICK button.jobs-search-results__load-more-button`.
#     """
#     response = client.chat.completions.create(
#         model="gpt-4-turbo-preview",
#         messages=[{"role": "user", "content": prompt}]
#     )
#     action = response.choices[0].message.content.strip()
#     print(f"🤖 AI chose scroll action: {action}")
#     return action


# def get_initial_page_action(client, simplified_html):
#     """
#     Main reasoning function: finds the 'Easy Apply' button and returns the agent action.
#     """
#     print("🤖 AI is performing a two-step page analysis...")

#     # Step 0: Python pre-check for 'Easy Apply' text
#     print("  -> Step 0: Python pre-check for 'Easy Apply' text...")
#     all_text = simplified_html.get_text(separator=' ', strip=True)
#     if "Easy Apply" not in all_text:
#         print("  -> Step 0 Result: 'Easy Apply' not found in page text.")
#         return "FAIL 'Easy Apply' text not found on page."

#     # Step 1: Python search for 'Easy Apply' button agent-id
#     print("  -> Step 1: Python search for 'Easy Apply' button agent-id...")
#     for button in simplified_html.find_all(['button', 'a']):
#         # Check if any child span or the button itself contains 'Easy Apply'
#         if 'Easy Apply' in button.get_text(strip=True):
#             agent_id = button.get('agent-id')
#             if agent_id:
#                 print(f"  -> Step 1 Result: Found agent-id: {agent_id}")
#                 return f"CLICK_EASY_APPLY {agent_id}"
#     print("  -> Step 1 Result: Could not isolate agent-id")
#     return "FAIL Could not isolate agent-id"

# def get_ai_action_for_application(client, simplified_html, application_data):
#     """
#     Asks the AI to decide the next step in filling out an application form.
#     """
#     print("🤖 AI is thinking about how to fill this form...")
#     prompt = f"""
#     You are an expert robotic process automation (RPA) agent. Your goal is to fill out and submit this job application form.
#     Here is your personal data for the application:
#     --- PERSONAL DATA ---
#     {json.dumps(application_data, indent=2)}
#     Here is the current state of the application form's HTML. Interactive elements have a unique `agent-id` attribute.
#     --- FORM HTML (first 6000 chars) ---
#     {simplified_html.prettify()[:6000]}
#     Based on the HTML and your personal data, what is the single next action you should take?
#     Your available actions are:
#     1.  `TYPE <agent-id> <text_to_type>`
#     2.  `SELECT <agent-id> <option_text>`
#     3.  `CLICK <agent-id>`
#     4.  `UPLOAD <agent-id> <file_path>`
#     5.  `ANSWER <agent-id> <question_text>`
#     6.  `SUBMIT <agent-id>`
#     7.  `DONE`
#     8.  `FAIL <reason>`
#     Your response must be a single line in the format `COMMAND agent-id value`. Do not explain.
#     """
#     response = client.chat.completions.create(
#         model="gpt-4-turbo-preview",
#         messages=[{"role": "user", "content": prompt}]
#     )
#     action = response.choices[0].message.content.strip()
#     print(f"🤖 AI chose form action: {action}")
#     return action

# def get_ai_answer_for_question(client, question, story_bank):
#     """
#     Uses the AI and story bank to answer a custom application question.
#     """
#     print(f"🤖 AI is thinking of an answer for: '{question}'...")
#     prompt = f"""
#     You are a career coach helping me answer a job application question.
#     The question is: "{question}"
#     Here is my "Story Bank" with my key career experiences:
#     --- STORY BANK ---
#     {json.dumps(story_bank, indent=2)}
#     Please generate a concise, professional answer to the question. The answer should be a single block of text. Do not add any conversational filler.
#     """
#     response = client.chat.completions.create(
#         model="gpt-4-turbo-preview",
#         messages=[{"role": "user", "content": prompt}]
#     )
#     answer = response.choices[0].message.content.strip()
#     print(f"🤖 AI generated answer: '{(answer[:70] + '...') if len(answer) > 70 else answer}'")
#     return answer