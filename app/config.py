import os
from dotenv import load_dotenv

load_dotenv()


GOOGLE_SHEETS_API_KEY = os.getenv("GOOGLE_SHEETS_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SYNC_API_KEY = os.getenv("SYNC_API_KEY")
MAL_CLIENT_ID = os.getenv("MAL_CLIENT_ID")
