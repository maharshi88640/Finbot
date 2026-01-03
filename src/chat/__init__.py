"""
Chat interface module for FinBot
Handles chat functionality and tool calling
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.core.database import DatabaseManager
from src.core.ai import AIManager
from .db_history import DatabaseChatHistoryManager

class ChatManager:
    """Handles chat operations and tool calling"""

    def __init__(self):
        self.db = DatabaseManager()
        self.ai = AIManager()
        self.history = DatabaseChatHistoryManager()
        self.tools = self._get_tools_definition()

    def _get_tools_definition(self) -> List[Dict]:
        """Get tools definition for OpenAI function calling"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_pdf_related_data",
                    "description": "Search for government documents using specific criteria like GR numbers, dates, branches, or subjects. Use this for targeted searches when user provides specific details.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "gr_no": {
                                "type": "string",
                                "description": "Government Resolution number (e.g., પગર-૧૦૨૦૨૩-૦૧-મ, STS-1096-535-Adt.07-03-1996). Can be in Gujarati or English."
                            },
                            "date": {
                                "type": "string",
                                "description": "Document date or year (e.g., 2023-04-17, 2023, April 2023). Use for finding documents from specific time periods."
                            },
                            "branch": {
                                "type": "string",
                                "enum": [
                                    "A-(Public Sector Undertaking)",
                                    "CH-(Service Matter)",
                                    "K-(Budget)",
                                    "M-(Pay of Government Employee)",
                                    "PayCell-(Pay Commission)",
                                    "N-(Banking)",
                                    "P-(Pension)",
                                    "T-(Local Establishment)",
                                    "TH-(Value Added Tax)",
                                    "TH-3-(Commercial Tax Establishment)",
                                    "Z-(Treasury)",
                                    "Z-1-(Economy)",
                                    "G-(Audit Para)",
                                    "GH-(Accounts Cadre Establishment)",
                                    "FR-(Financial Resources)",
                                    "DMO-(Debt Management)",
                                    "GO Cell-(Government Companies)",
                                    "B-RTI Cell-(Small Savings RTI)",
                                    "KH",
                                    "PMU-Cell",
                                    "GST Cell"
                                ],
                                "description": "Government department branch. Most common: 'M-(Pay of Government Employee)' for salary/pay matters, 'PayCell-(Pay Commission)' for pay commission orders."
                            },
                            "subject_en": {
                                "type": "string",
                                "description": "Search terms for document subject in English (e.g., 'pay scale', 'salary revision', 'allowance')"
                            },
                            "subject_gu": {
                                "type": "string",
                                "description": "Search terms for document subject in Gujarati"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_pdf_by_content",
                    "description": "Perform semantic search across all documents using natural language queries. Use this for broad searches or when looking for concepts rather than specific document details.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "Natural language search query (e.g., 'salary increases for government employees', 'pension benefits', 'pay commission recommendations')"
                            }
                        },
                        "required": ["content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "summarize_pdf",
                    "description": "Summarize PDF content from URL",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pdf_url": {"type": "string", "description": "PDF URL"}
                        },
                        "required": ["pdf_url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_pdf",
                    "description": "Answer questions based on specific PDF content when you have a document URL",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pdf_url": {"type": "string", "description": "PDF URL from search results"},
                            "query": {"type": "string", "description": "Specific question about the PDF content"}
                        },
                        "required": ["pdf_url", "query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "extract_gujarati_text",
                    "description": "Extract Gujarati text from PDF using specialized OCR. Use this when dealing with Gujarati government documents that may not extract properly with standard methods.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pdf_url": {"type": "string", "description": "PDF URL to extract Gujarati text from"}
                        },
                        "required": ["pdf_url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_database_overview",
                    "description": "Get overview of available documents, branches, and recent additions. Use this to help users understand what data is available.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]

    def get_pdf_related_data(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Search documents in database"""
        try:
            results = self.db.search_documents(args)
            # Format results with clickable links
            formatted_results = []
            for doc in results:
                pdf_url = doc.get('pdf_url', '')
                gr_no = doc.get('gr_no', 'N/A')
                date = doc.get('date', 'N/A')
                branch = doc.get('branch', 'N/A')
                subject = doc.get('subject_en', doc.get('subject_ur', 'No subject'))
                
                formatted_doc = {
                    "gr_no": gr_no,
                    "date": date,
                    "branch": branch,
                    "subject": subject,
                    "pdf_url": pdf_url,
                    "pdf_link": f"[📄 View Document]({pdf_url})" if pdf_url else "No PDF available"
                }
                formatted_results.append(formatted_doc)
            
            return {"results": formatted_results, "formatted": True}
        except Exception as e:
            return {"error": str(e)}

    def get_pdf_by_content(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Search documents by content similarity"""
        try:
            content = args.get("content", "")
            embedding = self.ai.create_embedding(content)
            results = self.db.search_by_content(embedding)
            return {"results": results}
        except Exception as e:
            return {"error": str(e)}

    def summarize_pdf(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Summarize PDF content"""
        try:
            pdf_url = args.get("pdf_url")
            summary = self.ai.summarize_pdf(pdf_url)
            return {"summary": summary}
        except Exception as e:
            return {"error": str(e)}

    def query_pdf(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Answer question based on PDF content"""
        try:
            pdf_url = args.get("pdf_url")
            query = args.get("query")
            answer = self.ai.answer_question_from_pdf(pdf_url, query)
            return {"answer": answer}
        except Exception as e:
            return {"error": str(e)}

    def extract_gujarati_text(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Extract Gujarati text from PDF using specialized OCR"""
        try:
            pdf_url = args.get("pdf_url")
            text = self.ai.extract_gujarati_text(pdf_url)
            return {"text": text}
        except Exception as e:
            return {"error": str(e)}

    def get_database_overview(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Get database overview and statistics"""
        try:
            total_docs = self.db.get_documents_count()
            branches = self.db.get_branches()

            # Get document count per branch
            branch_stats = {}
            for branch in branches:
                branch_docs = self.db.get_documents_by_branch(branch)
                branch_stats[branch] = len(branch_docs)

            # Get some recent documents with links
            recent_docs = self.db.search_documents({})[:5]
            recent_summary = []
            for doc in recent_docs:
                pdf_url = doc.get('pdf_url', '')
                recent_summary.append({
                    "gr_no": doc.get("gr_no", "N/A"),
                    "date": doc.get("date", "N/A"),
                    "branch": doc.get("branch", "N/A"),
                    "subject": doc.get("subject_en", doc.get("subject_ur", "N/A"))[:100] + "..." if len(doc.get("subject_en", doc.get("subject_ur", ""))) > 100 else doc.get("subject_en", doc.get("subject_ur", "N/A")),
                    "pdf_url": pdf_url,
                    "pdf_link": f"[📄 View PDF]({pdf_url})" if pdf_url else "No PDF available"
                })

            return {
                "total_documents": total_docs,
                "branches": branches,
                "branch_statistics": branch_stats,
                "recent_documents": recent_summary,
                "available_search_options": [
                    "Search by GR number",
                    "Search by date/year",
                    "Search by branch",
                    "Search by subject keywords",
                    "Semantic content search"
                ]
            }
        except Exception as e:
            return {"error": str(e)}

    def call_tool(self, tool_call) -> Dict[str, Any]:
        """Execute a tool call"""
        try:
            args = json.loads(tool_call.function.arguments)
            tool_name = tool_call.function.name

            tool_functions = {
                "get_pdf_related_data": self.get_pdf_related_data,
                "get_pdf_by_content": self.get_pdf_by_content,
                "summarize_pdf": self.summarize_pdf,
                "query_pdf": self.query_pdf,
                "extract_gujarati_text": self.extract_gujarati_text,
                "get_database_overview": self.get_database_overview
            }

            if tool_name in tool_functions:
                return tool_functions[tool_name](args)
            else:
                return {"error": f"Unknown tool: {tool_name}"}

        except json.JSONDecodeError:
            return {"error": "Invalid arguments format"}
        except Exception as e:
            return {"error": str(e)}

    def process_message(self, user_message: str, chat_history: List[Dict[str, str]] = None, save_to_history: bool = True) -> str:
        """Process a user message and return response"""
        if chat_history is None:
            chat_history = []

        # Save user message to persistent history
        if save_to_history:
            self.history.save_message("user", user_message)

        # Add system context
        total_docs = self.db.get_documents_count()
        branches = self.db.get_branches()
        system_prompt = f"""
        You are FinBot, an AI assistant specialized in querying and analyzing financial and administrative documents from government departments.

        DOCUMENT DATABASE:
        - Total documents: {total_docs}
        - Available branches: {', '.join(branches)}
        - Document types: Government orders, pay commission notifications, administrative circulars
        - Languages: English and Gujarati (some documents bilingual)
        - Current time: {datetime.now().strftime("%H:%M:%S %d-%m-%Y")}

        CAPABILITIES:
        1. Search documents by GR number, subject, branch, or date
        2. Summarize documents and extract key information
        3. Enhanced Gujarati text extraction with specialized OCR tools
        4. Compare documents across different time periods
        5. Analyze pay policies and administrative changes
        6. Find related documents on similar topics

        RESPONSE FORMATTING - VERY IMPORTANT:
        - When showing search results, ALWAYS include the PDF link using markdown format: [📄 View Document](URL)
        - Format each document as:
          **GR No:** [GR_NUMBER](PDF_URL)
          **Date:** DATE
          **Branch:** BRANCH
          **Subject:** SUBJECT
          **Link:** [📄 View PDF](PDF_URL)
        - Always make document links clickable and prominent
        - If multiple documents are found, list them as a numbered list with full details

        TEXT EXTRACTION FEATURES:
        - Enhanced pypdf extraction with better Unicode handling for Gujarati
        - Specialized Gujarati text extraction tool for better language support
        - Multi-method approach: tries best method first, falls back to alternatives
        - Handles mixed English-Gujarati content effectively

        RESPONSE GUIDELINES:
        - Always use available tools to search for relevant documents before answering
        - For Gujarati documents, use extract_gujarati_text tool for better results
        - Provide specific document references (GR numbers, dates) when possible
        - Summarize key points clearly and concisely
        - If documents are in Gujarati, provide English summaries
        - For pay-related queries, focus on salary scales, allowances, and policy changes
        - When multiple documents are found, prioritize by relevance and recency
        - If text extraction seems garbled, explain that OCR installation may improve results

        SAMPLE QUERIES YOU CAN HANDLE:
        - "Find documents about pay scale revisions"
        - "Extract Gujarati text from this PDF: [URL]"
        - "Show me recent government orders from Pay Commission"
        - "What are the latest salary policies for government employees?"
        - "Find documents from 2023 about employee benefits"
        - "Search for GR number"

        EXAMPLE OF GOOD RESPONSE FORMAT:
        I found the following documents:

        1. **GR No:** M_2641_17-Apr-2023_450
           **Date:** 2023-04-17
           **Branch:** M-(Pay of Government Employee)
           **Subject:** Pay scale revision for government employees
           **Link:** [📄 View PDF](https://financedepartment.gujarat.gov.in/...)

        2. **GR No:** PayCell_2863_02-Apr-2025_231
           **Date:** 2025-04-02
           **Branch:** PayCell-(Pay Commission)
           **Subject:** Pay commission recommendations
           **Link:** [📄 View PDF](https://financedepartment.gujarat.gov.in/...)

        Always provide helpful, accurate, and well-structured responses based on the available documents.
        """

        messages = [{"role": "system", "content": system_prompt}] + chat_history
        messages.append({"role": "user", "content": user_message})

        # Process with function calling
        retry_count = 0
        max_retries = 2
        
        while retry_count < max_retries:
            response = self.ai.chat_completion(messages, self.tools)
            
            # Handle case where response is None or dict (error marker)
            if response is None or (isinstance(response, dict) and response.get("error_type")):
                # Handle quota exceeded error
                if isinstance(response, dict) and response.get("error_type") == "quota_exceeded":
                    # Try to get database info and provide a fallback response
                    try:
                        total_docs = self.db.get_documents_count()
                        branches = self.db.get_branches()
                        fallback_msg = f"""I'm unable to connect to OpenAI's AI services due to an API quota issue. However, I can still help you search our document database!

**Database Status:**
- Total documents indexed: {total_docs}
- Available branches: {len(branches)}

**Available Branches:**
{chr(10).join([f"- {b}" for b in branches[:10]])}

**How to Fix AI Responses:**
1. Go to https://platform.openai.com/account/billing
2. Add a payment method or check your usage
3. Your quota resets at the start of each month

**What would you like to do?**
- Search for documents by GR number, date, branch, or subject
- Get an overview of the database
- I can still answer basic questions about the system!

Please try searching for a specific document or let me know what you're looking for."""
                        if save_to_history:
                            self.history.save_message("assistant", fallback_msg)
                        return fallback_msg
                    except Exception:
                        error_msg = "OpenAI API quota exceeded. Please check your OpenAI account billing settings at https://platform.openai.com/account/billing"
                        if save_to_history:
                            self.history.save_message("assistant", error_msg)
                        return error_msg
                
                # Handle auth error
                if isinstance(response, dict) and response.get("error_type") == "auth_error":
                    error_msg = "OpenAI API authentication failed. Please check your API key in the .env file."
                    if save_to_history:
                        self.history.save_message("assistant", error_msg)
                    return error_msg
                
                # Generic error for None response
                error_msg = "Failed to get response from AI. Please check your API credentials and try again."
                if save_to_history:
                    self.history.save_message("assistant", error_msg)
                return error_msg
            
            # Add assistant message to history
            messages.append({
                "role": "assistant",
                "content": response.content,
                "tool_calls": [tool_call.model_dump() for tool_call in response.tool_calls] if response.tool_calls else None
            })

            # Return if no tool calls
            if not response.tool_calls:
                # Save assistant response to persistent history
                if save_to_history:
                    self.history.save_message("assistant", response.content)
                return response.content

            # Execute tool calls
            for tool_call in response.tool_calls:
                tool_response = self.call_tool(tool_call)
                messages.append({
                    "role": "tool",
                    "content": json.dumps(tool_response),
                    "tool_call_id": tool_call.id
                })
            
            retry_count += 1
        
        # If we exhausted retries
        error_msg = "Unable to process your request. Please try again."
        if save_to_history:
            self.history.save_message("assistant", error_msg)
        return error_msg

    def get_system_status(self) -> Dict[str, Any]:
        """Get system status information"""
        return {
            "total_documents": self.db.get_documents_count(),
            "branches": self.db.get_branches(),
            "timestamp": datetime.now().isoformat()
        }

    # Chat History Management Methods

    def create_new_session(self, name: str = None) -> str:
        """Create a new chat session"""
        return self.history.create_session(name)

    def load_session(self, session_id: str) -> bool:
        """Load an existing chat session"""
        session_data = self.history.load_session(session_id)
        return session_data is not None

    def get_session_history(self, limit: int = None) -> List[Dict[str, str]]:
        """Get current session history for chat context"""
        return self.history.get_current_history(limit)

    def list_all_sessions(self) -> List[Dict[str, Any]]:
        """List all available chat sessions"""
        return self.history.list_sessions()

    def delete_session(self, session_id: str) -> bool:
        """Delete a chat session"""
        return self.history.delete_session(session_id)

    def rename_session(self, session_id: str, new_name: str) -> bool:
        """Rename a chat session"""
        return self.history.rename_session(session_id, new_name)

    def export_session(self, session_id: str, format: str = "json") -> Optional[str]:
        """Export a session to various formats"""
        return self.history.export_session(session_id, format)

    def clear_current_session(self) -> bool:
        """Clear current session messages"""
        return self.history.clear_current_session()

    def get_history_stats(self) -> Dict[str, Any]:
        """Get chat history statistics"""
        return self.history.get_session_stats()
