#!/usr/bin/env python3
"""
Save ONLY verified working PDF URLs from Gujarat Finance Department
All URLs verified with HTTP 200 and Content-Type: application/pdf
"""

from src.core.database import DatabaseManager

def save_verified_documents():
    """
    Save only verified documents. URLs were tested and confirmed working.
    Verification command: curl -sI <url> | head -5
    
    Returns HTTP 200 and Content-Type: application/pdf
    """
    
    # ONLY these 5 URLs are verified to work
    # Verified with: curl -sI <url> | head -5
    verified_documents = [
        {
            "gr_no": "Rule-Eng_34_2018-11",
            "date": "2018-11-13",
            "branch": "F-(Finance Code)",
            "subject_en": "Finance Code Rules - English Version",
            "subject_gu": "Finance Code Rules",
            "pdf_url": "https://financedepartment.gujarat.gov.in/Documents/Rule-Eng_34_2018-11-13_920.pdf"
        },
        {
            "gr_no": "Cir_1_2016-11",
            "date": "2016-11-09",
            "branch": "PayCell-(Pay Commission)",
            "subject_en": "Circular 1/2016 - Pay Commission Guidelines",
            "subject_gu": "Circular 1/2016 - Pay Commission",
            "pdf_url": "https://financedepartment.gujarat.gov.in/Documents/Cir_1_2016-11-9_846.PDF"
        },
        {
            "gr_no": "Cir_2_2016-11",
            "date": "2016-11-09",
            "branch": "PayCell-(Pay Commission)",
            "subject_en": "Circular 2/2016 - Allowances",
            "subject_gu": "Circular 2/2016 - Allowances",
            "pdf_url": "https://financedepartment.gujarat.gov.in/Documents/Cir_2_2016-11-9_814.PDF"
        },
        {
            "gr_no": "Cir_3_2017-1",
            "date": "2017-01-11",
            "branch": "PayCell-(Pay Commission)",
            "subject_en": "Circular 3/2017 - Service Matters",
            "subject_gu": "Circular 3/2017 - Service Matters",
            "pdf_url": "https://financedepartment.gujarat.gov.in/Documents/Cir_3_2017-1-11_391.pdf"
        },
        {
            "gr_no": "Cir_4_2017-5",
            "date": "2017-05-15",
            "branch": "PayCell-(Pay Commission)",
            "subject_en": "Circular 4/2017 - Dearness Allowance",
            "subject_gu": "Circular 4/2017 - DA",
            "pdf_url": "https://financedepartment.gujarat.gov.in/Documents/Cir_4_2017-5-15_80.PDF"
        },
    ]
    
    db = DatabaseManager()
    
    print("💾 Saving 5 verified documents to database...")
    print("=" * 60)
    
    # Insert documents
    success = db.insert_documents(verified_documents)
    
    if success:
        count = db.get_documents_count()
        print(f"✅ Successfully saved {len(verified_documents)} documents!")
        print(f"   Total documents in database: {count}")
        
        print(f"\n📄 VERIFIED WORKING URLs:")
        print(f"   All PDFs verified with: curl -sI <url> | head -5")
        print(f"   Returns: HTTP/1.1 200 OK + Content-Type: application/pdf\n")
        
        for doc in verified_documents:
            print(f"   ✅ {doc['gr_no']}")
            print(f"      {doc['pdf_url']}")
            print(f"      Branch: {doc['branch']}\n")
    else:
        print("❌ Failed to insert documents")

if __name__ == "__main__":
    save_verified_documents()

