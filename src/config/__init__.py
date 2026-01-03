"""
Configuration module for FinBot
Handles environment variables and application settings
"""

import os
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""


    # Gemini Configuration
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

    # Supabase Configuration
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

    # Application Settings
    EMBEDDING_MODEL = "text-embedding-3-small"
    CHAT_MODEL = "gpt-4o-mini"
    GEMINI_MODEL = "gemini-2.5-flash"
    MAX_TOKENS = 100000
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50

    # Scraping Settings
    SCRAPE_BASE_URL = "https://financedepartment.gujarat.gov.in/gr.html"
    CHROME_HEADLESS = True
    BATCH_SIZE = 25

    @classmethod
    def validate(cls):
        """Validate required environment variables"""
        required_vars = [
            ("GEMINI_API_KEY", cls.GEMINI_API_KEY),
            ("SUPABASE_URL", cls.SUPABASE_URL),
            ("SUPABASE_KEY", cls.SUPABASE_KEY)
        ]

        missing = []
        for var_name, var_value in required_vars:
            if not var_value or var_value == f"your_{var_name.lower()}_here":
                missing.append(var_name)

        if missing:
            # Don't raise error, just warn and allow demo mode
            import warnings
            warnings.warn(f"Missing environment variables: {', '.join(missing)}. Running in demo mode with limited functionality.")
            return False

        return True

class Clients:
    """Singleton clients for external services"""

    _supabase = None
    _openai = None
    _gemini = None

    @classmethod
    def get_supabase(cls):
        """Get Supabase client instance"""
        if cls._supabase is None:
            if not Config.validate():
                return None
            cls._supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        return cls._supabase

    @classmethod
    def get_openai(cls):
        """Get OpenAI client instance"""
        if cls._openai is None:
            if not Config.validate():
                return None
            cls._openai = OpenAI(api_key=Config.OPENAI_API_KEY)
        return cls._openai

    @classmethod
    def get_gemini(cls):
        """Get Gemini client instance"""
        if cls._gemini is None:
            if not Config.validate():
                return None
            if not Config.GEMINI_API_KEY:
                return None
            # Use the older google.generativeai package for better compatibility
            try:
                import google.generativeai as genai
                genai.configure(api_key=Config.GEMINI_API_KEY)
                cls._gemini = genai
            except ImportError:
                print("Failed to import google.generativeai")
                cls._gemini = None
        return cls._gemini
