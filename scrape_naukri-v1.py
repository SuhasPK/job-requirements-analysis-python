from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
from tqdm import tqdm

# Set up the WebDriver with webdriver-manager
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

def extract_job_postings(driver):
    job_postings = driver.find_elements(By.CSS_SELECTOR, 'div.srp-jobtuple-wrapper')
    jobs_data = []

    max_skills_count = 0  # Track the maximum number of skills found

    for job_posting in job_postings:
        try:
            job_title = job_posting.find_element(By.CSS_SELECTOR, 'a.title').text
            company_name = job_posting.find_element(By.CSS_SELECTOR, 'a.comp-name').text
            experience = job_posting.find_element(By.CSS_SELECTOR, 'span.expwdth').text
            salary = job_posting.find_element(By.CSS_SELECTOR, 'span.sal').text
            location = job_posting.find_element(By.CSS_SELECTOR, 'span.locWdth').text
            description = job_posting.find_element(By.CSS_SELECTOR, 'span.job-desc').text
            posted_days_ago = job_posting.find_element(By.CSS_SELECTOR, 'span.job-post-day').text
            
            # Extract skills with error handling for missing skills
            skills_list = []
            try:
                skills_element = job_posting.find_element(By.CSS_SELECTOR, 'ul.tags-gt')
                skills_list = [skill.text for skill in skills_element.find_elements(By.CSS_SELECTOR, 'li.dot-gt')]
            except Exception:
                print("Skills not found for this job posting.")
            
            # Update the maximum number of skills found so far
            max_skills_count = max(max_skills_count, len(skills_list))

            # Append all job details and skills into the jobs_data list
            jobs_data.append({
                "Job Title": job_title,
                "Company Name": company_name,
                "Experience": experience,
                "Salary": salary,
                "Location": location,
                "Description": description,
                "Posted Days Ago": posted_days_ago,
                "Skills": skills_list
            })
        except Exception as e:
            print(f"Error extracting job posting: {e}")
    
    return jobs_data, max_skills_count

def main():
    base_url = 'https://www.naukri.com/data-analyst-jobs-in-bangalore'
    driver.get(base_url)

    # Optionally, wait for the page to load completely
    driver.implicitly_wait(10)  # seconds

    # Start time tracking
    start_time = time.time()

    all_jobs_data = []
    num_pages = 2  # Number of pages to scrape

    max_skills_count = 0

    for page in tqdm(range(1, num_pages + 1), desc="Scraping Pages"):
        try:
            # Extract job postings from the current page
            jobs_data, page_max_skills_count = extract_job_postings(driver)
            all_jobs_data.extend(jobs_data)
            max_skills_count = max(max_skills_count, page_max_skills_count)
            
            # Navigate to the next page if not on the last page
            if page < num_pages:
                next_page_number = page + 1
                next_page_url = f"{base_url}-{next_page_number}"
                driver.get(next_page_url)
                
                # Dynamically wait for the job postings to load on the next page
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.srp-jobtuple-wrapper'))
                )
        except Exception as e:
            print(f"Error during page navigation: {e}")
            break

    # Convert to DataFrame
    df = pd.DataFrame(all_jobs_data)

    # Create skill columns dynamically for each job posting
    for i in range(1, max_skills_count + 1):
        df[f'Skill{i}'] = df['Skills'].apply(lambda x: x[i-1] if i-1 < len(x) else '')

    # Drop the 'Skills' column as it's no longer needed
    df = df.drop(columns=['Skills'])

    # Save DataFrame to CSV
    df.to_csv('job_postings.csv', index=False)

    # End time tracking
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Scraping completed in {elapsed_time:.2f} seconds.")

    # Close the WebDriver
    driver.quit()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Script interrupted by user.")
        driver.quit()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        driver.quit()

