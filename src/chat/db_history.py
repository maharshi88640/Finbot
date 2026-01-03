"""
Database-based Chat History Manager for FinBot
Handles persistent storage and management of chat sessions using Supabase
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from src.core.database import DatabaseManager
from src.config import Clients


class DatabaseChatHistoryManager:
    """Manages chat history with database storage"""

    def __init__(self, user_id: str = "default"):
        """Initialize database chat history manager

        Args:
            user_id: User identifier for multi-user support
        """
        self.db = DatabaseManager()
        self.supabase = Clients.get_supabase()
        self.user_id = user_id
        self.current_session_id = None
        self.current_session_name = None
        self.demo_mode = self.supabase is None

    def create_session(self, name: str = None) -> str:
        """Create a new chat session

        Args:
            name: Optional session name

        Returns:
            Session ID
        """
        if self.demo_mode:
            # Demo mode: return a fake session ID
            import uuid
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            if not name:
                name = f"Demo Session {timestamp}"
            self.current_session_id = str(uuid.uuid4())
            self.current_session_name = name
            return self.current_session_id

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        if not name:
            name = f"Chat Session {timestamp}"

        session_id = self.db.create_chat_session(name, self.user_id)

        if session_id:
            self.current_session_id = session_id
            self.current_session_name = name

        return session_id

    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load a chat session

        Args:
            session_id: Session ID to load

        Returns:
            Session data or None if not found
        """
        session_data = self.db.get_chat_session(session_id)

        if session_data:
            self.current_session_id = session_id
            self.current_session_name = session_data.get("name", "Unnamed Session")
            return session_data

        return None

    def save_message(self, role: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """Save a message to current session

        Args:
            role: Message role (user/assistant)
            content: Message content
            metadata: Optional metadata

        Returns:
            Success status
        """
        if not self.current_session_id:
            # Create new session if none exists
            self.create_session()

        return self.db.add_chat_message(
            self.current_session_id,
            role,
            content,
            metadata
        )

    def get_current_history(self, limit: int = None) -> List[Dict[str, str]]:
        """Get current session history in OpenAI format

        Args:
            limit: Maximum number of messages to return

        Returns:
            List of messages in OpenAI format
        """
        if not self.current_session_id:
            return []

        messages = self.db.get_chat_messages(self.current_session_id, limit)

        # Convert to OpenAI format
        openai_messages = []
        for msg in messages:
            openai_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        return openai_messages

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all available sessions

        Returns:
            List of session summaries
        """
        return self.db.list_chat_sessions(self.user_id)

    def delete_session(self, session_id: str) -> bool:
        """Delete a chat session

        Args:
            session_id: Session ID to delete

        Returns:
            Success status
        """
        success = self.db.delete_chat_session(session_id)

        # Clear current session if it was deleted
        if success and self.current_session_id == session_id:
            self.current_session_id = None
            self.current_session_name = None

        return success

    def rename_session(self, session_id: str, new_name: str) -> bool:
        """Rename a chat session

        Args:
            session_id: Session ID to rename
            new_name: New session name

        Returns:
            Success status
        """
        success = self.db.update_chat_session_name(session_id, new_name)

        # Update current session name if it's the active one
        if success and self.current_session_id == session_id:
            self.current_session_name = new_name

        return success

    def export_session(self, session_id: str, format: str = "json") -> Optional[str]:
        """Export a session to various formats

        Args:
            session_id: Session ID to export
            format: Export format (json, txt, md)

        Returns:
            Exported content as string
        """
        session_data = self.db.get_chat_session(session_id)
        if not session_data:
            return None

        messages = self.db.get_chat_messages(session_id)

        try:
            if format.lower() == "json":
                import json
                export_data = {
                    "session": session_data,
                    "messages": messages
                }
                return json.dumps(export_data, indent=2, ensure_ascii=False, default=str)

            elif format.lower() == "txt":
                content = f"Chat Session: {session_data.get('name')}\n"
                content += f"Created: {session_data.get('created_at')}\n"
                content += f"Updated: {session_data.get('updated_at')}\n"
                content += "=" * 50 + "\n\n"

                for msg in messages:
                    role = msg["role"].upper()
                    timestamp = msg.get("timestamp", "")
                    content += f"[{timestamp}] {role}:\n{msg['content']}\n\n"

                return content

            elif format.lower() == "md":
                content = f"# {session_data.get('name')}\n\n"
                content += f"**Created:** {session_data.get('created_at')}  \n"
                content += f"**Updated:** {session_data.get('updated_at')}  \n\n"
                content += "---\n\n"

                for msg in messages:
                    role = "🧑‍💼 **User**" if msg["role"] == "user" else "🤖 **Assistant**"
                    timestamp = msg.get("timestamp", "")
                    content += f"{role} *({timestamp})*\n\n{msg['content']}\n\n---\n\n"

                return content

            else:
                return None

        except Exception as e:
            print(f"Error exporting session {session_id}: {e}")
            return None

    def clear_current_session(self) -> bool:
        """Clear messages from current session

        Returns:
            Success status
        """
        if not self.current_session_id:
            return False

        return self.db.clear_chat_session_messages(self.current_session_id)

    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about chat sessions

        Returns:
            Statistics dictionary
        """
        stats = self.db.get_chat_stats(self.user_id)

        current_session_info = None
        if self.current_session_id:
            current_session_info = {
                "id": self.current_session_id,
                "name": self.current_session_name
            }

        return {
            "total_sessions": stats["total_sessions"],
            "total_messages": stats["total_messages"],
            "current_session": current_session_info,
            "most_recent": stats["most_recent"]
        }

    def get_session_messages_detailed(self, session_id: str) -> List[Dict[str, Any]]:
        """Get detailed messages from a session (including metadata)

        Args:
            session_id: Session ID

        Returns:
            List of detailed message data
        """
        return self.db.get_chat_messages(session_id)
