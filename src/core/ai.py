"""
AI operations module for FinBot
Handles Gemini interactions, embeddings, and chat completions
"""

import json
import httpx
import tiktoken
from typing import List, Dict, Any
try:
    from pdf2image import convert_from_bytes
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

import pypdf
from io import BytesIO

from src.config import Clients, Config

class AIManager:
    """Handles AI operations - Gemini only"""

    def __init__(self):
        self.gemini_client = Clients.get_gemini()
        self.demo_mode = self.gemini_client is None
        self.encoding = tiktoken.encoding_for_model("gpt-4o-mini")

    def create_embedding(self, text: str) -> List[float]:
        """Create embedding for text"""
        if self.demo_mode:
            return []
        # Gemini doesn't have embeddings API in the same way - return empty list
        return []

    def chat_completion(self, messages: List[Dict[str, str]], tools: List[Dict] = None) -> Any:
        """Create chat completion using Gemini only"""
        if self.demo_mode:
            return None
        
        # Use Gemini
        if self.gemini_client:
            try:
                return self._gemini_chat_completion(messages, tools)
            except Exception as e:
                print(f"Gemini API error: {e}")
                return {"error_type": "api_error", "message": str(e)}
        
        return {"error_type": "no_provider", "message": "No AI provider available"}

    def _gemini_chat_completion(self, messages: List[Dict[str, str]], tools: List[Dict] = None) -> Any:
        """Gemini chat completion using google.generativeai API"""
        # Extract system prompt and user messages
        system_prompt = ""
        user_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            elif msg["role"] == "user":
                user_messages.append(msg["content"])
            elif msg["role"] == "assistant":
                user_messages.append(f"Assistant: {msg['content']}")
        
        # Build the prompt with system instruction
        last_message = user_messages[-1] if user_messages else ""
        prompt = last_message
        
        if system_prompt:
            prompt = f"{system_prompt}\n\nUser: {last_message}"
        
        # Use google.generativeai API
        try:
            model = self.gemini_client.GenerativeModel(Config.GEMINI_MODEL)
            response = model.generate_content(prompt)
            
            # Extract the response text
            response_text = ""
            if hasattr(response, 'text'):
                response_text = response.text
            elif hasattr(response, 'candidates'):
                response_text = response.candidates[0].content.parts[0].text
            
            # Return as ChatCompletionMessage-like object
            class MockMessage:
                def __init__(self, content):
                    self.content = content
                    self.tool_calls = None
                def model_dump(self):
                    return {"content": self.content}
            
            return MockMessage(response_text)
            
        except Exception as e:
            print(f"Gemini API error: {e}")
            raise e

    def summarize_text(self, text: str, prompt: str = None) -> str:
        """Summarize text using AI"""
        if self.demo_mode:
            return "Demo mode: AI summarization disabled"
        
        if self.gemini_client:
            try:
                if not prompt:
                    prompt = "Summarize the given content with all the important details."
                full_prompt = f"{prompt}\n\nContent:\n{text}"
                model = self.gemini_client.GenerativeModel(Config.GEMINI_MODEL)
                response = model.generate_content(full_prompt)
                if hasattr(response, 'text'):
                    return response.text
                elif hasattr(response, 'candidates'):
                    return response.candidates[0].content.parts[0].text
            except Exception as e:
                print(f"Gemini summarization error: {e}")
        
        return "AI service unavailable"

    def process_pdf_from_url(self, pdf_url: str) -> str:
        """Extract text from PDF URL using multiple methods with enhanced Gujarati support"""
        try:
            with httpx.Client() as client:
                response = client.get(pdf_url)
                response.raise_for_status()

            pdf_binary = response.content

            # Method 1: Try pypdf with enhanced text extraction first
            try:
                pdf_file = BytesIO(pdf_binary)
                pdf_reader = pypdf.PdfReader(pdf_file)

                text = ""
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text.strip():  # Only add non-empty text
                        text += page_text + "\n"

                # If we got text, clean it up and return
                if text.strip():
                    # Clean up common PDF extraction artifacts
                    text = text.replace('\x00', '')  # Remove null bytes
                    text = ' '.join(text.split())  # Normalize whitespace
                    return text
            except Exception as e:
                print(f"pypdf extraction failed: {e}")

            # Method 2: Try OCR if available and pypdf failed
            if PDF2IMAGE_AVAILABLE and PYTESSERACT_AVAILABLE:
                try:
                    images = convert_from_bytes(pdf_binary, dpi=200)
                    text = ""
                    for img in images:
                        # Use multiple languages for better coverage
                        page_text = pytesseract.image_to_string(
                            img,
                            lang="eng+guj+hin+san",  # English, Gujarati, Hindi, Sanskrit
                            config='--psm 6 --oem 3'  # Better OCR configuration
                        )
                        if page_text.strip():
                            text += page_text + "\n"

                    if text.strip():
                        return text
                except Exception as e:
                    print(f"OCR extraction failed: {e}")

            # Method 3: Return message about limitations
            return "PDF text extraction completed, but content may be limited. For better Gujarati text extraction, OCR libraries (Tesseract) need to be installed."

        except Exception as e:
            raise Exception(f"Error processing PDF: {e}")

    def extract_text_simple(self, pdf_url: str) -> str:
        """Simple text extraction with OCR fallback for Gujarati support"""
        try:
            with httpx.Client() as client:
                response = client.get(pdf_url)
                response.raise_for_status()

            pdf_binary = response.content

            # Try OCR first for better Gujarati handling
            if PDF2IMAGE_AVAILABLE and PYTESSERACT_AVAILABLE:
                try:
                    images = convert_from_bytes(pdf_binary)
                    text = ""
                    for img in images:
                        page_text = pytesseract.image_to_string(
                            img,
                            lang="eng+guj+hin",
                            config='--psm 6 --oem 3'
                        )
                        if page_text.strip():
                            text += page_text + "\n"

                    if text.strip():
                        return text
                except Exception as e:
                    print(f"OCR failed, trying pypdf: {e}")

            # Fallback to pypdf
            pdf_file = BytesIO(pdf_binary)
            pdf_reader = pypdf.PdfReader(pdf_file)

            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text.strip():
                    text += page_text + "\n"

            return text if text.strip() else "No text found in PDF"

        except Exception as e:
            return f"Error extracting text: {e}"

    def extract_gujarati_text(self, pdf_url: str) -> str:
        """Specialized method for Gujarati text extraction using OCR"""
        try:
            if not (PDF2IMAGE_AVAILABLE and PYTESSERACT_AVAILABLE):
                return "OCR libraries (pdf2image and pytesseract) are available, but Tesseract OCR engine is not installed. Please install Tesseract OCR for Gujarati text extraction. For now, trying pypdf extraction..."

            # Check if tesseract is actually working
            try:
                import pytesseract
                pytesseract.get_tesseract_version()
            except:
                # Fall back to enhanced pypdf extraction
                return self._extract_with_enhanced_pypdf(pdf_url)

            with httpx.Client() as client:
                response = client.get(pdf_url)
                response.raise_for_status()

            pdf_binary = response.content
            images = convert_from_bytes(pdf_binary, dpi=300)  # Higher DPI for better OCR

            text = ""
            for i, img in enumerate(images):
                print(f"Processing page {i+1} for Gujarati text...")
                page_text = pytesseract.image_to_string(
                    img,
                    lang="guj+eng+hin",  # Gujarati first
                    config='--psm 6 --oem 3 -c tessedit_char_whitelist=અઆઇઈઉઊએઐઓઔકખગઘઙચછજઝઞટઠડઢણતથદધનપફબભમયરલવશષસહળક્ષજ્ઞાિીુૂేૈોૌ્ૂંઃ૦૧૨૩૪૫૬૭૮૯abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,;:!?()[]{}"\'-/ '
                )
                if page_text.strip():
                    text += page_text + "\n"

            return text if text.strip() else "No Gujarati text found in PDF"

        except Exception as e:
            # Fall back to enhanced pypdf extraction
            return self._extract_with_enhanced_pypdf(pdf_url)

    def _extract_with_enhanced_pypdf(self, pdf_url: str) -> str:
        """Enhanced pypdf extraction with better Unicode handling"""
        try:
            with httpx.Client() as client:
                response = client.get(pdf_url)
                response.raise_for_status()

            pdf_binary = response.content
            pdf_file = BytesIO(pdf_binary)
            pdf_reader = pypdf.PdfReader(pdf_file)

            text = ""
            for page in pdf_reader.pages:
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        # Better Unicode handling for Gujarati text
                        page_text = page_text.encode('utf-8', errors='ignore').decode('utf-8')
                        text += page_text + "\n"
                except Exception as e:
                    print(f"Error extracting page: {e}")
                    continue

            if text.strip():
                # Clean up the text
                text = text.replace('\x00', '')  # Remove null bytes
                text = ' '.join(text.split())  # Normalize whitespace
                return text
            else:
                return "No text found in PDF using pypdf extraction"

        except Exception as e:
            return f"Error in enhanced pypdf extraction: {e}"

    def summarize_pdf(self, pdf_url: str, metadata: dict = None) -> str:
        """Summarize PDF content with enhanced path info including branch and GR number"""
        if self.demo_mode:
            return "Demo mode: PDF summarization disabled"
        
        # Build enhanced path info from metadata
        path_info = {
            'pdf_url': pdf_url,
            'gr_no': metadata.get('gr_no', 'Unknown') if metadata else 'Unknown',
            'branch': metadata.get('branch', 'Unknown') if metadata else 'Unknown',
            'subject': metadata.get('subject_en', '') if metadata else '',
            'date': metadata.get('date', '') if metadata else '',
            'source_page': metadata.get('source_page', '') if metadata else '',
            'source_url': metadata.get('source_url', '') if metadata else '',
            'route': metadata.get('navigation_route', '') if metadata else ''
        }
        
        print(f"\n📄 SUMMARIZING PDF:")
        print(f"   GR No: {path_info['gr_no']}")
        print(f"   Branch: {path_info['branch']}")
        print(f"   Source Page: {path_info['source_page']}")
        print(f"   Source URL: {path_info['source_url']}")
        print(f"   PDF URL: {pdf_url}")
        print(f"   Route: {path_info['route']}")
        
        text = self.process_pdf_from_url(pdf_url)

        # Handle large texts by chunking
        max_tokens = Config.MAX_TOKENS
        summaries = []
        current_text = ""

        for line in text.split('\n'):
            test_text = current_text + line + '\n'
            if len(self.encoding.encode(test_text)) < max_tokens:
                current_text = test_text
            else:
                if current_text:
                    summary = self.summarize_text(current_text)
                    summaries.append(summary)
                current_text = line + '\n'

        # Process remaining text
        if current_text:
            summary = self.summarize_text(current_text)
            summaries.append(summary)

        # Create final summary if multiple chunks
        if len(summaries) > 1:
            combined_summaries = "\n\n".join(summaries)
            final_summary = self.summarize_text(
                combined_summaries,
                "Given the summaries separated by double newlines, generate a final comprehensive summary."
            )
        else:
            final_summary = summaries[0] if summaries else "No content found to summarize."

        # Append path info to summary for reference
        path_summary = f"\n\n---\n**Document Path Info:**\n"
        path_summary += f"- **GR No:** {path_info['gr_no']}\n"
        path_summary += f"- **Branch:** {path_info['branch']}\n"
        path_summary += f"- **Date:** {path_info['date']}\n"
        path_summary += f"- **Source Page:** {path_info['source_page']}\n"
        path_summary += f"- **PDF URL:** {pdf_url}\n"
        
        return final_summary + path_summary

    def answer_question_from_pdf(self, pdf_url: str, question: str) -> str:
        """Answer a question based on PDF content"""
        if self.demo_mode:
            return "Demo mode: Question answering disabled"
        text = self.process_pdf_from_url(pdf_url)

        # Use Gemini to answer
        prompt = f"Given the text from the PDF, generate an answer to the user query.\n\nText: {text}\n\nQuestion: {question}"
        model = self.gemini_client.GenerativeModel(Config.GEMINI_MODEL)
        response = model.generate_content(prompt)
        
        if hasattr(response, 'text'):
            return response.text
        elif hasattr(response, 'candidates'):
            return response.candidates[0].content.parts[0].text
        
        return "Unable to generate answer"

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))

