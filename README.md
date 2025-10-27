# Personal AI Job Application Bot

This project is a sophisticated, AI-powered automation tool designed to streamline the job application process. The bot automates searching for jobs on LinkedIn, filtering them based on custom criteria, using AI to tailor application materials, and applying to "Easy Apply" positions.

This is a personal tool and is intended to be run and configured for a single user.

## Features

-   **Automated Job Scraping:** Uses an AI agent to dynamically scrape job listings from LinkedIn.
-   **Smart Filtering:** Filters scraped jobs based on user-defined inclusion and exclusion keywords.
-   **AI-Powered Content Generation:** Leverages the OpenAI GPT-4 API to:
    -   Tailor your resume's summary and experience for each specific job description.
    -   Generate a unique, professional cover letter for each application.
-   **Autonomous Application Agent:** An AI agent that can:
    -   Intelligently identify the "Easy Apply" button on a job page.
    -   Navigate the multi-step "Easy Apply" modal.
    -   Fill in standard fields (e.g., phone number).
    -   Upload your resume.
    -   Use a "Story Bank" to answer custom behavioral questions on the fly.
-   **Secure & Configurable:** All personal data and credentials are kept separate from the code in configuration files (`profile.yml`, `.env`).
-   **Robust Workflow:** Includes a main menu and logging to track application status.

## Technology Stack

-   **Language:** Python 3
-   **Core Libraries:**
    -   **Web Automation:** `Selenium`
    -   **AI Integration:** `OpenAI`
    -   **HTML Parsing:** `BeautifulSoup4`
    -   **Configuration:** `PyYAML`, `python-dotenv`
    -   **Data Handling:** `Pandas`

## Setup & Installation

Follow these steps to set up the project on your local machine.

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/job_bot.git
cd job_bot
```

### 2. Set Up a Python Virtual Environment

It is highly recommended to use a virtual environment to manage dependencies.

```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install Dependencies

Install all required Python libraries using the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

### 4. Install ChromeDriver

This bot uses Selenium to control a Chrome browser.
1.  Check your Chrome browser version (`Settings` > `About Chrome`).
2.  Download the matching **ChromeDriver** from the [Chrome for Testing availability page](https://googlechromelabs.github.io/chrome-for-testing/).
3.  Unzip the file and place the `chromedriver` executable inside the root of the `job_bot` project folder.

### 5. Configure Your Credentials (`.env`)

Create a `.env` file to store your secret credentials.
1.  Copy the sample file: `cp sample.env .env` (on Mac/Linux) or `copy sample.env .env` (on Windows).
2.  Open the `.env` file and fill in your `LINKEDIN_EMAIL`, `LINKEDIN_PASSWORD`, and `OPENAI_API_KEY`.

### 6. Configure Your Profile (`profile.yml`)

This is the most important step for personalizing the bot. Open `profile.yml` and fill out all sections with your information:
-   `personal_info`: Your name, contact details, etc.
-   `job_search_criteria`: Keywords and locations for your job search.
-   `resume_path`: The **absolute file path** to your master resume (`.pdf` or `.docx`).
-   `resume_data`: Your resume in a structured format. Be detailed here for the best AI results.
-   `story_bank`: Your career stories for answering behavioral questions using the STAR method.

## How to Run the Bot

Once everything is set up, you can run the bot with a single command from your terminal (make sure your virtual environment is active).

```bash
python main.py
```

You will be presented with a menu:

-   **Option 1:** Runs the full end-to-end process: scrapes new jobs, filters them, and starts the application process.
-   **Option 2:** Skips the scraping step and uses the `scraped_jobs.csv` from the last run. This is useful for testing or re-running the AI/application steps.

The bot will ask for your confirmation (`y/n/skip`) before applying to each job.

## Important Notes

-   **Maintenance:** Web scrapers are fragile. If LinkedIn updates its website, the selectors in `scraper.py` or `application_bot.py` may need to be updated.
-   **Safety:** The application agent is configured to **simulate** the final "Submit" click for safety. To enable real submissions, you must uncomment the `target_element.click()` line in `application_bot.py`. Use this at your own risk and after verifying the bot's behavior.
-   **Security:** The `.gitignore` file is configured to prevent your `.env` file and other sensitive information from being committed to Git. **Do not modify it to track the `.env` file.**