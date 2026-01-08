#!/usr/bin/env python3
"""
Additional Document Scraper for FinBot
Scrapes 5 additional documents from each branch using actual website structure
Includes PDF verification and navigation route capture
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
from src.core.database import DatabaseManager
import re

class AdditionalScraper:
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

    def get_existing_gr_numbers(self, branch):
        """Get existing GR numbers for a branch to avoid duplicates"""
        existing_docs = self.db.get_documents_by_branch(branch)
        return {doc.get('gr_no', '') for doc in existing_docs}

    def get_existing_pdf_urls(self):
        """Get all existing PDF URLs to avoid duplicates"""
        all_docs = self.db.search_documents({})
        return {doc.get('pdf_url', '') for doc in all_docs}

    def scrape_page(self, page_name, page_url):
        """Scrape a specific page for PDF documents"""
        self.add_route_step(f"Home Page → {page_name}")
        print(f"🔍 Scraping {page_name}...")

        try:
            response = self.session.get(page_url, timeout=30)
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
                        'page_source': page_name,
                        'page_url': current_page_url,
                        'navigation_route': self.get_current_route()
                    })

            print(f"Found {len(pdf_links)} PDF links on {page_name}")
            return pdf_links

        except Exception as e:
            print(f"Error scraping {page_name}: {e}")
            return []

    def scrape_gr_page(self):
        """Scrape the GR (Government Resolution) page"""
        return self.scrape_page("GR Page", f"{self.base_url}/gr.html")

    def scrape_notifications_page(self):
        """Scrape the Notifications page"""
        return self.scrape_page("Notifications Page", f"{self.base_url}/Notifications.html")

    def scrape_circulars_page(self):
        """Scrape the Circulars page"""
        return self.scrape_page("Circulars Page", f"{self.base_url}/circulars.html")

    def classify_document_branch(self, text, context, url):
        """Classify document into appropriate branch based on content"""
        combined_text = f"{text} {context}".lower()

        pay_keywords = ['pay', 'salary', 'scale', 'grade', 'allowance', 'increment', 'વेतन', 'पगार']
        commission_keywords = ['commission', 'committee', 'कमीशन', 'समिति']

        if any(keyword in combined_text for keyword in commission_keywords):
            return "PayCell-(Pay Commission)"
        elif any(keyword in combined_text for keyword in pay_keywords):
            return "M-(Pay of Government Employee)"
        else:
            if 'employee' in combined_text or 'service' in combined_text:
                return "M-(Pay of Government Employee)"
            else:
                return "PayCell-(Pay Commission)"

    def extract_document_info(self, pdf_link):
        """Extract document information from PDF link data with verification - GR number is MANDATORY"""
        try:
            url = pdf_link['url']
            text = pdf_link['text']
            context = pdf_link['context']
            page_source = pdf_link.get('page_source', '')
            page_url = pdf_link.get('page_url', '')
            navigation_route = pdf_link.get('navigation_route', '')

            verification = self.verify_pdf_url(url)
            branch = self.classify_document_branch(text, context, url)

            combined_text = f"{text} {context}"
            gr_patterns = [
                r'પગર[^\s]*[\-\/]*\d+[^\s]*',
                r'GR[^\s]*[\-\/]*\d+[^\s]*',
                r'\w+\-\d+\-\d+\-\w+',
                r'[A-Z]+_\d+_[^_]+_\d+',
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
                subject = "Government Document"

            if len(subject) > 200:
                subject = subject[:200] + "..."

            # Build path info with branch and GR number
            path_info = {
                'gr_no': gr_no,
                'branch': branch,
                'source_page': page_source,
                'source_url': page_url,
                'pdf_url': url,
                'route': navigation_route,
                'date': date_str,
                'subject': subject
            }

            # Print debug route info to console
            print(f"\n🛤️ ROUTE DEBUG INFO:")
            print(f"   GR No: {gr_no}")
            print(f"   Branch: {branch}")
            print(f"   Source Page: {page_source}")
            print(f"   Source URL: {page_url}")
            print(f"   PDF URL: {url}")
            print(f"   Route: {navigation_route}")
            print(f"   Status: {verification.get('message', 'Unknown')}")

            return {
                'gr_no': gr_no,
                'date': date_str,
                'subject_en': subject,
                'subject_ur': '',
                'branch': branch,
                'pdf_url': url,
                'pdf_valid': verification['valid'],
                'fallback_url': verification.get('fallback_url'),
                'pdf_status': verification.get('message', 'Unknown'),
                'navigation_route': navigation_route,
                'scraped_at': datetime.now().isoformat(),
                'source_page': page_source,
                'source_page_url': page_url,
                'path_info': path_info  # Include full path info for frontend
            }

        except Exception as e:
            print(f"Error extracting document info: {e}")
            return None

    def save_documents_to_database(self, documents):
        """Save new documents to database"""
        success_count = 0

        docs_with_embeddings = []
        for doc in documents:
            try:
                text_for_embedding = f"{doc.get('subject_en', '')} {doc.get('branch', '')} {doc.get('gr_no', '')}"
                embedding = self.ai.create_embedding(text_for_embedding)

                doc_with_embedding = {
                    'gr_no': doc.get('gr_no', ''),
                    'date': doc.get('date', ''),
                    'subject_en': doc.get('subject_en', ''),
                    'subject_ur': doc.get('subject_ur', ''),
                    'branch': doc.get('branch', ''),
                    'pdf_url': doc.get('pdf_url', ''),
                    'pdf_valid': doc.get('pdf_valid', True),
                    'fallback_url': doc.get('fallback_url', ''),
                    'pdf_status': doc.get('pdf_status', ''),
                    'navigation_route': doc.get('navigation_route', ''),
                    'embedding': embedding
                }
                docs_with_embeddings.append(doc_with_embedding)
                
                pdf_status = "✅" if doc.get('pdf_valid', True) else "⚠️"
                print(f"{pdf_status} Prepared: {doc.get('gr_no', 'Unknown')} ({doc.get('branch', 'Unknown')})")

            except Exception as e:
                print(f"❌ Error preparing document {doc.get('gr_no', 'Unknown')}: {e}")

        if docs_with_embeddings:
            try:
                self.db.insert_documents(docs_with_embeddings)
                success_count = len(docs_with_embeddings)
                print(f"✅ Successfully inserted {success_count} documents into database")
            except Exception as e:
                print(f"❌ Error inserting documents into database: {e}")

        return success_count

    def run_additional_scraping(self):
        """Run the additional scraping process"""
        print("🚀 Starting Additional Document Scraping")
        print("=" * 60)

        existing_urls = self.get_existing_pdf_urls()
        print(f"Existing documents in database: {len(existing_urls)}")

        # Scrape primary pages
        all_pdf_links = []
        all_pdf_links.extend(self.scrape_gr_page())
        time.sleep(2)
        all_pdf_links.extend(self.scrape_notifications_page())
        time.sleep(2)
        all_pdf_links.extend(self.scrape_circulars_page())
        time.sleep(2)
        
        # Scrape fallback pages (in case primary routes are unavailable)
        print("\n🔄 Checking fallback pages...")
        all_pdf_links.extend(self.scrape_circulars_page())  # Circulars fallback
        time.sleep(2)
        all_pdf_links.extend(self.scrape_gr_page())  # GR page fallback
        time.sleep(2)

        print(f"\n📊 Total PDF links found: {len(all_pdf_links)}")

        new_documents = []
        branch_counts = {"M-(Pay of Government Employee)": 0, "PayCell-(Pay Commission)": 0}
        valid_count = 0
        invalid_count = 0

        for pdf_link in all_pdf_links:
            if pdf_link['url'] not in existing_urls:
                doc_info = self.extract_document_info(pdf_link)

                if doc_info:
                    branch = doc_info.get('branch', '')
                    pdf_valid = doc_info.get('pdf_valid', False)
                    
                    if pdf_valid:
                        valid_count += 1
                    else:
                        invalid_count += 1

                    if branch_counts.get(branch, 0) < 5:
                        new_documents.append(doc_info)
                        branch_counts[branch] = branch_counts.get(branch, 0) + 1
                        
                        status_indicator = "✅" if pdf_valid else "⚠️"
                        route = doc_info.get('navigation_route', 'Unknown route')
                        print(f"{status_indicator} New document: {doc_info.get('gr_no', 'Unknown')} ({branch})")
                        if not pdf_valid:
                            print(f"   Route: {route}")

                        if all(count >= 5 for count in branch_counts.values()):
                            break

                time.sleep(0.5)

        if new_documents:
            print(f"\n💾 Saving {len(new_documents)} new documents to database...")
            saved_count = self.save_documents_to_database(new_documents)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_samples/additional_scraped_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(new_documents, f, ensure_ascii=False, indent=2)

            print(f"\n✅ SCRAPING COMPLETE!")
            print(f"📊 New documents by branch:")
            for branch, count in branch_counts.items():
                print(f"   {branch}: {count} documents")
            print(f"📊 PDF Status:")
            print(f"   ✅ Valid PDFs: {valid_count}")
            print(f"   ⚠️  Invalid/Indirect PDFs: {invalid_count}")
            print(f"💾 Successfully saved to database: {saved_count}")
            print(f"📁 Backup saved to: {filename}")

        else:
            print("\n⚠️  No new documents found")

if __name__ == "__main__":
    scraper = AdditionalScraper()
    scraper.run_additional_scraping()

