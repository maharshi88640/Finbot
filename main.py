"""
Main FinBot application module
Optimized and modular version
"""

import streamlit as st
import json
from datetime import datetime
from pathlib import Path

# Add src to path
import sys
sys.path.append(str(Path(__file__).parent))

from src.chat import ChatManager
from src.core.database import DatabaseManager
from src.scraper import WebScraper

class FinBotApp:
    """Main FinBot Streamlit application"""

    def __init__(self):
        self.chat_manager = ChatManager()
        self.db_manager = DatabaseManager()
        self.scraper = WebScraper()

        # Initialize session state
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if "log_history" not in st.session_state:
            st.session_state.log_history = []
        if "current_session_id" not in st.session_state:
            st.session_state.current_session_id = None
        if "use_persistent_history" not in st.session_state:
            st.session_state.use_persistent_history = True

    def log_message(self, message: str):
        """Add message to log history"""
        st.session_state.log_history.append(message)
        if hasattr(self, 'logs_placeholder'):
            self.logs_placeholder.markdown(
                "\n".join(f"• {msg}" for msg in st.session_state.log_history[-10:])  # Show last 10 logs
            )

    def render_sidebar(self):
        """Render sidebar with system info and logs"""
        with st.sidebar:
            st.header("🤖 FinBot Control Panel")

            # Chat Session Management
            with st.expander("💬 Chat Sessions", expanded=True):
                # Create new session
                col1, col2 = st.columns([3, 1])
                with col1:
                    new_session_name = st.text_input("New Session Name", placeholder="Enter session name")
                with col2:
                    if st.button("➕"):
                        if new_session_name.strip():
                            session_id = self.chat_manager.create_new_session(new_session_name.strip())
                            st.session_state.current_session_id = session_id
                            st.session_state.chat_history = []
                            st.rerun()

                # Session stats
                stats = self.chat_manager.get_history_stats()
                if stats["current_session"]:
                    st.write(f"**Current:** {stats['current_session']['name']}")

                st.write(f"**Total Sessions:** {stats['total_sessions']}")
                st.write(f"**Total Messages:** {stats['total_messages']}")
                st.write("💾 **Storage:** Database (Supabase)")

                # Load existing session
                sessions = self.chat_manager.list_all_sessions()
                if sessions:
                    session_options = {f"{s['name']} ({s['message_count']} msgs)": s['id'] for s in sessions}
                    selected_session = st.selectbox("Load Session", ["Select a session..."] + list(session_options.keys()))

                    if selected_session != "Select a session..." and selected_session in session_options:
                        session_id = session_options[selected_session]
                        if st.button("📂 Load Session"):
                            if self.chat_manager.load_session(session_id):
                                st.session_state.current_session_id = session_id
                                # Load session history into streamlit session
                                session_history = self.chat_manager.get_session_history()
                                st.session_state.chat_history = session_history
                                st.rerun()

                # Session actions
                if st.session_state.current_session_id:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("🧹 Clear"):
                            if self.chat_manager.clear_current_session():
                                st.session_state.chat_history = []
                                st.rerun()
                    with col2:
                        if st.button("📥 Export"):
                            if st.session_state.current_session_id:
                                content = self.chat_manager.export_session(st.session_state.current_session_id, "md")
                                if content:
                                    st.download_button(
                                        "💾 Download",
                                        content,
                                        file_name=f"chat_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                                        mime="text/markdown"
                                    )
                    with col3:
                        if st.button("🗑️ Delete"):
                            if self.chat_manager.delete_session(st.session_state.current_session_id):
                                st.session_state.current_session_id = None
                                st.session_state.chat_history = []
                                st.rerun()

            # System Status
            with st.expander("📊 System Status", expanded=True):
                status = self.chat_manager.get_system_status()
                st.metric("Total Documents", status["total_documents"])
                st.metric("Branches", len(status["branches"]))

                # Branch breakdown
                if status["branches"]:
                    st.write("**Branches:**")
                    for branch in status["branches"]:
                        count = len(self.db_manager.get_documents_by_branch(branch))
                        st.write(f"• {branch}: {count} docs")

            # Processing Logs
            with st.expander("📝 Processing Logs", expanded=False):
                self.logs_placeholder = st.empty()
                if st.session_state.log_history:
                    self.logs_placeholder.markdown(
                        "\n".join(f"• {msg}" for msg in st.session_state.log_history[-10:])
                    )
                else:
                    self.logs_placeholder.markdown("• No logs yet")

            # Quick Actions
            with st.expander("⚡ Quick Actions", expanded=False):
                # Persistent history toggle
                use_persistent = st.checkbox("Use Persistent History", value=st.session_state.use_persistent_history)
                if use_persistent != st.session_state.use_persistent_history:
                    st.session_state.use_persistent_history = use_persistent
                    st.rerun()

                if st.button("🕷️ Scrape Sample Data"):
                    self.scrape_sample_data()

                if st.button("🧹 Clear Session Chat"):
                    st.session_state.chat_history = []
                    st.rerun()

                if st.button("📊 Refresh Status"):
                    st.rerun()

    def scrape_sample_data(self):
        """Scrape sample data"""
        try:
            self.log_message("Starting sample scraping...")
            with st.spinner("Scraping sample data..."):
                data = self.scraper.scrape_sample(num_branches=1, records_per_branch=5)
                self.log_message(f"✅ Scraped {len(data)} records")
                st.success(f"Successfully scraped {len(data)} records!")
                st.rerun()
        except Exception as e:
            self.log_message(f"❌ Scraping error: {e}")
            st.error(f"Scraping failed: {e}")

    def render_chat_interface(self):
        """Render main chat interface"""
        st.title("🏦 FinBot - Financial Document Assistant")
        st.markdown("Ask me anything about financial documents, search for specific documents, or get summaries!")

        # Display chat history
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.chat_message("user").write(message["content"])
            elif message["role"] == "assistant":
                st.chat_message("assistant").write(message["content"])

        # Chat input
        if prompt := st.chat_input("Type your query here..."):
            # Add user message to history
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            # Process message
            try:
                self.log_message("Processing user query...")
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        # Determine if we should use persistent history
                        use_persistent = st.session_state.use_persistent_history

                        # Create session if needed and using persistent history
                        if use_persistent and not st.session_state.current_session_id:
                            session_id = self.chat_manager.create_new_session(f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                            st.session_state.current_session_id = session_id

                        # Get chat history for context
                        if use_persistent and st.session_state.current_session_id:
                            # Use persistent history from database
                            recent_history = self.chat_manager.get_session_history(10)
                            response = self.chat_manager.process_message(prompt, recent_history, save_to_history=True)
                        else:
                            # Use session-only history
                            recent_history = st.session_state.chat_history[-10:-1]  # Exclude current message
                            response = self.chat_manager.process_message(prompt, recent_history, save_to_history=False)

                        st.write(response)

                        # Add assistant response to session history
                        st.session_state.chat_history.append({"role": "assistant", "content": response})

                        self.log_message("✅ Query processed successfully")

            except Exception as e:
                st.error(f"Error processing message: {e}")
                self.log_message(f"❌ Error: {e}")

    def run(self):
        """Run the Streamlit application"""
        st.set_page_config(
            page_title="FinBot",
            page_icon="🏦",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Custom CSS
        st.markdown("""
        <style>
        .main > div {
            padding-top: 2rem;
        }
        .stChatMessage {
            margin-bottom: 1rem;
        }
        </style>
        """, unsafe_allow_html=True)

        # Render components
        self.render_sidebar()
        self.render_chat_interface()

def main():
    """Main application entry point"""
    try:
        app = FinBotApp()
        app.run()
    except Exception as e:
        st.error(f"Application error: {e}")
        st.stop()

if __name__ == "__main__":
    main()
