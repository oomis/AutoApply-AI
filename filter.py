# filter.py

import pandas as pd

def filter_jobs(config):
    """
    Reads the scraped jobs, filters them based on exclusion keywords,
    and returns a clean DataFrame of jobs to apply for.
    """
    try:
        df = pd.read_csv('scraped_jobs.csv')
        print(f"📄 Found {len(df)} jobs in scraped_jobs.csv")
    except FileNotFoundError:
        print("❌ scraped_jobs.csv not found. Please run the scraper first.")
        return None

    # Get exclusion keywords from config, convert to lowercase for case-insensitive matching
    exclusion_keywords = [k.lower() for k in config['job_search_criteria']['exclusion_keywords']]
    
    print(f"Filtering based on {len(exclusion_keywords)} exclusion keywords: {', '.join(exclusion_keywords)}")

    # Keep track of jobs that are filtered out and why
    filtered_out_jobs = []

    def is_excluded(row):
        # Combine title and description for a comprehensive check
        text_to_check = (str(row['title']) + ' ' + str(row['description'])).lower()
        for keyword in exclusion_keywords:
            if keyword in text_to_check:
                filtered_out_jobs.append({
                    "title": row['title'],
                    "reason": f"Contains excluded keyword: '{keyword}'"
                })
                return True # Exclude this row
        return False # Do not exclude this row

    # Apply the filter function
    # The ~ operator inverts the boolean mask, so we keep rows where is_excluded is False.
    original_count = len(df)
    df_filtered = df[~df.apply(is_excluded, axis=1)]
    
    print("\n--- Filtering Report ---")
    for job in filtered_out_jobs:
        print(f"  -> Rejected: '{job['title']}' (Reason: {job['reason']})")
    
    print(f"\n✅ Filtering complete. Kept {len(df_filtered)} out of {original_count} jobs.")

    # Save the good jobs to a new CSV
    if not df_filtered.empty:
        df_filtered.to_csv('filtered_jobs.csv', index=False)
        print("✅ Filtered jobs saved to filtered_jobs.csv")
    
    return df_filtered