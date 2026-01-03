#!/usr/bin/env python3
"""
Branch-Specific Document Scraper
Uses the GR page branch selector to get 5 documents from each branch
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
from src.core.database import DatabaseManager
import re

class BranchSpecificScraper:
    def __init__(self):
        self.base_url = "https://financedepartment.gujarat.gov.in"
        self.db = DatabaseManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        from src.core.ai import AIManager
        self.ai = AIManager()

    def get_form_data(self):
        """Get initial form data from GR page"""
        try:
            response = self.session.get(f"{self.base_url}/gr.html", timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract form data
            form_data = {}

            # Get hidden inputs
            hidden_inputs = soup.find_all('input', type='hidden')
            for input_elem in hidden_inputs:
                name = input_elem.get('name', '')
                value = input_elem.get('value', '')
                if name:
                    form_data[name] = value

            return form_data

        except Exception as e:
            print(f"Error getting form data: {e}")
            return {}

    def scrape_branch_documents(self, branch_value, branch_name, language='1'):
        """Scrape documents for a specific branch"""
        print(f"\n🔍 Scraping {branch_name} (value: {branch_value})")

        try:
            # Get initial form data
            form_data = self.get_form_data()

            # Set branch and language
            form_data.update({
                'ctl04$ddllang': language,  # 1=English, 2=Gujarati
                'ctl08$ddlbranch': branch_value,
                '__EVENTTARGET': 'ctl08$ddlbranch',
                '__EVENTARGUMENT': ''
            })

            # Make POST request
            response = self.session.post(
                f"{self.base_url}/gr.html",
                data=form_data,
                timeout=30
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for PDF links in the response
            pdf_links = []
            links = soup.find_all('a', href=True)

            for link in links:
                href = link.get('href', '')
                if '.pdf' in href.lower():
                    # Construct full URL
                    if href.startswith('/'):
                        full_url = self.base_url + href
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        full_url = self.base_url + '/' + href.lstrip('/')

                    # Get context text
                    text = link.get_text(strip=True)
                    parent_text = ""
                    parent = link.find_parent()
                    if parent:
                        parent_text = parent.get_text(strip=True)

                    pdf_links.append({
                        'url': full_url,
                        'text': text,
                        'context': parent_text,
                        'branch_name': branch_name,
                        'branch_value': branch_value
                    })

            print(f"   Found {len(pdf_links)} PDF links")
            return pdf_links

        except Exception as e:
            print(f"   Error scraping {branch_name}: {e}")
            return []

    def extract_document_info(self, pdf_link):
        """Extract document information from PDF link data"""
        try:
            url = pdf_link['url']
            text = pdf_link['text']
            context = pdf_link['context']
            branch_name = pdf_link['branch_name']

            # Extract GR number with enhanced patterns
            combined_text = f"{text} {context}"
            gr_patterns = [
                r'પગર[^\s]*[\-\/]*\d+[^\s]*',  # Gujarati GR pattern
                r'GR[^\s]*[\-\/]*\d+[^\s]*',   # English GR pattern
                r'\w+\-\d+\-\d+\-\w+',         # Pattern like M_2641_17-Apr-2023_450
                r'[A-Z]+_\d+_[^_]+_\d+',       # General pattern
                r'Cir_\d+_[^_]+_\d+',          # Circular pattern
                r'Rule_\d+_[^_]+_\d+',         # Rule pattern
                r'Not_\d+_[^_]+_\d+',          # Notification pattern
            ]

            gr_no = "Unknown"
            for pattern in gr_patterns:
                match = re.search(pattern, combined_text)
                if match:
                    gr_no = match.group(0)
                    break

            # If no GR found, extract from URL
            if gr_no == "Unknown":
                url_parts = url.split('/')[-1].replace('.pdf', '').replace('.PDF', '')
                if '_' in url_parts or '-' in url_parts:
                    gr_no = url_parts

            # Extract date
            date_patterns = [
                r'\d{1,2}[-/]\w{3}[-/]\d{2,4}',  # 17-Apr-2023
                r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', # 17/04/2023
                r'\d{4}[-/]\d{1,2}[-/]\d{1,2}'    # 2023-04-17
            ]

            date_str = datetime.now().strftime("%Y-%m-%d")
            for pattern in date_patterns:
                match = re.search(pattern, combined_text)
                if match:
                    date_str = match.group(0)
                    break

            # Extract subject
            subject = text if text and len(text.strip()) > 0 else context
            if not subject or len(subject.strip()) == 0:
                subject = f"{branch_name} Document"

            # Limit subject length
            if len(subject) > 200:
                subject = subject[:200] + "..."

            return {
                'gr_no': gr_no,
                'date': date_str,
                'subject_en': subject,
                'subject_ur': '',
                'branch': branch_name,
                'pdf_url': url,
                'scraped_at': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error extracting document info: {e}")
            return None

    def get_existing_pdf_urls(self):
        """Get all existing PDF URLs to avoid duplicates"""
        all_docs = self.db.search_documents({})
        return {doc.get('pdf_url', '') for doc in all_docs}

    def run_branch_scraping(self, target_per_branch=5):
        """Scrape documents from all branches"""
        print("🚀 STARTING BRANCH-SPECIFIC SCRAPING")
        print("=" * 60)

        # Define all branches from the dropdown
        branches = [
            ('1', 'A-(Public Sector Undertaking)'),
            ('2', 'CH-(Service Matter)'),
            ('3', 'K-(Budget)'),
            ('4', 'M-(Pay of Government Employee)'),
            ('5', 'PayCell-(Pay Commission)'),
            ('6', 'N-(Banking)'),
            ('7', 'P-(Pension)'),
            ('8', 'T-(Local Establishment)'),
            ('9', 'TH-(Value Added Tax)'),
            ('10', 'TH-3-(Commercial Tax Establishment)'),
            ('11', 'Z-(Treasury)'),
            ('12', 'Z-1-(Economy)'),
            ('13', 'G-(Audit Para)'),
            ('14', 'GH-(Accounts Cadre Establishment)'),
            ('15', 'FR-(Financial Resources)'),
            ('16', 'DMO-(Debt Management)'),
            ('17', 'GO Cell-(Government Companies)'),
            ('18', 'B-RTI Cell-(Small Savings RTI)'),
            ('19', 'KH'),
            ('20', 'PMU-Cell'),
            ('1024', 'GST Cell')
        ]

        existing_urls = self.get_existing_pdf_urls()
        print(f"Existing documents in database: {len(existing_urls)}")

        # Track documents by branch
        branch_documents = {}
        all_new_documents = []

        for branch_value, branch_name in branches:
            try:
                # Skip if we already have enough from this branch
                existing_branch_docs = self.db.get_documents_by_branch(branch_name)
                if len(existing_branch_docs) >= 10:  # Already have enough
                    print(f"⏭️  Skipping {branch_name} - already have {len(existing_branch_docs)} documents")
                    continue

                # Scrape this branch
                pdf_links = self.scrape_branch_documents(branch_value, branch_name)

                branch_count = 0
                for pdf_link in pdf_links:
                    if pdf_link['url'] not in existing_urls and branch_count < target_per_branch:
                        doc_info = self.extract_document_info(pdf_link)

                        if doc_info:
                            if branch_name not in branch_documents:
                                branch_documents[branch_name] = []

                            branch_documents[branch_name].append(doc_info)
                            all_new_documents.append(doc_info)
                            existing_urls.add(pdf_link['url'])  # Avoid duplicates in same run
                            branch_count += 1

                            print(f"   ✅ New: {doc_info.get('gr_no', 'Unknown')}")

                time.sleep(3)  # Rate limiting between branches

            except Exception as e:
                print(f"   ❌ Error with {branch_name}: {e}")
                continue

        # Show results
        print(f"\n📊 NEW DOCUMENTS BY BRANCH:")
        print("=" * 50)

        for branch, docs in branch_documents.items():
            print(f"{branch}: {len(docs)} new documents")

        # Save results
        if all_new_documents:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_samples/branch_specific_scraped_{timestamp}.json"

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(all_new_documents, f, ensure_ascii=False, indent=2)

            print(f"\n✅ BRANCH-SPECIFIC SCRAPING COMPLETE!")
            print(f"📊 Total new documents found: {len(all_new_documents)}")
            print(f"🌳 Branches with new documents: {len(branch_documents)}")
            print(f"📁 Backup saved to: {filename}")

            return all_new_documents, filename
        else:
            print("\n⚠️  No new documents found from any branch")
            return [], None

if __name__ == "__main__":
    scraper = BranchSpecificScraper()
    documents, backup_file = scraper.run_branch_scraping(target_per_branch=5)
