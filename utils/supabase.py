"""
Supabase client initialization
Mirrors the dual-client pattern from DaanaRx-Backend/src/utils/supabase.ts
"""
import logging
from supabase import create_client, Client
from config import settings

logger = logging.getLogger(__name__)

_supabase_server: Client | None = None
_supabase_auth: Client | None = None


def get_supabase_server() -> Client:
    """Get server-side Supabase client with service role key (for admin DB operations)"""
    global _supabase_server
    if _supabase_server is None:
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set"
            )
        _supabase_server = create_client(
            settings.supabase_url, settings.supabase_service_role_key
        )
        logger.info("Supabase server client initialized")
    return _supabase_server


def get_supabase_auth() -> Client:
    """Get Supabase client with anon key (for signInWithPassword)"""
    global _supabase_auth
    if _supabase_auth is None:
        if not settings.supabase_url or not settings.supabase_anon_key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
        _supabase_auth = create_client(
            settings.supabase_url, settings.supabase_anon_key
        )
        logger.info("Supabase auth client initialized")
    return _supabase_auth
