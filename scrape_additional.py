#!/usr/bin/env python3
"""
Additional Document Scraper for FinBot
Scrapes 5 additional documents from each branch using actual website structure
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
        # Import AI manager for embeddings
        from src.core.ai import AIManager
        self.ai = AIManager()

    def get_existing_gr_numbers(self, branch):
        """Get existing GR numbers for a branch to avoid duplicates"""
        existing_docs = self.db.get_documents_by_branch(branch)
        return {doc.get('gr_no', '') for doc in existing_docs}

    def get_existing_pdf_urls(self):
        """Get all existing PDF URLs to avoid duplicates"""
        all_docs = self.db.search_documents({})
        return {doc.get('pdf_url', '') for doc in all_docs}

    def scrape_gr_page(self):
        """Scrape the GR (Government Resolution) page"""
        print(f"🔍 Scraping GR page...")

        try:
            url = f"{self.base_url}/gr.html"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for PDF links
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

                    # Get text content for the document
                    text = link.get_text(strip=True)
                    parent_text = ""
                    parent = link.find_parent()
                    if parent:
                        parent_text = parent.get_text(strip=True)

                    pdf_links.append({
                        'url': full_url,
                        'text': text,
                        'context': parent_text
                    })

            print(f"Found {len(pdf_links)} PDF links on GR page")
            return pdf_links

        except Exception as e:
            print(f"Error scraping GR page: {e}")
            return []

    def scrape_notifications_page(self):
        """Scrape the Notifications page"""
        print(f"🔍 Scraping Notifications page...")

        try:
            url = f"{self.base_url}/Notifications.html"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for PDF links
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

                    # Get text content for the document
                    text = link.get_text(strip=True)
                    parent_text = ""
                    parent = link.find_parent()
                    if parent:
                        parent_text = parent.get_text(strip=True)

                    pdf_links.append({
                        'url': full_url,
                        'text': text,
                        'context': parent_text
                    })

            print(f"Found {len(pdf_links)} PDF links on Notifications page")
            return pdf_links

        except Exception as e:
            print(f"Error scraping Notifications page: {e}")
            return []

    def scrape_circulars_page(self):
        """Scrape the Circulars page"""
        print(f"🔍 Scraping Circulars page...")

        try:
            url = f"{self.base_url}/circulars.html"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for PDF links
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

                    # Get text content for the document
                    text = link.get_text(strip=True)
                    parent_text = ""
                    parent = link.find_parent()
                    if parent:
                        parent_text = parent.get_text(strip=True)

                    pdf_links.append({
                        'url': full_url,
                        'text': text,
                        'context': parent_text
                    })

            print(f"Found {len(pdf_links)} PDF links on Circulars page")
            return pdf_links

        except Exception as e:
            print(f"Error scraping Circulars page: {e}")
            return []

    def classify_document_branch(self, text, context, url):
        """Classify document into appropriate branch based on content"""
        combined_text = f"{text} {context}".lower()

        # Pay-related keywords
        pay_keywords = ['pay', 'salary', 'scale', 'grade', 'allowance', 'increment', 'વેતન', 'પગાર']

        # Pay Commission keywords
        commission_keywords = ['commission', 'committee', 'કમિશન', 'સમિતિ']

        if any(keyword in combined_text for keyword in commission_keywords):
            return "PayCell-(Pay Commission)"
        elif any(keyword in combined_text for keyword in pay_keywords):
            return "M-(Pay of Government Employee)"
        else:
            # Default classification based on content hints
            if 'employee' in combined_text or 'service' in combined_text:
                return "M-(Pay of Government Employee)"
            else:
                return "PayCell-(Pay Commission)"

    def extract_document_info(self, pdf_link):
        """Extract document information from PDF link data"""
        try:
            url = pdf_link['url']
            text = pdf_link['text']
            context = pdf_link['context']

            # Determine branch
            branch = self.classify_document_branch(text, context, url)

            # Extract GR number
            combined_text = f"{text} {context}"
            gr_patterns = [
                r'પગર[^\s]*[\-\/]*\d+[^\s]*',  # Gujarati GR pattern
                r'GR[^\s]*[\-\/]*\d+[^\s]*',   # English GR pattern
                r'\w+\-\d+\-\d+\-\w+',         # Pattern like M_2641_17-Apr-2023_450
                r'[A-Z]+_\d+_[^_]+_\d+',       # General pattern
            ]

            gr_no = "Unknown"
            for pattern in gr_patterns:
                match = re.search(pattern, combined_text)
                if match:
                    gr_no = match.group(0)
                    break

            # If no GR found, try extracting from URL
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
                subject = "Government Document"

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
                'scraped_at': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error extracting document info: {e}")
            return None

    def save_documents_to_database(self, documents):
        """Save new documents to database"""
        success_count = 0

        # Prepare documents with embeddings
        docs_with_embeddings = []
        for doc in documents:
            try:
                # Create embedding for the document
                text_for_embedding = f"{doc.get('subject_en', '')} {doc.get('branch', '')} {doc.get('gr_no', '')}"
                embedding = self.ai.create_embedding(text_for_embedding)

                # Prepare document with embedding
                doc_with_embedding = {
                    'gr_no': doc.get('gr_no', ''),
                    'date': doc.get('date', ''),
                    'subject_en': doc.get('subject_en', ''),
                    'subject_ur': doc.get('subject_ur', ''),
                    'branch': doc.get('branch', ''),
                    'pdf_url': doc.get('pdf_url', ''),
                    'embedding': embedding
                }
                docs_with_embeddings.append(doc_with_embedding)
                print(f"✅ Prepared: {doc.get('gr_no', 'Unknown')} ({doc.get('branch', 'Unknown')})")

            except Exception as e:
                print(f"❌ Error preparing document {doc.get('gr_no', 'Unknown')}: {e}")

        # Insert all documents at once
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

        # Scrape all document pages
        all_pdf_links = []
        all_pdf_links.extend(self.scrape_gr_page())
        time.sleep(2)
        all_pdf_links.extend(self.scrape_notifications_page())
        time.sleep(2)
        all_pdf_links.extend(self.scrape_circulars_page())

        print(f"\n📊 Total PDF links found: {len(all_pdf_links)}")

        # Filter out existing documents and process new ones
        new_documents = []
        branch_counts = {"M-(Pay of Government Employee)": 0, "PayCell-(Pay Commission)": 0}

        for pdf_link in all_pdf_links:
            if pdf_link['url'] not in existing_urls:
                doc_info = self.extract_document_info(pdf_link)

                if doc_info:
                    branch = doc_info.get('branch', '')

                    # Limit to 5 documents per branch
                    if branch_counts.get(branch, 0) < 5:
                        new_documents.append(doc_info)
                        branch_counts[branch] = branch_counts.get(branch, 0) + 1
                        print(f"✅ New document: {doc_info.get('gr_no', 'Unknown')} ({branch})")

                        # Stop if we have 5 from each branch
                        if all(count >= 5 for count in branch_counts.values()):
                            break

                time.sleep(0.5)  # Rate limiting

        if new_documents:
            print(f"\n💾 Saving {len(new_documents)} new documents to database...")
            saved_count = self.save_documents_to_database(new_documents)

            # Save to JSON file as backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_samples/additional_scraped_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(new_documents, f, ensure_ascii=False, indent=2)

            print(f"\n✅ SCRAPING COMPLETE!")
            print(f"📊 New documents by branch:")
            for branch, count in branch_counts.items():
                print(f"   {branch}: {count} documents")
            print(f"💾 Successfully saved to database: {saved_count}")
            print(f"📁 Backup saved to: {filename}")

        else:
            print("\n⚠️  No new documents found")

if __name__ == "__main__":
    scraper = AdditionalScraper()
    scraper.run_additional_scraping()
