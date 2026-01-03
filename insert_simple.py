#!/usr/bin/env python3
"""
Insert Documents Without Embeddings
Insert the scraped documents without the embedding column to resolve schema issues
"""

import json
from src.core.database import DatabaseManager

def insert_without_embeddings():
    """Insert documents without embedding column"""

    filename = 'data_samples/branch_specific_scraped_20251009_143744.json'

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            documents = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {filename}")
        return

    print(f"📁 Loading {len(documents)} documents from {filename}")

    db = DatabaseManager()

    # Prepare documents WITHOUT embedding
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

    print(f"✅ Prepared {len(docs_for_insertion)} documents (without embeddings)")

    # Try inserting all at once
    try:
        print(f"🚀 Inserting all {len(docs_for_insertion)} documents...")
        result = db.insert_documents(docs_for_insertion)
        print(f"✅ Successfully inserted all documents!")

    except Exception as e:
        print(f"❌ Batch insert failed: {e}")

        # Try individual inserts
        print(f"🔄 Trying individual insertions...")
        success_count = 0

        for i, doc in enumerate(docs_for_insertion):
            try:
                db.insert_documents([doc])
                success_count += 1
                if i % 10 == 0:
                    print(f"   Inserted {i+1}/{len(docs_for_insertion)}...")
            except Exception as e2:
                print(f"   ❌ Failed: {doc.get('gr_no', 'Unknown')} - {e2}")

        print(f"✅ Individual insertions complete: {success_count} successful")

    # Verify the results
    print(f"\n🔍 Verifying database state...")
    new_total = db.get_documents_count()
    new_branches = db.get_branches()

    print(f"📈 Final database summary:")
    print(f"   Total documents: {new_total}")
    print(f"   Total branches: {len(new_branches)}")

    if len(new_branches) > 2:
        print(f"\n📊 Documents per branch:")
        for branch in sorted(new_branches):
            docs = db.get_documents_by_branch(branch)
            print(f"   {branch}: {len(docs)} documents")

if __name__ == "__main__":
    insert_without_embeddings()
