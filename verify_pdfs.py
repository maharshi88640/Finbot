
import requests
from src.core.database import DatabaseManager
from datetime import datetime
import sys

def verify_pdf_accessible(url: str, timeout: int = 10) -> dict:
    """Check if a PDF URL is actually accessible"""
    try:
        # Try HEAD request first (faster)
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            content_length = response.headers.get('Content-Length', '0')
            
            # Check if it's actually a PDF
            if 'pdf' in content_type.lower() or int(content_length) > 1000:
                return {
                    'accessible': True,
                    'status_code': response.status_code,
                    'content_type': content_type,
                    'content_length': content_length,
                    'message': '✅ PDF is accessible'
                }
            else:
                return {
                    'accessible': False,
                    'status_code': response.status_code,
                    'content_type': content_type,
                    'message': '⚠️ URL exists but may not be a valid PDF'
                }
        
        return {
            'accessible': False,
            'status_code': response.status_code,
            'message': f'❌ URL returned HTTP {response.status_code}'
        }
        
    except requests.exceptions.Timeout:
        return {
            'accessible': False,
            'error': 'timeout',
            'message': '❌ Request timed out'
        }
    except requests.exceptions.ConnectionError as e:
        return {
            'accessible': False,
            'error': 'connection_error',
            'message': '❌ Connection error - URL may not exist'
        }
    except requests.exceptions.TooManyRedirects:
        return {
            'accessible': False,
            'error': 'redirects',
            'message': '❌ Too many redirects'
        }
    except Exception as e:
        return {
            'accessible': False,
            'error': str(e),
            'message': f'❌ Error: {str(e)}'
        }

def verify_all_pdfs():
    """Verify all PDFs in the database"""
    db = DatabaseManager()
    
    # Get all documents
    all_docs = db.search_documents({})
    
    print(f"🔍 Verifying {len(all_docs)} documents...\n")
    print("=" * 80)
    
    working_count = 0
    broken_count = 0
    results = []
    
    for i, doc in enumerate(all_docs, 1):
        gr_no = doc.get('gr_no', 'Unknown')
        pdf_url = doc.get('pdf_url', '')
        branch = doc.get('branch', 'Unknown')
        subject = doc.get('subject_en', doc.get('subject_ur', 'No subject'))[:50]
        
        print(f"\n[{i}/{len(all_docs)}] Verifying: {gr_no}")
        print(f"   Branch: {branch}")
        print(f"   Subject: {subject}...")
        print(f"   URL: {pdf_url}")
        
        if not pdf_url:
            print(f"   ❌ No URL provided")
            broken_count += 1
            results.append({
                'gr_no': gr_no,
                'pdf_url': pdf_url,
                'accessible': False,
                'reason': 'No URL'
            })
            continue
        
        # Verify the PDF
        verification = verify_pdf_accessible(pdf_url)
        print(f"   {verification['message']}")
        
        if verification['accessible']:
            working_count += 1
            results.append({
                'gr_no': gr_no,
                'pdf_url': pdf_url,
                'accessible': True,
                'branch': branch,
                'subject': doc.get('subject_en', '')
            })
        else:
            broken_count += 1
            results.append({
                'gr_no': gr_no,
                'pdf_url': pdf_url,
                'accessible': False,
                'reason': verification.get('message', 'Unknown error'),
                'status_code': verification.get('status_code'),
                'branch': branch,
                'subject': doc.get('subject_en', '')
            })
    
    print("\n" + "=" * 80)
    print(f"\n📊 VERIFICATION SUMMARY:")
    print(f"   ✅ Working PDFs: {working_count}")
    print(f"   ❌ Broken PDFs: {broken_count}")
    print(f"   📄 Total: {len(all_docs)}")
    
    # Save broken PDFs to file for review
    broken_pdfs = [r for r in results if not r['accessible']]
    
    if broken_pdfs:
        print(f"\n⚠️  BROKEN PDF LINKS:")
        print("-" * 80)
        for pdf in broken_pdfs:
            print(f"\n📛 {pdf['gr_no']}")
            print(f"   Branch: {pdf['branch']}")
            print(f"   Subject: {pdf['subject'][:50]}...")
            print(f"   URL: {pdf['pdf_url']}")
            print(f"   Reason: {pdf['reason']}")
        
        # Save to file
        import json
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"broken_pdfs_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'verification_date': timestamp,
                'total_documents': len(all_docs),
                'working_count': working_count,
                'broken_count': broken_count,
                'broken_pdfs': broken_pdfs
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 Broken PDF list saved to: {filename}")
    
    return results

def clean_broken_pdfs():
    """Remove or mark broken PDFs in the database"""
    db = DatabaseManager()
    all_docs = db.search_documents({})
    
    print("\n🧹 CLEANING BROKEN PDFs...")
    print("=" * 80)
    
    updated_count = 0
    
    for doc in all_docs:
        pdf_url = doc.get('pdf_url', '')
        if not pdf_url:
            continue
            
        verification = verify_pdf_accessible(pdf_url)
        
        if not verification['accessible']:
            gr_no = doc.get('gr_no', 'Unknown')
            
            # Update the document with verification status
            db.update_document({
                'gr_no': doc.get('gr_no'),
                'pdf_valid': False,
                'pdf_status': verification.get('message', 'Unknown'),
                'verification_date': str(datetime.now())
            })
            
            print(f"❌ Marked as broken: {gr_no}")
            print(f"   Reason: {verification.get('message', 'Unknown')}")
            updated_count += 1
    
    print(f"\n✅ Updated {updated_count} documents with broken PDF status")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Verify PDF URLs in FinBot database')
    parser.add_argument('--clean', action='store_true', help='Mark broken PDFs in database')
    parser.add_argument('--verify-only', action='store_true', help='Only verify, do not clean')
    
    args = parser.parse_args()
    
    if args.clean:
        verify_all_pdfs()
        clean_broken_pdfs()
    else:
        verify_all_pdfs()

