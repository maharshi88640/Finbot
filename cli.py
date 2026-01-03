#!/usr/bin/env python3
"""
FinBot CLI Tools
Command-line interface for various FinBot operations
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.scraper import WebScraper
from src.core.database import DatabaseManager
from src.chat import ChatManager
from src.config import Config

def scrape_data(args):
    """Scrape data from the web"""
    scraper = WebScraper()

    if args.sample:
        print("🧪 Running sample scrape...")
        data = scraper.scrape_sample(args.branches, args.records_per_branch)
    else:
        print("🕷️ Running full scrape...")
        data = scraper.scrape_all_branches(
            max_branches=args.branches,
            max_records_per_branch=args.records_per_branch
        )

    print(f"✅ Scraping completed: {len(data)} records")

def check_database(args):
    """Check database status"""
    db = DatabaseManager()

    print("📊 Database Status:")
    print(f"Total documents: {db.get_documents_count()}")

    branches = db.get_branches()
    print(f"Branches: {len(branches)}")

    for branch in branches:
        count = len(db.get_documents_by_branch(branch))
        print(f"  • {branch}: {count} docs")

def clear_database(args):
    """Clear database"""
    if not args.confirm:
        print("⚠️  This will delete ALL data from the database!")
        confirm = input("Type 'DELETE' to confirm: ")
        if confirm != "DELETE":
            print("❌ Operation cancelled")
            return

    db = DatabaseManager()
    success = db.clear_documents()

    if success:
        print("✅ Database cleared successfully")
    else:
        print("❌ Failed to clear database")

def list_chat_sessions(args):
    """List all chat sessions"""
    chat = ChatManager()
    sessions = chat.list_all_sessions()

    if not sessions:
        print("📭 No chat sessions found")
        return

    print(f"💬 Found {len(sessions)} chat sessions:")
    print("-" * 80)

    for session in sessions:
        print(f"📝 {session['name']}")
        print(f"   ID: {session['id']}")
        print(f"   Created: {session['created_at']}")
        print(f"   Updated: {session['updated_at']}")
        print(f"   Messages: {session['message_count']}")
        print()

def export_chat_session(args):
    """Export a chat session"""
    chat = ChatManager()

    if args.session_id:
        session_id = args.session_id
    else:
        # List sessions and let user choose
        sessions = chat.list_all_sessions()
        if not sessions:
            print("📭 No chat sessions found")
            return

        print("Available sessions:")
        for i, session in enumerate(sessions):
            print(f"{i+1}. {session['name']} ({session['message_count']} messages)")

        try:
            choice = int(input("Select session number: ")) - 1
            session_id = sessions[choice]['id']
        except (ValueError, IndexError):
            print("❌ Invalid selection")
            return

    # Export session
    content = chat.export_session(session_id, args.format)
    if not content:
        print("❌ Failed to export session")
        return

    # Save to file
    filename = f"chat_session_{session_id[:8]}.{args.format}"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Session exported to {filename}")

def delete_chat_session(args):
    """Delete a chat session"""
    chat = ChatManager()

    if args.session_id:
        session_id = args.session_id
        # Get session name for confirmation
        sessions = chat.list_all_sessions()
        session_name = next((s['name'] for s in sessions if s['id'] == session_id), session_id)
    else:
        # List sessions and let user choose
        sessions = chat.list_all_sessions()
        if not sessions:
            print("📭 No chat sessions found")
            return

        print("Available sessions:")
        for i, session in enumerate(sessions):
            print(f"{i+1}. {session['name']} ({session['message_count']} messages)")

        try:
            choice = int(input("Select session number: ")) - 1
            session_id = sessions[choice]['id']
            session_name = sessions[choice]['name']
        except (ValueError, IndexError):
            print("❌ Invalid selection")
            return

    # Confirm deletion
    print(f"⚠️  This will permanently delete session: {session_name}")
    confirm = input("Type 'DELETE' to confirm: ")
    if confirm != "DELETE":
        print("❌ Operation cancelled")
        return

    if chat.delete_session(session_id):
        print("✅ Session deleted successfully")
    else:
        print("❌ Failed to delete session")

def chat_stats(args):
    """Show chat history statistics"""
    chat = ChatManager()
    stats = chat.get_history_stats()

    print("📊 Chat History Statistics (Database Storage):")
    print(f"Total Sessions: {stats['total_sessions']}")
    print(f"Total Messages: {stats['total_messages']}")

    if stats['current_session']:
        print(f"Current Session: {stats['current_session']['name']}")
    else:
        print("Current Session: None")

    if stats.get('most_recent'):
        print(f"Most Recent: {stats['most_recent']['name']} ({stats['most_recent']['updated_at']})")

    print("\n💾 Storage: Supabase Database")
    print("🔄 Sync: Real-time across devices")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="FinBot CLI Tools")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape data from web")
    scrape_parser.add_argument("--sample", action="store_true", help="Run sample scrape")
    scrape_parser.add_argument("--branches", type=int, help="Maximum branches to scrape")
    scrape_parser.add_argument("--records-per-branch", type=int, help="Maximum records per branch")
    scrape_parser.set_defaults(func=scrape_data)

    # Database commands
    db_parser = subparsers.add_parser("db", help="Database operations")
    db_subparsers = db_parser.add_subparsers(dest="db_command")

    # Check database
    check_parser = db_subparsers.add_parser("status", help="Check database status")
    check_parser.set_defaults(func=check_database)

    # Clear database
    clear_parser = db_subparsers.add_parser("clear", help="Clear database")
    clear_parser.add_argument("--confirm", action="store_true", help="Skip confirmation")
    clear_parser.set_defaults(func=clear_database)

    # Chat commands
    chat_parser = subparsers.add_parser("chat", help="Chat history operations")
    chat_subparsers = chat_parser.add_subparsers(dest="chat_command")

    # List chat sessions
    list_parser = chat_subparsers.add_parser("list", help="List all chat sessions")
    list_parser.set_defaults(func=list_chat_sessions)

    # Export chat session
    export_parser = chat_subparsers.add_parser("export", help="Export a chat session")
    export_parser.add_argument("--session-id", help="Session ID to export")
    export_parser.add_argument("--format", choices=["json", "txt", "md"], default="md", help="Export format")
    export_parser.set_defaults(func=export_chat_session)

    # Delete chat session
    delete_parser = chat_subparsers.add_parser("delete", help="Delete a chat session")
    delete_parser.add_argument("--session-id", help="Session ID to delete")
    delete_parser.set_defaults(func=delete_chat_session)

    # Chat statistics
    stats_parser = chat_subparsers.add_parser("stats", help="Show chat history statistics")
    stats_parser.set_defaults(func=chat_stats)

    args = parser.parse_args()

    if hasattr(args, 'func'):
        try:
            Config.validate()
            args.func(args)
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
