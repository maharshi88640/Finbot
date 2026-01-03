#!/usr/bin/env python3
"""
Insert Scraped Documents to Database
Loads the branch-specific scraped documents and inserts them into the database
"""

import json
from src.core.database import DatabaseManager
from src.core.ai import AIManager

def insert_branch_documents():
    """Insert the branch-specific scraped documents into database"""

    # Load the scraped documents
    filename = 'data_samples/branch_specific_scraped_20251009_143744.json'

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            documents = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {filename}")
        return

    print(f"📁 Loading {len(documents)} documents from {filename}")

    db = DatabaseManager()
    ai = AIManager()

    # Group documents by branch for better tracking
    branch_counts = {}
    for doc in documents:
        branch = doc.get('branch', 'Unknown')
        branch_counts[branch] = branch_counts.get(branch, 0) + 1

    print("\n📊 Documents to insert by branch:")
    for branch, count in branch_counts.items():
        print(f"  {branch}: {count} documents")

    # Prepare documents for database insertion
    docs_for_insertion = []
    success_count = 0

    print(f"\n💾 Preparing documents for database insertion...")

    for i, doc in enumerate(documents, 1):
        try:
            # Create embedding for the document
            text_for_embedding = f"{doc.get('subject_en', '')} {doc.get('branch', '')} {doc.get('gr_no', '')}"
            embedding = ai.create_embedding(text_for_embedding)

            # Prepare document with embedding
            doc_data = {
                'gr_no': doc.get('gr_no', ''),
                'date': doc.get('date', ''),
                'subject_en': doc.get('subject_en', ''),
                'subject_ur': doc.get('subject_ur', ''),
                'branch': doc.get('branch', ''),
                'pdf_url': doc.get('pdf_url', ''),
                'embedding': embedding
            }
            docs_for_insertion.append(doc_data)

            if i % 10 == 0:
                print(f"   Prepared {i}/{len(documents)} documents...")

        except Exception as e:
            print(f"❌ Error preparing document {i} ({doc.get('gr_no', 'Unknown')}): {e}")
            continue

    print(f"✅ Prepared {len(docs_for_insertion)} documents for insertion")

    # Insert documents in batches
    batch_size = 20
    total_batches = (len(docs_for_insertion) + batch_size - 1) // batch_size

    print(f"\n🚀 Inserting documents in {total_batches} batches of {batch_size}...")

    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(docs_for_insertion))
        batch = docs_for_insertion[start_idx:end_idx]

        try:
            result = db.insert_documents(batch)
            success_count += len(batch)
            print(f"   ✅ Batch {batch_num + 1}/{total_batches}: Inserted {len(batch)} documents")

        except Exception as e:
            print(f"   ❌ Batch {batch_num + 1}/{total_batches} failed: {e}")
            # Try inserting documents individually in this batch
            for doc in batch:
                try:
                    db.insert_documents([doc])
                    success_count += 1
                    print(f"      ✅ Individual insert: {doc.get('gr_no', 'Unknown')}")
                except Exception as e2:
                    print(f"      ❌ Failed: {doc.get('gr_no', 'Unknown')} - {e2}")

    print(f"\n📊 INSERTION COMPLETE!")
    print(f"✅ Successfully inserted: {success_count} documents")
    print(f"❌ Failed insertions: {len(documents) - success_count}")

    # Verify the database state
    print(f"\n🔍 Verifying database state...")
    new_total = db.get_documents_count()
    new_branches = db.get_branches()

    print(f"📈 Database summary:")
    print(f"   Total documents: {new_total}")
    print(f"   Total branches: {len(new_branches)}")

    print(f"\n📊 Documents per branch:")
    for branch in sorted(new_branches):
        docs = db.get_documents_by_branch(branch)
        print(f"   {branch}: {len(docs)} documents")

if __name__ == "__main__":
    insert_branch_documents()
