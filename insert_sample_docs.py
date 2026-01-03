"""
Insert sample documents for testing FinBot
"""

from src.core.database import DatabaseManager

def insert_sample_documents():
    """Insert sample Gujarat Government GR documents"""
    
    sample_docs = [
        {
            "gr_no": "GR-2024-01-001",
            "date": "2024-01-15",
            "branch": "Finance Department",
            "subject_en": "Budget allocation for education sector FY 2024-25",
            "subject_gu": "Finance Department Budget allocation document",
            "pdf_url": "https://financedepartment.gujarat.gov.in/documents/GR-2024-01-001.pdf"
        },
        {
            "gr_no": "GR-2024-01-002",
            "date": "2024-01-20",
            "branch": "Finance Department",
            "subject_en": "Revision of DA rates for government employees",
            "subject_gu": "Finance Department DA revision document",
            "pdf_url": "https://financedepartment.gujarat.gov.in/documents/GR-2024-01-002.pdf"
        },
        {
            "gr_no": "GR-2024-02-001",
            "date": "2024-02-05",
            "branch": "Health Department",
            "subject_en": "Guidelines for COVID-19 vaccination camps",
            "subject_gu": "Health Department vaccination guidelines",
            "pdf_url": "https://financedepartment.gujarat.gov.in/documents/GR-2024-02-001.pdf"
        },
        {
            "gr_no": "GR-2024-02-002",
            "date": "2024-02-10",
            "branch": "Health Department",
            "subject_en": "Procurement of medical equipment for district hospitals",
            "subject_gu": "Health Department medical equipment procurement",
            "pdf_url": "https://financedepartment.gujarat.gov.in/documents/GR-2024-02-002.pdf"
        },
        {
            "gr_no": "GR-2024-03-001",
            "date": "2024-03-01",
            "branch": "Agriculture Department",
            "subject_en": "Subsidy scheme for drip irrigation systems",
            "subject_gu": "Agriculture Department drip irrigation subsidy",
            "pdf_url": "https://financedepartment.gujarat.gov.in/documents/GR-2024-03-001.pdf"
        },
        {
            "gr_no": "GR-2024-03-002",
            "date": "2024-03-15",
            "branch": "Agriculture Department",
            "subject_en": "PM Kisan scheme implementation guidelines",
            "subject_gu": "Agriculture Department PM Kisan guidelines",
            "pdf_url": "https://financedepartment.gujarat.gov.in/documents/GR-2024-03-002.pdf"
        },
        {
            "gr_no": "GR-2024-04-001",
            "date": "2024-04-01",
            "branch": "Education Department",
            "subject_en": "School education curriculum revision 2024",
            "subject_gu": "Education Department curriculum revision",
            "pdf_url": "https://financedepartment.gujarat.gov.in/documents/GR-2024-04-001.pdf"
        },
        {
            "gr_no": "GR-2024-04-002",
            "date": "2024-04-10",
            "branch": "Education Department",
            "subject_en": "Teacher recruitment notification for primary schools",
            "subject_gu": "Education Department teacher recruitment",
            "pdf_url": "https://financedepartment.gujarat.gov.in/documents/GR-2024-04-002.pdf"
        },
        {
            "gr_no": "GR-2024-05-001",
            "date": "2024-05-05",
            "branch": "Revenue Department",
            "subject_en": "Land record digitization project update",
            "subject_gu": "Revenue Department land digitization",
            "pdf_url": "https://financedepartment.gujarat.gov.in/documents/GR-2024-05-001.pdf"
        },
        {
            "gr_no": "GR-2024-05-002",
            "date": "2024-05-15",
            "branch": "Revenue Department",
            "subject_en": "Property tax assessment guidelines",
            "subject_gu": "Revenue Department property tax guidelines",
            "pdf_url": "https://financedepartment.gujarat.gov.in/documents/GR-2024-05-002.pdf"
        },
        {
            "gr_no": "GR-2023-12-001",
            "date": "2023-12-20",
            "branch": "Finance Department",
            "subject_en": "State tax revenue collection report Q3 2023",
            "subject_gu": "Finance Department Q3 tax report",
            "pdf_url": "https://financedepartment.gujarat.gov.in/documents/GR-2023-12-001.pdf"
        },
        {
            "gr_no": "GR-2023-11-001",
            "date": "2023-11-15",
            "branch": "Transport Department",
            "subject_en": "Electric vehicle policy implementation",
            "subject_gu": "Transport Department EV policy",
            "pdf_url": "https://financedepartment.gujarat.gov.in/documents/GR-2023-11-001.pdf"
        }
    ]
    
    db = DatabaseManager()
    
    # Check current count
    current_count = db.get_documents_count()
    print(f"Current documents in database: {current_count}")
    
    # Insert sample documents
    success = db.insert_documents(sample_docs)
    
    if success:
        new_count = db.get_documents_count()
        print(f"Successfully inserted {len(sample_docs)} documents!")
        print(f"Total documents now: {new_count}")
    else:
        print("Failed to insert documents")

if __name__ == "__main__":
    insert_sample_documents()

