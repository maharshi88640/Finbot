#!/usr/bin/env python3
"""
Real Document Scraper for Gujarat Finance Department
Finds and verifies actual PDF documents from the website
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
from src.core.database import DatabaseManager
import re
import os
from urllib.parse import urljoin

class RealDocumentScraper:
    def __init__(self):
        self.base_url = "https://financedepartment.gujarat.gov.in"
        self.db = DatabaseManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })

    def verify_pdf(self, pdf_url, timeout=10):
        """Verify if PDF URL is accessible and returns valid PDF"""
        try:
            response = self.session.head(pdf_url, timeout=timeout, allow_redirects=True)
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '').lower()
                content_length = response.headers.get('Content-Length', '0')
                
                if 'pdf' in content_type or int(content_length) > 1000:
                    return {
                        'valid': True,
                        'url': pdf_url,
                        'status_code': response.status_code,
                        'message': 'PDF accessible directly'
                    }
            
            # Try GET request for more details
            response = self.session.get(pdf_url, timeout=15, stream=True)
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '').lower()
                if 'pdf' in content_type:
                    return {
                        'valid': True,
                        'url': pdf_url,
                        'status_code': response.status_code,
                        'message': 'PDF accessible directly'
                    }
                else:
                    return {
                        'valid': False,
                        'url': pdf_url,
                        'status_code': response.status_code,
                        'fallback_url': response.url,
                        'message': 'Content is not a PDF'
                    }
            
            return {
                'valid': False,
                'url': pdf_url,
                'status_code': response.status_code,
                'message': f'HTTP {response.status_code}'
            }
            
        except requests.exceptions.Timeout:
            return {'valid': False, 'url': pdf_url, 'message': 'Request timeout'}
        except requests.exceptions.ConnectionError:
            return {'valid': False, 'url': pdf_url, 'message': 'Connection error'}
        except Exception as e:
            return {'valid': False, 'url': pdf_url, 'message': str(e)}

    def extract_gr_number(self, text, url):
        """Extract GR number from text or URL - GR number is MANDATORY"""
        combined = f"{text} {url}"
        
        patterns = [
            r'GR[-_]?\d+[-_]?\d+[-_]?\w+',
            r'[A-Z]+[-_]\d+[-_]\d+[-_]\d+',
            r'[A-Z]+_\d+_[^_]+_\d+',
            r'Rule[-_]?\d+[-_]?\w+',
            r'Not[-_]?\d+[-_]?\w+',
            r'Cir[-_]?\d+[-_]?\w+',
            r'\d{4}[-_]\d{4}[-_]\w+',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                return match.group(0)
        
        # Extract from URL filename - MANDATORY
        url_parts = url.split('/')[-1].replace('.pdf', '').replace('.PDF', '')
        if url_parts and len(url_parts) > 3:
            # Clean up the filename to create a valid GR-like number
            gr_like = re.sub(r'[^A-Za-z0-9\-_]', '-', url_parts)
            gr_like = re.sub(r'-+', '-', gr_like).strip('-')
            if len(gr_like) > 5:
                return gr_like
        
        # Final fallback - generate from URL structure
        # Format: PageType_DocumentNumber (e.g., Circular_123)
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
        elif 'budget' in url.lower():
            page_type = "Bud"
        
        return f"{page_type}_{url_hash}"

    def extract_date(self, text):
        """Extract date from text"""
        if not text:
            return datetime.now().strftime("%Y-%m-%d")
        
        date_patterns = [
            r'\d{1,2}[-/]\w{3}[-/]\d{2,4}',
            r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
            r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return datetime.now().strftime("%Y-%m-%d")

    def extract_branch(self, text, url, context=""):
        """Classify document into appropriate branch"""
        combined = f"{text} {context} {url}".lower()
        
        branch_keywords = {
            "M-(Pay of Government Employee)": ['pay', 'salary', 'scale', 'grade', 'allowance', 'increment', 'employee', 'service'],
            "PayCell-(Pay Commission)": ['commission', 'committee', 'pay commission'],
            "K-(Budget)": ['budget', 'allocation', 'expenditure', 'appropriation'],
            "A-(Public Sector Undertaking)": ['psu', 'undertaking', 'corporation', 'company'],
            "CH-(Service Matter)": ['service', 'recruitment', 'promotion', 'transfer', 'posting'],
            "N-(Banking)": ['bank', 'banking', 'treasury', 'deposit'],
            "P-(Pension)": ['pension', 'retirement', 'gratuity', 'provident'],
            "T-(Treasury)": ['treasury', 'cash', 'payment', 'receipt'],
            "F-(Finance Code)": ['finance code', 'financial rules', 'procedure', 'manual'],
            "AU-(Audit)": ['audit', 'inspection', 'examination'],
            "Z-(Economy)": ['economy', 'economic'],
            "GST Cell": ['gst', 'goods and service tax'],
        }
        
        for branch, keywords in branch_keywords.items():
            if any(kw in combined for kw in keywords):
                return branch
        
        # Default based on URL patterns
        if 'rule' in url.lower():
            return "F-(Finance Code)"
        elif 'notif' in url.lower():
            return "PayCell-(Pay Commission)"
        elif 'circular' in url.lower():
            return "PayCell-(Pay Commission)"
        elif 'gr' in url.lower():
            return "M-(Pay of Government Employee)"
        else:
            return "M-(Pay of Government Employee)"

    def extract_subject(self, text, url):
        """Extract subject from text or generate from URL"""
        if text and len(text.strip()) > 3:
            # Clean up text
            subject = re.sub(r'\s+', ' ', text.strip())
            if len(subject) > 200:
                subject = subject[:200] + "..."
            return subject
        
        # Generate from URL
        filename = url.split('/')[-1].replace('.pdf', '').replace('.PDF', '')
        filename = re.sub(r'[-_]', ' ', filename)
        return filename[:200] if filename else "Government Document"

    def get_navigation_route(self, url, page_name):
        """Generate navigation route to document"""
        return f"Home Page → {page_name} → Document"

    def scrape_documents_folder(self):
        """Try to list documents from the Documents folder"""
        print("📁 Checking Documents folder...")
        
        documents = []
        
        # Try common document patterns
        base_doc_url = f"{self.base_url}/Documents/"
        
        # Common PDF naming patterns (these are real files found on the site)
        known_pdfs = [
            "Rule-Eng_34_2018-11-13_920.pdf",
        ]
        
        # We'll find more by scraping the main pages
        return documents

    def scrape_page_for_pdfs(self, page_name, page_url, max_pdfs=10):
        """Scrape a page for PDF links"""
        print(f"\n🔍 Scraping: {page_name}")
        
        try:
            response = self.session.get(page_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            pdf_links = []
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link.get('href', '')
                
                if '.pdf' in href.lower():
                    # Construct full URL
                    if href.startswith('/'):
                        full_url = urljoin(self.base_url, href)
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        full_url = urljoin(self.base_url, href)
                    
                    # Get link text
                    text = link.get_text(strip=True)
                    if not text:
                        # Try parent
                        parent = link.find_parent(['div', 'p', 'td', 'li', 'span'])
                        if parent:
                            text = parent.get_text(strip=True)
                    
                    # Get context
                    context = ""
                    container = link.find_parent(['div', 'td', 'li'])
                    if container:
                        context = container.get_text(strip=True)[:100]
                    
                    if full_url not in [p['url'] for p in pdf_links]:
                        pdf_links.append({
                            'url': full_url,
                            'text': text,
                            'context': context,
                            'page_name': page_name,
                            'page_url': page_url
                        })
            
            print(f"   Found {len(pdf_links)} PDF links")
            
            # Verify and process PDFs
            verified_docs = []
            for pdf in pdf_links[:max_pdfs]:
                verification = self.verify_pdf(pdf['url'])
                
                if verification['valid']:
                    gr_no = self.extract_gr_number(pdf['text'], pdf['url'])
                    date = self.extract_date(pdf['text'])
                    branch = self.extract_branch(pdf['text'], pdf['url'], pdf['context'])
                    subject = self.extract_subject(pdf['text'], pdf['url'])
                    
                    doc = {
                        'gr_no': gr_no,
                        'date': date,
                        'branch': branch,
                        'subject_en': subject,
                        'pdf_url': pdf['url'],
                        'pdf_valid': True,
                        'fallback_url': None,
                        'pdf_status': 'Accessible',
                        'navigation_route': self.get_navigation_route(pdf['url'], pdf['page_name']),
                        'scraped_at': datetime.now().isoformat(),
                        'source_page': pdf['page_name'],
                        'source_page_url': pdf['page_url']
                    }
                    
                    verified_docs.append(doc)
                    print(f"   ✅ {gr_no} - {date}")
            
            return verified_docs
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return []

    def scrape_all_pages(self, max_per_page=5):
        """Scrape all known pages for PDFs"""
        print("🚀 STARTING REAL DOCUMENT SCRAPING")
        print("=" * 60)
        
        pages = [
            ("Home Page", f"{self.base_url}/"),
            # Primary document pages
            ("GR Page", f"{self.base_url}/gr.html"),
            ("Circulars", f"{self.base_url}/circulars.html"),
            # Fallback pages (used when primary routes are unavailable)
            ("Circulars (Fallback)", f"{self.base_url}/circulars.html"),
            ("GR Page (Fallback)", f"{self.base_url}/gr.html"),
            # Additional pages
            ("Notifications", f"{self.base_url}/Notifications.html"),
            ("Rules", f"{self.base_url}/rules.html"),
            ("Budget", f"{self.base_url}/Budget.html"),
            ("Budget in Brief", f"{self.base_url}/Budget-in-brief.html"),
            ("Budget Speech", f"{self.base_url}/Budget-speech.html"),
            ("Pension", f"{self.base_url}/pension.html"),
            ("Treasury", f"{self.base_url}/treasury.html"),
        ]
        
        all_documents = []
        seen_urls = set()
        stats = {'valid': 0, 'invalid': 0, 'pages_scanned': 0}
        
        for page_name, page_url in pages:
            try:
                docs = self.scrape_page_for_pdfs(page_name, page_url, max_per_page)
                
                for doc in docs:
                    if doc['pdf_url'] not in seen_urls:
                        all_documents.append(doc)
                        seen_urls.add(doc['pdf_url'])
                        stats['valid'] += 1
                
                if docs:
                    stats['pages_scanned'] += 1
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Error scraping {page_name}: {e}")
                continue
        
        print(f"\n📊 SCRAPING SUMMARY:")
        print(f"   ✅ Valid PDFs found: {stats['valid']}")
        print(f"   📄 Total documents: {len(all_documents)}")
        print(f"   🌐 Pages scanned: {stats['pages_scanned']}")
        
        return all_documents

    def save_documents(self, documents):
        """Save documents to database"""
        if not documents:
            print("No documents to save")
            return 0
        
        try:
            # Insert into database
            self.db.insert_documents(documents)
            print(f"✅ Saved {len(documents)} documents to database")
            
            # Also save to JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_samples/real_documents_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(documents, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Backup saved to: {filename}")
            return len(documents)
            
        except Exception as e:
            print(f"❌ Error saving documents: {e}")
            return 0

if __name__ == "__main__":
    scraper = RealDocumentScraper()
    documents = scraper.scrape_all_pages(max_per_page=10)
    
    if documents:
        scraper.save_documents(documents)
        
        print("\n📄 SAMPLE DOCUMENTS:")
        for doc in documents[:5]:
            print(f"\n  GR No: {doc['gr_no']}")
            print(f"  Date: {doc['date']}")
            print(f"  Branch: {doc['branch']}")
            print(f"  Subject: {doc['subject_en'][:80]}...")
            print(f"  URL: {doc['pdf_url']}")
            print(f"  Status: {doc['pdf_status']}")

