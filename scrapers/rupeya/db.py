"""Supabase admin client wrapper.

The scrapers run as a trusted service and use the service-role key,
which bypasses Row-Level Security. This is the *only* context outside
the Next.js server-side admin paths where that key should ever live.
"""

from __future__ import annotations

from functools import lru_cache

from supabase import create_client, Client

from . import config


@lru_cache(maxsize=1)
def get_client() -> Client:
    """Return a memoized Supabase admin client."""
    return create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)
