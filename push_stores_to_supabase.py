import json
import os
from pathlib import Path

import requests

try:
    # Optional: load environment variables from .env if python-dotenv is installed
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None


ROOT = Path(__file__).resolve().parent


def load_env():
    """
    Ensure SUPABASE_URL and SUPABASE_SECRET_KEY are available.
    If python-dotenv is installed, load from .env in the backend folder.
    """
    if load_dotenv is not None:
        env_path = ROOT / ".env"
        if env_path.exists():
            load_dotenv(env_path)

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_secret = os.getenv("SUPABASE_SECRET_KEY")

    if not supabase_url or not supabase_secret:
        raise RuntimeError(
            "SUPABASE_URL or SUPABASE_SECRET_KEY is missing. "
            "Set them in environment or backend/.env."
        )

    return supabase_url, supabase_secret


def push_stores(table_name: str = "zoya_stores") -> None:
    """
    Read stores from zoya_stores.json and insert/upsert into Supabase.

    - Assumes a table named `zoya_stores` (by default) with columns:
      store_name, store_type, address, email, phone, city, state, pincode.
    - Uses Supabase REST API with service role key from SUPABASE_SECRET_KEY.
    """
    supabase_url, supabase_secret = load_env()

    json_path = ROOT / "zoya_stores.json"
    if not json_path.exists():
        raise FileNotFoundError(f"{json_path} not found. Generate it first.")

    with json_path.open(encoding="utf-8") as f:
        stores = json.load(f)

    if not isinstance(stores, list):
        raise ValueError("zoya_stores.json must contain a list of store objects.")

    # Normalize fields for Supabase:
    # - Strip JSON-only fields that don't exist as DB columns (like isInternational)
    #   to avoid PostgREST errors about unknown columns.
    normalized_stores = []
    for s in stores:
        s = dict(s)  # shallow copy
        # Remove JSON-only key that Supabase doesn't know about
        s.pop("isInternational", None)
        normalized_stores.append(s)

    url = f"{supabase_url}/rest/v1/{table_name}"
    headers = {
        "apikey": supabase_secret,
        "Authorization": f"Bearer {supabase_secret}",
        "Content-Type": "application/json",
        # If there's a unique constraint (e.g. on email or store_name) this will upsert
        "Prefer": "resolution=merge-duplicates",
    }

    resp = requests.post(url, headers=headers, json=normalized_stores, timeout=30)
    print("Status:", resp.status_code)
    try:
        print("Response:", resp.json())
    except Exception:
        print("Response text:", resp.text)


if __name__ == "__main__":
    push_stores()

