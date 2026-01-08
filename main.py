"""
Main FinBot application module
Fixed PDF link handling and improved logging
"""

import streamlit as st
import json
import re
from datetime import datetime
from pathlib import Path

# Add src to path
import sys
sys.path.append(str(Path(__file__).parent))

from src.chat import ChatManager
from src.core.database import DatabaseManager
from src.scraper import WebScraper
from src.pdf_proxy import start_proxy_server

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
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        st.session_state.log_history.append(log_entry)
        print(log_entry)  # Also print to console for debugging

    def render_logs(self):
        """Render logs in sidebar"""
        if hasattr(self, 'logs_placeholder') and self.logs_placeholder:
            if st.session_state.log_history:
                recent_logs = st.session_state.log_history[-10:]
                log_text = "\n".join(f"• {msg}" for msg in recent_logs)
                self.logs_placeholder.markdown(log_text)
            else:
                self.logs_placeholder.markdown("• No logs yet")

    def render_pdf_links_html(self, text: str):
        """Render PDF links using pure HTML that opens directly in new tab"""
        # Pattern to match markdown links: [text](url)
        link_pattern = r'\[([^\]]+)\]\((https?://[^)]+)\)'
        
        # Find all links
        links = re.findall(link_pattern, text)
        
        if not links:
            # No links found, just render the text
            st.markdown(text)
            return
        
        # Process each link
        remaining_text = text
        link_count = 0
        
        for link_text, url in links:
            # Skip empty links or non-PDF links (optional filter)
            if url.endswith('.pdf') or 'financedepartment' in url:
                link_count += 1
                # Create HTML button that opens directly in new tab
                button_html = f'''
                <a href="{url}" target="_blank" rel="noopener noreferrer"
                   style="display: inline-flex; align-items: center; gap: 6px;
                          padding: 6px 12px; background-color: #FF4B4B;
                          color: white; text-decoration: none; border-radius: 4px;
                          font-size: 14px; font-weight: 500; margin: 4px 4px 4px 0;
                          cursor: pointer;">
                   <span>📄</span> <span>Open PDF</span>
                </a>
                '''
                
                # Replace the markdown link with the button
                markdown_link = f"[{link_text}]({url})"
                remaining_text = remaining_text.replace(markdown_link, button_html)
        
        # Render the final HTML
        if remaining_text.strip():
            st.markdown(remaining_text, unsafe_allow_html=True)

    def render_sidebar(self):
        """Render sidebar with system info and logs"""
        with st.sidebar:
            st.header("🤖 FinBot Control Panel")

            # Debug info
            st.info(f"Debug: Python {sys.version.split()[0]}")

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
            with st.expander("📝 Processing Logs", expanded=True):
                self.logs_placeholder = st.empty()
                self.render_logs()

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

    def render_chat_message(self, role: str, content: str):
        """Render a chat message with proper PDF link handling"""
        if role == "user":
            st.chat_message("user").write(content)
        elif role == "assistant":
            # Use container to control HTML rendering
            with st.chat_message("assistant"):
                self.render_pdf_links_html(content)

    def render_chat_interface(self):
        """Render main chat interface"""
        st.title("🏦 FinBot - Financial Document Assistant")
        st.markdown("Ask me anything about financial documents, search for specific documents, or get summaries!")

        # Debug info
        st.caption(f"Session ID: {st.session_state.get('current_session_id', 'None')}")

        # Display chat history
        for i, message in enumerate(st.session_state.chat_history):
            self.render_chat_message(message["role"], message["content"])

        # Chat input
        if prompt := st.chat_input("Type your query here..."):
            # Add user message to history
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            # Process message
            try:
                self.log_message(f"User query: {prompt[:50]}...")
                
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        # Determine if we should use persistent history
                        use_persistent = st.session_state.use_persistent_history

                        # Create session if needed and using persistent history
                        if use_persistent and not st.session_state.current_session_id:
                            session_id = self.chat_manager.create_new_session(f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                            st.session_state.current_session_id = session_id
                            self.log_message(f"Created new session: {session_id}")

                        # Get chat history for context
                        if use_persistent and st.session_state.current_session_id:
                            # Use persistent history from database
                            recent_history = self.chat_manager.get_session_history(10)
                            self.log_message(f"Using persistent history, {len(recent_history)} messages")
                            response = self.chat_manager.process_message(prompt, recent_history, save_to_history=True)
                        else:
                            # Use session-only history
                            recent_history = st.session_state.chat_history[-10:-1]
                            self.log_message(f"Using session history, {len(recent_history)} messages")
                            response = self.chat_manager.process_message(prompt, recent_history, save_to_history=False)

                        # Render response with proper PDF link handling
                        self.render_pdf_links_html(response)

                        self.log_message("✅ Response rendered")

                # Add assistant response to session history
                st.session_state.chat_history.append({"role": "assistant", "content": response})

            except Exception as e:
                error_msg = f"Error processing message: {e}"
                st.error(error_msg)
                self.log_message(f"❌ {error_msg}")
                import traceback
                traceback.print_exc()

    def run(self):
        """Run the Streamlit application"""
        # Start local PDF proxy that forces inline Content-Disposition
        try:
            start_proxy_server()
        except Exception as e:
            print(f"Failed to start PDF proxy: {e}")

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
        /* Ensure links open in new tab */
        .stMarkdown a {
            target-name: _blank;
        }
        </style>
        """, unsafe_allow_html=True)

        # Render components
        self.render_sidebar()
        self.render_chat_interface()

def main():
    """Main application entry point"""
    try:
        print("Starting FinBot application...")
        app = FinBotApp()
        app.run()
    except Exception as e:
        print(f"Application error: {e}")
        import traceback
        traceback.print_exc()
        st.error(f"Application error: {e}")
        st.stop()

if __name__ == "__main__":
    main()
