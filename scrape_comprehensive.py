#!/usr/bin/env python3
"""
Comprehensive Branch Scraper for FinBot
Finds all branches and scrapes 5 documents from each
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
from src.core.database import DatabaseManager
import re

class ComprehensiveScraper:
    def __init__(self):
        self.base_url = "https://financedepartment.gujarat.gov.in"
        self.db = DatabaseManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        from src.core.ai import AIManager
        self.ai = AIManager()

    def discover_all_document_pages(self):
        """Discover all document pages and sections on the website"""
        print("🔍 DISCOVERING ALL DOCUMENT SECTIONS...")
        print("=" * 60)

        document_pages = []

        # Known document pages
        known_pages = [
            ("GR (Government Resolutions)", "/gr.html"),
            ("Notifications", "/Notifications.html"),
            ("Circulars", "/circulars.html"),
            ("Rules", "/rules.html"),
            ("Budget Documents", "/budget.html"),
            ("Treasury Instructions", "/treasury.html"),
            ("Pension Documents", "/pension.html"),
            ("Finance Code", "/finance-code.html"),
            ("PFMS Documents", "/pfms.html"),
            ("Audit Reports", "/audit.html")
        ]

        # Try to access each known page
        for name, path in known_pages:
            try:
                url = self.base_url + path
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    document_pages.append((name, url))
                    print(f"✅ Found: {name}")
                else:
                    print(f"❌ Not found: {name} (404)")
            except Exception as e:
                print(f"❌ Error checking {name}: {e}")
            time.sleep(1)

        # Also explore the main page for additional links
        try:
            response = self.session.get(self.base_url, timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for additional document links
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True)

                if ('.html' in href and
                    any(word in text.lower() for word in ['document', 'order', 'rule', 'circular', 'notification']) and
                    href not in [page[1] for page in document_pages]):

                    full_url = href if href.startswith('http') else self.base_url + href
                    document_pages.append((text[:30], full_url))
                    print(f"✅ Discovered: {text[:30]}")

        except Exception as e:
            print(f"Error exploring main page: {e}")

        print(f"\n📊 Total document sections found: {len(document_pages)}")
        return document_pages

    def scrape_page_for_pdfs(self, page_name, page_url):
        """Scrape a specific page for PDF documents"""
        print(f"\n🔍 Scraping {page_name}...")

        try:
            response = self.session.get(page_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all PDF links
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
                        'page_source': page_name
                    })

            print(f"   Found {len(pdf_links)} PDF links")
            return pdf_links

        except Exception as e:
            print(f"   Error scraping {page_name}: {e}")
            return []

    def classify_document_branch(self, text, context, url, page_source):
        """Enhanced classification to identify more branches"""
        combined_text = f"{text} {context} {page_source}".lower()

        # Enhanced branch classification
        branch_keywords = {
            "M-(Pay of Government Employee)": [
                'pay', 'salary', 'scale', 'grade', 'allowance', 'increment',
                'employee', 'service', 'વેતન', 'પગાર', 'કર્મચારી'
            ],
            "PayCell-(Pay Commission)": [
                'commission', 'committee', 'pay commission', 'કમિશન', 'સમિતિ'
            ],
            "K-(Budget)": [
                'budget', 'allocation', 'expenditure', 'appropriation',
                'બજેટ', 'ફાળવણી', 'ખર્ચ'
            ],
            "A-(Public Sector Undertaking)": [
                'psu', 'undertaking', 'corporation', 'enterprise', 'company',
                'ઉદ્યોગ', 'કંપની', 'નિગમ'
            ],
            "CH-(Service Matter)": [
                'service', 'recruitment', 'promotion', 'transfer', 'posting',
                'સેવા', 'ભરતી', 'બઢતી'
            ],
            "N-(Banking)": [
                'bank', 'banking', 'treasury', 'deposit', 'account',
                'બેંક', 'ખજાનો', 'ખાતું'
            ],
            "P-(Pension)": [
                'pension', 'retirement', 'gratuity', 'provident fund',
                'પેન્શન', 'નિવૃત્તિ', 'ભવિષ્ય નિધિ'
            ],
            "T-(Treasury)": [
                'treasury', 'cash', 'payment', 'receipt', 'transaction',
                'ખજાનો', 'રોકડ', 'ચુકવણી'
            ],
            "F-(Finance Code)": [
                'finance code', 'financial rules', 'procedure', 'manual',
                'નાણાકીય નિયમો', 'કોડ'
            ],
            "AU-(Audit)": [
                'audit', 'inspection', 'examination', 'review',
                'ઓડિટ', 'તપાસ', 'નિરીક્ષણ'
            ]
        }

        # Check for specific keywords
        for branch, keywords in branch_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                return branch

        # Default classification based on page source
        if 'gr' in page_source.lower() or 'resolution' in page_source.lower():
            return "M-(Pay of Government Employee)"
        elif 'circular' in page_source.lower():
            return "PayCell-(Pay Commission)"
        elif 'budget' in page_source.lower():
            return "K-(Budget)"
        elif 'treasury' in page_source.lower():
            return "T-(Treasury)"
        elif 'pension' in page_source.lower():
            return "P-(Pension)"
        elif 'audit' in page_source.lower():
            return "AU-(Audit)"
        else:
            return "M-(Pay of Government Employee)"  # Default

    def extract_document_info(self, pdf_link):
        """Extract document information from PDF link data"""
        try:
            url = pdf_link['url']
            text = pdf_link['text']
            context = pdf_link['context']
            page_source = pdf_link['page_source']

            # Determine branch with enhanced classification
            branch = self.classify_document_branch(text, context, url, page_source)

            # Extract GR number with more patterns
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
                subject = f"{page_source} Document"

            # Limit subject length
            if len(subject) > 200:
                subject = subject[:200] + "..."

            return {
                'gr_no': gr_no,
                'date': date_str,
                'subject_en': subject,
                'subject_ur': '',
                'branch': branch,
                'pdf_url': url,
                'scraped_at': datetime.now().isoformat(),
                'source_page': page_source
            }

        except Exception as e:
            print(f"Error extracting document info: {e}")
            return None

    def get_existing_pdf_urls(self):
        """Get all existing PDF URLs to avoid duplicates"""
        all_docs = self.db.search_documents({})
        return {doc.get('pdf_url', '') for doc in all_docs}

    def run_comprehensive_scraping(self, target_per_branch=5):
        """Run comprehensive scraping to get documents from all branches"""
        print("🚀 STARTING COMPREHENSIVE BRANCH SCRAPING")
        print("=" * 60)

        # Discover all document pages
        document_pages = self.discover_all_document_pages()

        existing_urls = self.get_existing_pdf_urls()
        print(f"Existing documents in database: {len(existing_urls)}")

        # Scrape all pages for PDF links
        all_pdf_links = []
        for page_name, page_url in document_pages:
            pdf_links = self.scrape_page_for_pdfs(page_name, page_url)
            all_pdf_links.extend(pdf_links)
            time.sleep(2)  # Rate limiting

        print(f"\n📊 Total PDF links found: {len(all_pdf_links)}")

        # Process documents and organize by branch
        branch_documents = {}

        for pdf_link in all_pdf_links:
            if pdf_link['url'] not in existing_urls:
                doc_info = self.extract_document_info(pdf_link)

                if doc_info:
                    branch = doc_info.get('branch', 'Unknown')

                    if branch not in branch_documents:
                        branch_documents[branch] = []

                    # Only add if we haven't reached the target for this branch
                    if len(branch_documents[branch]) < target_per_branch:
                        branch_documents[branch].append(doc_info)
                        print(f"✅ New: {doc_info.get('gr_no', 'Unknown')} ({branch})")

                time.sleep(0.5)  # Rate limiting

        # Show results by branch
        print(f"\n📊 NEW DOCUMENTS BY BRANCH:")
        print("=" * 50)
        all_new_documents = []

        for branch, docs in branch_documents.items():
            print(f"{branch}: {len(docs)} documents")
            all_new_documents.extend(docs)

        # Save results
        if all_new_documents:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_samples/comprehensive_scraped_{timestamp}.json"

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(all_new_documents, f, ensure_ascii=False, indent=2)

            print(f"\n✅ COMPREHENSIVE SCRAPING COMPLETE!")
            print(f"📊 Total new documents found: {len(all_new_documents)}")
            print(f"🌳 Branches discovered: {len(branch_documents)}")
            print(f"📁 Backup saved to: {filename}")

            return all_new_documents, filename
        else:
            print("\n⚠️  No new documents found")
            return [], None

if __name__ == "__main__":
    scraper = ComprehensiveScraper()
    documents, backup_file = scraper.run_comprehensive_scraping(target_per_branch=5)
