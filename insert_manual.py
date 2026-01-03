#!/usr/bin/env python3
"""
Manual insertion script for additional documents
"""

import json
from src.core.database import DatabaseManager
from src.core.ai import AIManager

def insert_additional_documents():
    """Insert the additional documents manually"""

    # Load the scraped documents
    with open('data_samples/additional_scraped_20251009_141950.json', 'r', encoding='utf-8') as f:
        documents = json.load(f)

    print(f"Loading {len(documents)} documents for insertion...")

    db = DatabaseManager()
    ai = AIManager()

    # Prepare documents without embedding for now
    docs_for_insertion = []
    for doc in documents:
        doc_data = {
            'gr_no': doc.get('gr_no', ''),
            'date': doc.get('date', ''),
            'subject_en': doc.get('subject_en', ''),
            'subject_ur': doc.get('subject_ur', ''),
            'branch': doc.get('branch', ''),
            'pdf_url': doc.get('pdf_url', '')
        }
        docs_for_insertion.append(doc_data)
        print(f"Prepared: {doc.get('gr_no', 'Unknown')}")

    # Try to insert without embeddings
    try:
        result = db.insert_documents(docs_for_insertion)
        print(f"✅ Successfully inserted {len(docs_for_insertion)} documents")

        # Verify insertion
        new_count = db.get_documents_count()
        print(f"📊 New total document count: {new_count}")

        # Show branch counts
        branches = db.get_branches()
        for branch in branches:
            docs = db.get_documents_by_branch(branch)
            print(f"   {branch}: {len(docs)} documents")

    except Exception as e:
        print(f"❌ Error inserting documents: {e}")

if __name__ == "__main__":
    insert_additional_documents()
