#!/usr/bin/env python3
"""
Test script to verify API credentials are working
"""
import os
import sys

# Add src to path
sys.path.insert(0, '/Users/maharshipatel/Downloads/FinBot_v2-main')

from src.config import Config, Clients

def test_credentials():
    print("=" * 60)
    print("Testing FinBot Credentials")
    print("=" * 60)
    
    # Check OpenAI
    print("\n1. Checking OpenAI API Key:")
    if Config.OPENAI_API_KEY:
        # Mask the key for security
        masked = Config.OPENAI_API_KEY[:10] + "..." + Config.OPENAI_API_KEY[-4:]
        print(f"   ✓ OPENAI_API_KEY is set: {masked}")
        
        # Try to create client
        try:
            client = Clients.get_openai()
            if client:
                print("   ✓ OpenAI client created successfully")
            else:
                print("   ✗ OpenAI client is None")
        except Exception as e:
            print(f"   ✗ Error creating OpenAI client: {e}")
    else:
        print("   ✗ OPENAI_API_KEY is NOT set")
    
    # Check Supabase
    print("\n2. Checking Supabase credentials:")
    if Config.SUPABASE_URL:
        print(f"   ✓ SUPABASE_URL is set: {Config.SUPABASE_URL}")
    else:
        print("   ✗ SUPABASE_URL is NOT set")
    
    if Config.SUPABASE_KEY:
        masked = Config.SUPABASE_KEY[:10] + "..."
        print(f"   ✓ SUPABASE_KEY is set: {masked}")
    else:
        print("   ✗ SUPABASE_KEY is NOT set")
    
    # Try to create Supabase client
    if Config.SUPABASE_URL and Config.SUPABASE_KEY:
        try:
            client = Clients.get_supabase()
            if client:
                print("   ✓ Supabase client created successfully")
            else:
                print("   ✗ Supabase client is None (validation may have failed)")
        except Exception as e:
            print(f"   ✗ Error creating Supabase client: {e}")
    
    print("\n" + "=" * 60)
    print("Demo Mode Status:")
    print("=" * 60)
    
    # Force re-check
    from src.core.database import DatabaseManager
    from src.core.ai import AIManager
    
    db = DatabaseManager()
    ai = AIManager()
    
    print(f"Database demo_mode: {db.demo_mode}")
    print(f"AI demo_mode: {ai.demo_mode}")
    
    if db.demo_mode or ai.demo_mode:
        print("\n⚠️  Running in DEMO MODE - credentials not properly configured!")
        print("\nTo fix:")
        print("1. Make sure .env file has correct values (not placeholders)")
        print("2. Restart the application after updating .env")
    else:
        print("\n✓ All credentials are working! Ready for full functionality.")
    
    print("=" * 60)

if __name__ == "__main__":
    test_credentials()

