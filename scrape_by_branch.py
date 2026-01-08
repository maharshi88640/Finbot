#!/usr/bin/env python3
"""
Branch-Specific Document Scraper
Uses the GR page branch selector to get 5 documents from each branch
Includes PDF verification and navigation route capture
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
        
        # Navigation route tracking
        self.navigation_route = []

    def add_route_step(self, step):
        """Add a step to the navigation route"""
        self.navigation_route.append({
            'step': len(self.navigation_route) + 1,
            'description': step,
            'timestamp': datetime.now().isoformat()
        })

    def get_current_route(self):
        """Get the current navigation route as a formatted string"""
        if not self.navigation_route:
            return ""
        
        route_str = " → ".join([step['description'] for step in self.navigation_route])
        self.navigation_route = []  # Reset for next document
        return route_str

    def verify_pdf_url(self, pdf_url):
        """Verify if PDF URL is accessible and return status with fallback page info"""
        try:
            # Try HEAD request first
            response = self.session.head(pdf_url, timeout=10, allow_redirects=True)
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                content_length = response.headers.get('Content-Length', 0)
                if 'pdf' in content_type.lower() or int(content_length) > 0:
                    return {
                        'valid': True, 
                        'url': pdf_url, 
                        'status_code': response.status_code,
                        'fallback_url': None,
                        'message': 'PDF accessible directly'
                    }
            
            # Try GET request if HEAD fails
            response = self.session.get(pdf_url, timeout=15, stream=True)
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                
                if 'pdf' in content_type.lower():
                    return {
                        'valid': True, 
                        'url': pdf_url, 
                        'status_code': response.status_code,
                        'fallback_url': None,
                        'message': 'PDF accessible directly'
                    }
                else:
                    return {
                        'valid': False, 
                        'url': pdf_url, 
                        'status_code': response.status_code,
                        'fallback_url': response.url,
                        'message': 'PDF not directly accessible - use fallback page link'
                    }
            
            return {
                'valid': False, 
                'url': pdf_url, 
                'status_code': response.status_code,
                'fallback_url': None,
                'message': f'PDF not accessible (HTTP {response.status_code})'
            }
            
        except requests.exceptions.Timeout:
            return {
                'valid': False, 
                'url': pdf_url, 
                'error': 'Request timeout',
                'fallback_url': None,
                'message': 'Request timed out - try accessing via fallback page'
            }
        except requests.exceptions.ConnectionError:
            return {
                'valid': False, 
                'url': pdf_url, 
                'error': 'Connection error',
                'fallback_url': None,
                'message': 'Connection error - try accessing via fallback page'
            }
        except Exception as e:
            return {
                'valid': False, 
                'url': pdf_url, 
                'error': str(e),
                'fallback_url': None,
                'message': f'Error: {str(e)}'
            }

    def get_form_data(self):
        """Get initial form data from GR page"""
        try:
            self.add_route_step("Home Page")
            response = self.session.get(f"{self.base_url}/gr.html", timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            form_data = {}

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
        self.add_route_step(f"Home Page → GR Page → {branch_name}")
        print(f"\n🔍 Scraping {branch_name} (value: {branch_value})")

        try:
            form_data = self.get_form_data()

            form_data.update({
                'ctl04$ddllang': language,
                'ctl08$ddlbranch': branch_value,
                '__EVENTTARGET': 'ctl08$ddlbranch',
                '__EVENTARGUMENT': ''
            })

            response = self.session.post(
                f"{self.base_url}/gr.html",
                data=form_data,
                timeout=30
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            current_page_url = response.url

            pdf_links = []
            links = soup.find_all('a', href=True)

            for link in links:
                href = link.get('href', '')
                if '.pdf' in href.lower():
                    if href.startswith('/'):
                        full_url = self.base_url + href
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        full_url = self.base_url + '/' + href.lstrip('/')

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
                        'branch_value': branch_value,
                        'page_url': current_page_url,
                        'navigation_route': self.get_current_route()
                    })

            print(f"   Found {len(pdf_links)} PDF links")
            return pdf_links

        except Exception as e:
            print(f"   Error scraping {branch_name}: {e}")
            return []

    def extract_document_info(self, pdf_link):
        """Extract document information from PDF link data with verification"""
        try:
            url = pdf_link['url']
            text = pdf_link['text']
            context = pdf_link['context']
            branch_name = pdf_link['branch_name']
            page_url = pdf_link.get('page_url', '')
            navigation_route = pdf_link.get('navigation_route', '')

            verification = self.verify_pdf_url(url)

            combined_text = f"{text} {context}"
            gr_patterns = [
                r'પગર[^\s]*[\-\/]*\d+[^\s]*',
                r'GR[^\s]*[\-\/]*\d+[^\s]*',
                r'\w+\-\d+\-\d+\-\w+',
                r'[A-Z]+_\d+_[^_]+_\d+',
                r'Cir_\d+_[^_]+_\d+',
                r'Rule_\d+_[^_]+_\d+',
                r'Not_\d+_[^_]+_\d+',
            ]

            gr_no = None
            for pattern in gr_patterns:
                match = re.search(pattern, combined_text)
                if match:
                    gr_no = match.group(0)
                    break

            # If no GR found, extract from URL - MANDATORY
            if not gr_no:
                url_parts = url.split('/')[-1].replace('.pdf', '').replace('.PDF', '')
                if '_' in url_parts or '-' in url_parts:
                    gr_no = url_parts
                else:
                    # Generate fallback GR number from URL
                    url_hash = hash(url) % 100000
                    page_type = "DOC"
                    if 'circular' in url.lower():
                        page_type = "Cir"
                    elif 'gr' in url.lower():
                        page_type = "GR"
                    elif 'rule' in url.lower():
                        page_type = "Rule"
                    elif 'notification' in url.lower():
                        page_type = "Not"
                    gr_no = f"{page_type}_{url_hash}"

            date_patterns = [
                r'\d{1,2}[-/]\w{3}[-/]\d{2,4}',
                r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
                r'\d{4}[-/]\d{1,2}[-/]\d{1,2}'
            ]

            date_str = datetime.now().strftime("%Y-%m-%d")
            for pattern in date_patterns:
                match = re.search(pattern, combined_text)
                if match:
                    date_str = match.group(0)
                    break

            subject = text if text and len(text.strip()) > 0 else context
            if not subject or len(subject.strip()) == 0:
                subject = f"{branch_name} Document"

            if len(subject) > 200:
                subject = subject[:200] + "..."

            return {
                'gr_no': gr_no,
                'date': date_str,
                'subject_en': subject,
                'subject_ur': '',
                'branch': branch_name,
                'pdf_url': url,
                'pdf_valid': verification['valid'],
                'fallback_url': verification.get('fallback_url'),
                'pdf_status': verification.get('message', 'Unknown'),
                'navigation_route': navigation_route,
                'scraped_at': datetime.now().isoformat(),
                'source_page_url': page_url
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

        branch_documents = {}
        all_new_documents = []
        valid_count = 0
        invalid_count = 0

        for branch_value, branch_name in branches:
            try:
                existing_branch_docs = self.db.get_documents_by_branch(branch_name)
                if len(existing_branch_docs) >= 10:
                    print(f"⏭️  Skipping {branch_name} - already have {len(existing_branch_docs)} documents")
                    continue

                pdf_links = self.scrape_branch_documents(branch_value, branch_name)

                branch_count = 0
                for pdf_link in pdf_links:
                    if pdf_link['url'] not in existing_urls and branch_count < target_per_branch:
                        doc_info = self.extract_document_info(pdf_link)

                        if doc_info:
                            pdf_valid = doc_info.get('pdf_valid', False)
                            if pdf_valid:
                                valid_count += 1
                            else:
                                invalid_count += 1
                            
                            if branch_name not in branch_documents:
                                branch_documents[branch_name] = []

                            branch_documents[branch_name].append(doc_info)
                            all_new_documents.append(doc_info)
                            existing_urls.add(pdf_link['url'])
                            branch_count += 1

                            status_indicator = "✅" if pdf_valid else "⚠️"
                            route = doc_info.get('navigation_route', 'Unknown route')
                            print(f"   {status_indicator} New: {doc_info.get('gr_no', 'Unknown')}")
                            if not pdf_valid:
                                print(f"      Route: {route}")

                time.sleep(3)

            except Exception as e:
                print(f"   ❌ Error with {branch_name}: {e}")
                continue

        print(f"\n📊 NEW DOCUMENTS BY BRANCH:")
        print("=" * 50)

        for branch, docs in branch_documents.items():
            print(f"{branch}: {len(docs)} new documents")

        print(f"\n📊 PDF STATUS SUMMARY:")
        print(f"   ✅ Valid PDFs: {valid_count}")
        print(f"   ⚠️  Invalid/Indirect PDFs: {invalid_count}")
        print(f"   📁 Navigation routes saved for all documents")

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

