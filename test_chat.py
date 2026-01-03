#!/usr/bin/env python3
"""
Test script to verify chat functionality works
"""
import os
import sys

# Add src to path
sys.path.insert(0, '/Users/maharshipatel/Downloads/FinBot_v2-main')

from src.chat import ChatManager

def test_chat():
    print("=" * 60)
    print("Testing Chat Functionality")
    print("=" * 60)
    
    try:
        # Initialize chat manager
        print("\n1. Initializing ChatManager...")
        chat = ChatManager()
        print("   ✓ ChatManager initialized")
        
        # Test system status
        print("\n2. Getting system status...")
        status = chat.get_system_status()
        print(f"   ✓ System status: {status}")
        
        # Test a simple message
        print("\n3. Testing chat message...")
        response = chat.process_message("Hello, what can you do?", save_to_history=False)
        print(f"   ✓ Response received (length: {len(response)} chars)")
        print(f"   Preview: {response[:200]}...")
        
        print("\n" + "=" * 60)
        print("✓ All chat tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 60)
        print("✗ Chat test failed!")
        print("=" * 60)
        return False
    
    return True

if __name__ == "__main__":
    test_chat()

