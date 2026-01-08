#!/usr/bin/env python3
"""
Verify and save only working PDF URLs to database
"""

import requests
from src.core.database import DatabaseManager

def verify_url(url, timeout=5):
    """Check if URL returns valid PDF"""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '').lower()
            if 'pdf' in content_type:
                return True, "Valid PDF"
            elif response.headers.get('Content-Length', '0') > '1000':
                return True, "Large file (likely PDF)"
        return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

# All candidate documents
all_docs = [
    {"gr_no": "Rule-Eng_34_2018-11", "date": "2018-11-13", "branch": "F-(Finance Code)", "subject_en": "Finance Code Rules - English Version", "pdf_url": "https://financedepartment.gujarat.gov.in/Documents/Rule-Eng_34_2018-11-13_920.pdf"},
    {"gr_no": "Rule-Eng_1_2014-2", "date": "2014-02-01", "branch": "F-(Finance Code)", "subject_en": "Finance Code Rule 1 - English", "pdf_url": "https://financedepartment.gujarat.gov.in/Documents/Rule-Eng_1_2014-2-1_1.pdf"},
    {"gr_no": "Rule-Eng_2_2014-2", "date": "2014-02-01", "branch": "F-(Finance Code)", "subject_en": "Finance Code Rule 2 - English", "pdf_url": "https://financedepartment.gujarat.gov.in/Documents/Rule-Eng_2_2014-2-1_2.pdf"},
    {"gr_no": "Rule-Eng_3_2014-2", "date": "2014-02-01", "branch": "F-(Finance Code)", "subject_en": "Finance Code Rule 3 - English", "pdf_url": "https://financedepartment.gujarat.gov.in/Documents/Rule-Eng_3_2014-2-1_3.pdf"},
    {"gr_no": "Rule-Eng_4_2014-2", "date": "2014-02-01", "branch": "F-(Finance Code)", "subject_en": "Finance Code Rule 4 - English", "pdf_url": "https://financedepartment.gujarat.gov.in/Documents/Rule-Eng_4_2014-2-1_4.pdf"},
    {"gr_no": "Rule-Eng_5_2014-2", "date": "2014-02-01", "branch": "F-(Finance Code)", "subject_en": "Finance Code Rule 5 - English", "pdf_url": "https://financedepartment.gujarat.gov.in/Documents/Rule-Eng_5_2014-2-1_5.pdf"},
    {"gr_no": "Cir_1_2016-11", "date": "2016-11-09", "branch": "PayCell-(Pay Commission)", "subject_en": "Circular 1/2016 - Pay Commission Guidelines", "pdf_url": "https://financedepartment.gujarat.gov.in/Documents/Cir_1_2016-11-9_846.PDF"},
    {"gr_no": "Cir_2_2016-11", "date": "2016-11-09", "branch": "PayCell-(Pay Commission)", "subject_en": "Circular 2/2016 - Allowances", "pdf_url": "https://financedepartment.gujarat.gov.in/Documents/Cir_2_2016-11-9_814.PDF"},
    {"gr_no": "Cir_3_2017-1", "date": "2017-01-11", "branch": "PayCell-(Pay Commission)", "subject_en": "Circular 3/2017 - Service Matters", "pdf_url": "https://financedepartment.gujarat.gov.in/Documents/Cir_3_2017-1-11_391.pdf"},
    {"gr_no": "Cir_4_2017-5", "date": "2017-05-15", "branch": "PayCell-(Pay Commission)", "subject_en": "Circular 4/2017 - Dearness Allowance", "pdf_url": "https://financedepartment.gujarat.gov.in/Documents/Cir_4_2017-5-15_80.PDF"},
    {"gr_no": "Cir_5_2019-5", "date": "2019-05-20", "branch": "PayCell-(Pay Commission)", "subject_en": "Circular 5/2019 - Pay Revision", "pdf_url": "https://financedepartment.gujarat.gov.in/Documents/Cir_5_2019-5-20_82.PDF"},
    {"gr_no": "Cir_6_2022-4", "date": "2022-04-01", "branch": "PayCell-(Pay Commission)", "subject_en": "Circular 6/2022 - 7th Pay Commission Implementation", "pdf_url": "https://financedepartment.gujarat.gov.in/Documents/Cir_6_2022-4-1_86.PDF"},
    {"gr_no": "Cir_7_2022-10", "date": "2022-10-01", "branch": "PayCell-(Pay Commission)", "subject_en": "Circular 7/2022 - House Rent Allowance", "pdf_url": "https://financedepartment.gujarat.gov.in/Documents/Cir_7_2022-10-1_87.PDF"},
    {"gr_no": "Cir_8_2022-10", "date": "2022-10-01", "branch": "PayCell-(Pay Commission)", "subject_en": "Circular 8/2022 - Travel Allowance", "pdf_url": "https://financedepartment.gujarat.gov.in/Documents/Cir_8_2022-10-1_88.PDF"},
    {"gr_no": "Cir_9_2022-10", "date": "2022-10-01", "branch": "PayCell-(Pay Commission)", "subject_en": "Circular 9/2022 - Medical Allowance", "pdf_url": "https://financedepartment.gujarat.gov.in/Documents/Cir_9_2022-10-1_89.PDF"},
    {"gr_no": "Cir_10_2023-4", "date": "2023-04-01", "branch": "PayCell-(Pay Commission)", "subject_en": "Circular 10/2023 - Annual Increment", "pdf_url": "https://financedepartment.gujarat.gov.in/Documents/Cir_10_2023-4-1_90.PDF"},
    {"gr_no": "Rule-Guj_1_2014-2", "date": "2014-02-01", "branch": "F-(Finance Code)", "subject_en": "Finance Code Rule 1 - Gujarati", "pdf_url": "https://financedepartment.gujarat.gov.in/Documents/Rule-Guj_1_2014-2-1_1.pdf"},
    {"gr_no": "Rule-Guj_2_2014-2", "date": "2014-02-01", "branch": "F-(Finance Code)", "subject_en": "Finance Code Rule 2 - Gujarati", "pdf_url": "https://financedepartment.gujarat.gov.in/Documents/Rule-Guj_2_2014-2-1_2.pdf"},
    {"gr_no": "Rule-Guj_3_2014-2", "date": "2014-02-01", "branch": "F-(Finance Code)", "subject_en": "Finance Code Rule 3 - Gujarati", "pdf_url": "https://financedepartment.gujarat.gov.in/Documents/Rule-Guj_3_2014-2-1_3.pdf"},
    {"gr_no": "Rule-Guj_4_2014-2", "date": "2014-02-01", "branch": "F-(Finance Code)", "subject_en": "Finance Code Rule 4 - Gujarati", "pdf_url": "https://financedepartment.gujarat.gov.in/Documents/Rule-Guj_4_2014-2-1_4.pdf"},
    {"gr_no": "Rule-Guj_5_2014-2", "date": "2014-02-01", "branch": "F-(Finance Code)", "subject_en": "Finance Code Rule 5 - Gujarati", "pdf_url": "https://financedepartment.gujarat.gov.in/Documents/Rule-Guj_5_2014-2-1_5.pdf"},
]

# Verify all URLs
print("🔍 VERIFYING ALL PDF URLs...")
print("=" * 60)

working_docs = []
broken_urls = []

for doc in all_docs:
    is_working, message = verify_url(doc['pdf_url'])
    if is_working:
        working_docs.append(doc)
        print(f"✅ {doc['gr_no']}: {message}")
    else:
        broken_urls.append((doc['gr_no'], doc['pdf_url'], message))
        print(f"❌ {doc['gr_no']}: {message}")

print(f"\n📊 SUMMARY:")
print(f"   ✅ Working PDFs: {len(working_docs)}")
print(f"   ❌ Broken URLs: {len(broken_urls)}")

if broken_urls:
    print(f"\n❌ Broken URLs to remove:")
    for gr_no, url, msg in broken_urls:
        print(f"   - {gr_no}: {msg}")

# Save only working documents
if working_docs:
    db = DatabaseManager()
    print(f"\n💾 Saving {len(working_docs)} verified documents to database...")
    
    # Clear and re-insert
    db.clear_documents()
    db.insert_documents(working_docs)
    
    count = db.get_documents_count()
    print(f"✅ Successfully saved {len(working_docs)} documents!")
    print(f"   Total in database: {count}")

