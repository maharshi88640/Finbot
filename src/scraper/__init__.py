"""
Web scraping module for FinBot
Handles scraping financial documents from government websites
"""

import os
from typing import List, Dict, Any
from datetime import datetime
from deep_translator import GoogleTranslator
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.config import Config
from src.core.database import DatabaseManager

class WebScraper:
    """Handles web scraping operations"""

    def __init__(self):
        self.db = DatabaseManager()
        self.base_url = Config.SCRAPE_BASE_URL

    def _setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome WebDriver"""
        options = webdriver.ChromeOptions()

        # Download directory for PDFs
        download_dir = os.path.abspath("pdfs")
        os.makedirs(download_dir, exist_ok=True)

        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
        }

        options.add_experimental_option("prefs", prefs)

        if Config.CHROME_HEADLESS:
            options.add_argument("--headless=new")

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        return webdriver.Chrome(options=options)

    def _click_dropdown_menu(self, driver: webdriver.Chrome):
        """Click dropdown menu"""
        dropdown_menu = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "jqTransformSelectWrapper"))
        )
        dropdown_menu.click()

    def _get_ul_element(self, driver: webdriver.Chrome):
        """Get dropdown ul element"""
        return WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@class='jqTransformSelectWrapper']//ul")
            )
        )

    def _translate_subject(self, subject: str) -> Dict[str, str]:
        """Translate subject to English and Gujarati"""
        try:
            subject_en = GoogleTranslator(source="auto", target="en").translate(subject)
            subject_gu = GoogleTranslator(source="auto", target="gu").translate(subject)
            return {"en": subject_en, "gu": subject_gu}
        except Exception as e:
            print(f"Translation error: {e}")
            return {"en": subject, "gu": subject}

    def scrape_branch(self, driver: webdriver.Chrome, branch_name: str, max_records: int = None) -> List[Dict[str, Any]]:
        """Scrape documents from a specific branch"""
        print(f"🏢 Processing branch: {branch_name}")

        # Wait for table to load
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "table"))
        )
        soup = BeautifulSoup(table.get_attribute("outerHTML"), "html.parser")

        branch_data = []
        rows = soup.find_all("tr")
        print(f"📄 Found {len(rows)} rows in {branch_name}")

        processed_count = 0
        for row in rows:
            if max_records and processed_count >= max_records:
                break

            cols = row.find_all("td")
            if len(cols) == 4:
                gr_no = cols[0].text.strip()
                date = cols[1].text.strip()
                subject = cols[2].text.strip()
                pdf_link = cols[3].find("a")["href"] if cols[3].find("a") else None

                # Translate subjects
                translations = self._translate_subject(subject)

                pdf_url = f"https://financedepartment.gujarat.gov.in/{pdf_link}" if pdf_link else None

                record = {
                    "gr_no": gr_no,
                    "date": date,
                    "branch": branch_name,
                    "subject_en": translations["en"],
                    "subject_gu": translations["gu"],
                    "pdf_url": pdf_url
                }

                branch_data.append(record)
                processed_count += 1

                if processed_count % 10 == 0:
                    print(f"  📝 Processed {processed_count} records...")

        print(f"✅ Completed {branch_name}: {len(branch_data)} records")
        return branch_data

    def scrape_all_branches(self, max_branches: int = None, max_records_per_branch: int = None, save_to_db: bool = True) -> List[Dict[str, Any]]:
        """Scrape all branches"""
        print("🕷️ Starting full scraping...")

        driver = self._setup_driver()
        all_data = []

        try:
            driver.get(self.base_url)
            print("✅ Page loaded successfully")

            self._click_dropdown_menu(driver)
            ul_element = self._get_ul_element(driver)
            li_elements = ul_element.find_elements(By.TAG_NAME, "li")

            # Skip first 3 and last 2 elements (usually headers/footers)
            start_idx = 3
            end_idx = len(li_elements) - 2

            if max_branches:
                end_idx = min(start_idx + max_branches, end_idx)

            total_branches = end_idx - start_idx
            print(f"📋 Processing {total_branches} branches")

            for i in range(start_idx, end_idx):
                if i != start_idx:  # Reopen dropdown for subsequent branches
                    self._click_dropdown_menu(driver)
                    WebDriverWait(driver, 5).until(EC.visibility_of(self._get_ul_element(driver)))
                    li_elements = self._get_ul_element(driver).find_elements(By.TAG_NAME, "li")

                branch = li_elements[i].get_attribute("innerText")
                branch_num = i - start_idx + 1
                print(f"\n🏢 Branch {branch_num}/{total_branches}: {branch}")

                driver.execute_script("arguments[0].scrollIntoView();", li_elements[i])
                WebDriverWait(driver, 5).until(EC.element_to_be_clickable(li_elements[i])).click()

                # Scrape branch data
                branch_data = self.scrape_branch(driver, branch, max_records_per_branch)
                all_data.extend(branch_data)

                # Save to database in batches
                if save_to_db and branch_data:
                    success = self.db.insert_documents(branch_data)
                    if success:
                        print(f"  💾 Saved {len(branch_data)} records to database")
                    else:
                        print(f"  ❌ Failed to save records to database")

        except Exception as e:
            print(f"❌ Scraping error: {e}")
        finally:
            driver.quit()
            print("🔒 Browser closed")

        print(f"\n🎉 Scraping completed! Total records: {len(all_data)}")
        return all_data

    def scrape_sample(self, num_branches: int = 2, records_per_branch: int = 10) -> List[Dict[str, Any]]:
        """Scrape a small sample for testing"""
        print(f"🧪 Scraping sample: {num_branches} branches, {records_per_branch} records each")
        return self.scrape_all_branches(
            max_branches=num_branches,
            max_records_per_branch=records_per_branch,
            save_to_db=True
        )
