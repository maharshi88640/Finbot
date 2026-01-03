#!/usr/bin/env python3
"""
GR Page Branch Analyzer
Analyzes the GR page to find branch selectors and extract all branches
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime

class GRPageAnalyzer:
    def __init__(self):
        self.base_url = "https://financedepartment.gujarat.gov.in"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def analyze_gr_page(self):
        """Analyze the GR page structure"""
        print("🔍 ANALYZING GR PAGE FOR BRANCH SELECTOR:")
        print("=" * 60)

        url = f"{self.base_url}/gr.html"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for select elements (dropdowns)
            selects = soup.find_all('select')
            print(f"Select elements found: {len(selects)}")

            all_branches = []

            for i, select in enumerate(selects):
                print(f"\nSelect {i+1}:")
                print(f"  ID: {select.get('id', 'No ID')}")
                print(f"  Name: {select.get('name', 'No name')}")
                print(f"  Class: {select.get('class', 'No class')}")

                # Get all options
                options = select.find_all('option')
                print(f"  Options ({len(options)}):")

                for j, option in enumerate(options):
                    value = option.get('value', '')
                    text = option.get_text(strip=True)
                    if value and text and text.lower() != 'select':
                        all_branches.append({
                            'value': value,
                            'text': text,
                            'select_id': select.get('id', ''),
                            'select_name': select.get('name', '')
                        })
                    print(f"    {j+1}. Value: '{value}' | Text: '{text}'")

            # Look for any input elements that might be related
            inputs = soup.find_all('input')
            print(f"\nInput elements found: {len(inputs)}")
            for input_elem in inputs:
                input_type = input_elem.get('type', '')
                input_name = input_elem.get('name', '')
                input_id = input_elem.get('id', '')
                if input_type in ['hidden', 'text', 'submit']:
                    print(f"  Input: type='{input_type}', name='{input_name}', id='{input_id}'")

            # Look for forms
            forms = soup.find_all('form')
            print(f"\nForms found: {len(forms)}")
            for i, form in enumerate(forms):
                print(f"Form {i+1}:")
                print(f"  Action: {form.get('action', 'No action')}")
                print(f"  Method: {form.get('method', 'GET')}")
                print(f"  ID: {form.get('id', 'No ID')}")

            return all_branches

        except Exception as e:
            print(f"Error analyzing GR page: {e}")
            return []

    def test_branch_request(self, branch_info):
        """Test making a request with a specific branch"""
        print(f"\n🧪 Testing branch: {branch_info['text']} (value: {branch_info['value']})")

        try:
            # Try different URL patterns
            test_urls = [
                f"{self.base_url}/gr.html?branch={branch_info['value']}",
                f"{self.base_url}/gr.html?{branch_info['select_name']}={branch_info['value']}",
                f"{self.base_url}/documents.php?branch={branch_info['value']}",
                f"{self.base_url}/gr.php?branch={branch_info['value']}"
            ]

            for url in test_urls:
                try:
                    response = self.session.get(url, timeout=15)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        pdf_links = soup.find_all('a', href=lambda x: x and '.pdf' in x.lower())
                        print(f"   ✅ URL works: {url} ({len(pdf_links)} PDFs found)")
                        return url, len(pdf_links)
                    else:
                        print(f"   ❌ {response.status_code}: {url}")
                except Exception as e:
                    print(f"   ❌ Error: {url} - {e}")

                time.sleep(1)

            return None, 0

        except Exception as e:
            print(f"Error testing branch: {e}")
            return None, 0

if __name__ == "__main__":
    analyzer = GRPageAnalyzer()

    # Analyze the page structure
    branches = analyzer.analyze_gr_page()

    if branches:
        print(f"\n📊 SUMMARY:")
        print(f"Total branches found: {len(branches)}")

        # Test a few branches
        print(f"\n🧪 TESTING BRANCH REQUESTS:")
        for branch in branches[:3]:  # Test first 3 branches
            analyzer.test_branch_request(branch)
            time.sleep(2)

        # Save branch information
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data_samples/branches_discovered_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(branches, f, ensure_ascii=False, indent=2)

        print(f"\n📁 Branch information saved to: {filename}")
    else:
        print("No branches found in dropdown selectors")
