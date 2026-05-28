import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL") or ""
supabase_anon_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY") or ""

is_supabase_configured = False
supabase: Client = None

if supabase_url and supabase_anon_key and "your-supabase-project" not in supabase_url:
    try:
        supabase = create_client(supabase_url, supabase_anon_key)
        is_supabase_configured = True
    except Exception as e:
        print(f"[WARNING] Supabase client failed to initialize: {e}")
        is_supabase_configured = False
        supabase = None

def get_supabase_client(token: str = None) -> Client:
    if not is_supabase_configured or not supabase:
        return None
    if not token or token.startswith("mock-session-"):
        return supabase
    try:
        # Create a new client instance
        client = create_client(supabase_url, supabase_anon_key)
        # Directly set the authorization header on the PostgREST session
        client.postgrest.session.headers["Authorization"] = f"Bearer {token}"
        return client
    except Exception as e:
        print(f"[WARNING] Failed to create request-scoped client: {e}")
        return supabase
