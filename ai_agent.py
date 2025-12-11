import openai
from bs4 import BeautifulSoup
import json
from typing import Any, Dict, List
from selenium.webdriver.remote.webdriver import WebDriver

def simplify_html(html_content: str, for_application: bool = False) -> BeautifulSoup:
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

def get_ai_action_for_scrolling(
    client: Any,
    simplified_html: BeautifulSoup,
    previous_actions: List[str],
    job_count: int
) -> str:
    """
    Asks the AI what to do next to find more jobs on a search results page.
    """
    print("🤖 AI is thinking about how to scroll...")
    prompt = (
        "You are an expert web scraping agent. Your goal is to scroll a LinkedIn job search page to reveal all possible job listings.\n"
        "The current simplified text view of the page is:\n"
        "--- PAGE STATE (first 4000 chars) ---\n"
        f"{simplified_html.get_text(separator='\\n', strip=True)[:4000]}\n"
        f"So far, you have found {job_count} jobs.\n"
        f"The previous actions you have taken are: {', '.join(previous_actions) if previous_actions else 'None'}.\n"
        "Based on this, what is the best action to take next to find more jobs?\n"
        "Your available actions are:\n"
        "1. \"SCROLL_WINDOW\": Scroll the main window down. This is the most common action.\n"
        "2. \"CLICK <CSS_SELECTOR>\": Click a 'load more' button. You must provide a valid CSS selector for the button.\n"
        "3. \"STOP\": If you believe all jobs have been loaded, you are stuck, or you see text like \"you've seen all jobs\".\n"
        "Analyze the page state. If you see a \"See more jobs\" or \"Load more\" button, choose CLICK. Otherwise, SCROLL_WINDOW is the default safe action.\n"
        "Your response must be ONLY ONE of the actions listed above. For example: `SCROLL_WINDOW` or `CLICK button.jobs-search-results__load-more-button`."
    )
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[{"role": "user", "content": prompt}]
    )
    action = response.choices[0].message.content.strip()
    print(f"🤖 AI chose scroll action: {action}")
    return action

def get_initial_page_action(client: Any, simplified_html: BeautifulSoup) -> str:
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

def get_ai_action_for_application(
    client: Any,
    simplified_html: BeautifulSoup,
    application_data: Dict[str, Any]
) -> str:
    """
    Asks the AI to decide the next step in filling out an application form.
    """
    print("🤖 AI is thinking about how to fill this form...")
    prompt = (
        "You are an expert robotic process automation (RPA) agent. Your goal is to fill out and submit this job application form.\n"
        "Here is your personal data for the application:\n"
        "--- PERSONAL DATA ---\n"
        f"{json.dumps(application_data, indent=2)}\n"
        "Here is the current state of the application form's HTML. Interactive elements have a unique `agent-id` attribute.\n"
        "--- FORM HTML (first 6000 chars) ---\n"
        f"{simplified_html.prettify()[:6000]}\n"
        "Based on the HTML and your personal data, what is the single next action you should take?\n"
        "Your available actions are:\n"
        "1.  `TYPE <agent-id> <text_to_type>`\n"
        "2.  `SELECT <agent-id> <option_text>`\n"
        "3.  `CLICK <agent-id>`\n"
        "4.  `UPLOAD <agent-id> <file_path>`\n"
        "5.  `ANSWER <agent-id> <question_text>`\n"
        "6.  `SUBMIT <agent-id>`\n"
        "7.  `DONE`\n"
        "8.  `FAIL <reason>`\n"
        "Your response must be a single line in the format `COMMAND agent-id value`. Do not explain."
    )
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[{"role": "user", "content": prompt}]
    )
    action = response.choices[0].message.content.strip()
    print(f"🤖 AI chose form action: {action}")
    return action

def get_ai_answer_for_question(
    client: Any,
    question: str,
    story_bank: List[Dict[str, Any]]
) -> str:
    """
    Uses the AI and story bank to answer a custom application question.
    """
    print(f"🤖 AI is thinking of an answer for: '{question}'...")
    prompt = (
        f"You are a career coach helping me answer a job application question.\n"
        f"The question is: \"{question}\"\n"
        "Here is my \"Story Bank\" with my key career experiences:\n"
        "--- STORY BANK ---\n"
        f"{json.dumps(story_bank, indent=2)}\n"
        "Please generate a concise, professional answer to the question. The answer should be a single block of text. Do not add any conversational filler."
    )
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response.choices[0].message.content.strip()
    print(f"🤖 AI generated answer: '{(answer[:70] + '...') if len(answer) > 70 else answer}'")
    return answer

def click_easy_apply_button(driver: WebDriver, timeout: int = 10) -> None:
    """
    Robustly clicks the 'Easy Apply' button on a LinkedIn job page using Selenium.
    Tries multiple selectors and scrolls into view.
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    print("🔎 Looking for the real 'Easy Apply' button in the browser...")
    selectors = [
        "//button[contains(@class, 'jobs-apply-button') and contains(., 'Easy Apply')]",
        "//button[contains(@class, 'jobs-apply-button')]//span[contains(text(), 'Easy Apply')]/ancestor::button",
        "//button[contains(text(), 'Easy Apply')]",
        "//button[contains(@aria-label, 'Easy Apply')]"
    ]
    for selector in selectors:
        try:
            easy_apply_button = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, selector))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", easy_apply_button)
            easy_apply_button.click()
            print(f"✅ Clicked the real 'Easy Apply' button using selector: {selector}")
            return
        except Exception as e:
            print(f"Selector failed: {selector} ({e})")
            continue
    raise Exception("Could not find or click the 'Easy Apply' button with any known selector.")