"""
Database operations module for FinBot
Handles all Supabase database interactions
"""

from typing import List, Dict, Any, Optional
from src.config import Clients, Config

class DatabaseManager:
    """Handles database operations"""

    def __init__(self):
        self.supabase = Clients.get_supabase()
        self.demo_mode = self.supabase is None

    def _check_demo_mode(self) -> bool:
        """Check if running in demo mode"""
        if self.demo_mode:
            print("Demo mode: Database operations disabled")
        return self.demo_mode

    def get_documents_count(self) -> int:
        """Get total number of documents"""
        if self.demo_mode:
            return 0
        result = self.supabase.table("documents").select("count", count="exact").execute()
        return result.count if result.count else 0

    def insert_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Insert documents in batches"""
        if self.demo_mode:
            return False
        try:
            batch_size = Config.BATCH_SIZE
            total_inserted = 0

            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                self.supabase.table("documents").insert(batch).execute()
                total_inserted += len(batch)

            return True
        except Exception as e:
            print(f"Error inserting documents: {e}")
            return False

    def search_documents(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search documents with filters"""
        if self.demo_mode:
            return []
        query = self.supabase.table("documents").select("*")

        # Apply filters
        if filters.get("gr_no"):
            query = query.ilike("gr_no", f"%{filters['gr_no']}%")

        if filters.get("branch"):
            query = query.eq("branch", filters["branch"])

        if filters.get("date"):
            query = query.eq("date", filters["date"])

        if filters.get("subject_en"):
            query = query.ilike("subject_en", f"%{filters['subject_en']}%")

        if filters.get("subject_gu"):
            query = query.ilike("subject_gu", f"%{filters['subject_gu']}%")

        result = query.execute()
        return result.data

    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID"""
        if self.demo_mode:
            return None
        result = self.supabase.table("documents").select("*").eq("id", doc_id).execute()
        return result.data[0] if result.data else None

    def update_document(self, document: Dict[str, Any]) -> bool:
        """Update a document in the database"""
        if self.demo_mode:
            return False
        try:
            # Build update data - only update fields that are provided
            update_data = {}
            
            if 'gr_no' in document:
                update_data['gr_no'] = document['gr_no']
            if 'pdf_valid' in document:
                update_data['pdf_valid'] = document['pdf_valid']
            if 'pdf_status' in document:
                update_data['pdf_status'] = document['pdf_status']
            if 'verification_date' in document:
                update_data['verification_date'] = document['verification_date']
            
            if not update_data:
                return False
                
            # Update by gr_no (assuming gr_no is unique or we update all matching)
            self.supabase.table("documents").update(update_data).eq("gr_no", document['gr_no']).execute()
            return True
        except Exception as e:
            print(f"Error updating document: {e}")
            return False

    def search_by_content(self, query_embedding: List[float], threshold: float = 0.78, limit: int = 10) -> List[Dict[str, Any]]:
        """Search documents by content similarity"""
        if self.demo_mode:
            return []
        result = self.supabase.rpc(
            "match_documents",
            {
                "query_embedding": query_embedding,
                "match_threshold": threshold,
                "match_count": limit
            }
        ).execute()
        return result.data

    def insert_vectors(self, vectors: List[Dict[str, Any]]) -> bool:
        """Insert vector embeddings"""
        if self.demo_mode:
            return False
        try:
            self.supabase.table("vectors").insert(vectors).execute()
            return True
        except Exception as e:
            print(f"Error inserting vectors: {e}")
            return False

    def clear_documents(self) -> bool:
        """Clear all documents (use with caution!)"""
        if self.demo_mode:
            return False
        try:
            # First clear vectors (due to foreign key constraint)
            self.supabase.table("vectors").delete().neq("id", "").execute()
            # Then clear documents
            self.supabase.table("documents").delete().neq("id", "").execute()
            return True
        except Exception as e:
            print(f"Error clearing documents: {e}")
            return False

    def get_branches(self) -> List[str]:
        """Get all unique branches"""
        if self.demo_mode:
            return []
        result = self.supabase.table("documents").select("branch").execute()
        branches = set(doc["branch"] for doc in result.data)
        return sorted(list(branches))

    def get_documents_by_branch(self, branch: str) -> List[Dict[str, Any]]:
        """Get all documents for a specific branch"""
        if self.demo_mode:
            return []
        result = self.supabase.table("documents").select("*").eq("branch", branch).execute()
        return result.data

    # Chat History Methods

    def create_chat_session(self, name: str, user_id: str = "default") -> Optional[str]:
        """Create a new chat session"""
        if self.demo_mode:
            return None
        try:
            result = self.supabase.table("chat_sessions").insert({
                "name": name,
                "user_id": user_id
            }).execute()

            if result.data:
                return result.data[0]["id"]
            return None
        except Exception as e:
            print(f"Error creating chat session: {e}")
            return None

    def get_chat_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a chat session by ID"""
        if self.demo_mode:
            return None
        try:
            result = self.supabase.table("chat_sessions").select("*").eq("id", session_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error getting chat session: {e}")
            return None

    def list_chat_sessions(self, user_id: str = "default", limit: int = 50) -> List[Dict[str, Any]]:
        """List chat sessions for a user"""
        if self.demo_mode:
            return []
        try:
            result = (self.supabase.table("chat_sessions")
                     .select("*, message_count:chat_messages(count)")
                     .eq("user_id", user_id)
                     .eq("is_active", True)
                     .order("updated_at", desc=True)
                     .limit(limit)
                     .execute())

            # Process the data to include message count
            sessions = []
            for session in result.data:
                session_data = {
                    "id": session["id"],
                    "name": session["name"],
                    "created_at": session["created_at"],
                    "updated_at": session["updated_at"],
                    "metadata": session.get("metadata", {}),
                    "message_count": len(session.get("message_count", []))
                }
                sessions.append(session_data)

            return sessions
        except Exception as e:
            print(f"Error listing chat sessions: {e}")
            return []

    def add_chat_message(self, session_id: str, role: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """Add a message to a chat session"""
        if self.demo_mode:
            return False
        try:
            # Get the next message order
            result = (self.supabase.table("chat_messages")
                     .select("message_order")
                     .eq("session_id", session_id)
                     .order("message_order", desc=True)
                     .limit(1)
                     .execute())

            next_order = 1
            if result.data:
                next_order = result.data[0]["message_order"] + 1

            # Insert the message
            self.supabase.table("chat_messages").insert({
                "session_id": session_id,
                "role": role,
                "content": content,
                "metadata": metadata or {},
                "message_order": next_order
            }).execute()

            return True
        except Exception as e:
            print(f"Error adding chat message: {e}")
            return False

    def get_chat_messages(self, session_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """Get messages from a chat session"""
        if self.demo_mode:
            return []
        try:
            query = (self.supabase.table("chat_messages")
                    .select("*")
                    .eq("session_id", session_id)
                    .order("message_order", desc=False))

            if limit:
                query = query.limit(limit)

            result = query.execute()
            return result.data
        except Exception as e:
            print(f"Error getting chat messages: {e}")
            return []

    def delete_chat_session(self, session_id: str) -> bool:
        """Delete a chat session (soft delete by marking inactive)"""
        if self.demo_mode:
            return False
        try:
            self.supabase.table("chat_sessions").update({
                "is_active": False
            }).eq("id", session_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting chat session: {e}")
            return False

    def update_chat_session_name(self, session_id: str, new_name: str) -> bool:
        """Update a chat session name"""
        if self.demo_mode:
            return False
        try:
            self.supabase.table("chat_sessions").update({
                "name": new_name
            }).eq("id", session_id).execute()
            return True
        except Exception as e:
            print(f"Error updating chat session name: {e}")
            return False

    def clear_chat_session_messages(self, session_id: str) -> bool:
        """Clear all messages from a chat session"""
        if self.demo_mode:
            return False
        try:
            self.supabase.table("chat_messages").delete().eq("session_id", session_id).execute()
            return True
        except Exception as e:
            print(f"Error clearing chat session messages: {e}")
            return False

    def get_chat_stats(self, user_id: str = "default") -> Dict[str, Any]:
        """Get chat history statistics"""
        if self.demo_mode:
            return {"total_sessions": 0, "total_messages": 0, "most_recent": None}
        try:
            # Get session count
            sessions_result = (self.supabase.table("chat_sessions")
                              .select("id", count="exact")
                              .eq("user_id", user_id)
                              .eq("is_active", True)
                              .execute())

            session_count = sessions_result.count or 0

            # Get total message count
            messages_result = (self.supabase.table("chat_messages")
                              .select("id", count="exact")
                              .in_("session_id",
                                   [s["id"] for s in (self.supabase.table("chat_sessions")
                                                     .select("id")
                                                     .eq("user_id", user_id)
                                                     .eq("is_active", True)
                                                     .execute()).data])
                              .execute())

            message_count = messages_result.count or 0

            # Get most recent session
            recent_result = (self.supabase.table("chat_sessions")
                            .select("*")
                            .eq("user_id", user_id)
                            .eq("is_active", True)
                            .order("updated_at", desc=True)
                            .limit(1)
                            .execute())

            most_recent = recent_result.data[0] if recent_result.data else None

            return {
                "total_sessions": session_count,
                "total_messages": message_count,
                "most_recent": most_recent
            }
        except Exception as e:
            print(f"Error getting chat stats: {e}")
            return {"total_sessions": 0, "total_messages": 0, "most_recent": None}
