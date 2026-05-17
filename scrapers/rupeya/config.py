"""Environment loading + global settings for the scraper package.

Reads .env on import; subsequent imports get the cached values.
Fails fast with a clear error if required env vars are missing.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the scrapers/ folder regardless of where the script is run.
_HERE = Path(__file__).resolve().parent.parent  # scrapers/
load_dotenv(_HERE / ".env")


def _require(name: str) -> str:
    """Return env var or raise a clear error."""
    val = os.environ.get(name)
    if not val:
        raise RuntimeError(
            f"[rupeya.config] Missing env var: {name}. "
            f"Check scrapers/.env (copy from .env.example if needed)."
        )
    return val


def _optional_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


# --- Required ---
SUPABASE_URL: str = _require("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY: str = _require("SUPABASE_SERVICE_ROLE_KEY")

# --- Optional knobs ---
SCRAPE_DELAY_SECONDS: float = float(os.environ.get("SCRAPE_DELAY_SECONDS", "1"))
SCRAPE_LIMIT: int = _optional_int("SCRAPE_LIMIT", 0)  # 0 = no limit
LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO").upper()


def setup_logging() -> logging.Logger:
    """Configure root logger and return a named one for scripts."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger("rupeya")
