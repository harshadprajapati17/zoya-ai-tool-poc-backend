import json
from pathlib import Path
import os

from dotenv import load_dotenv
from supabase import create_client, Client


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "zoya_products.json"


def load_env() -> None:
    env_path = ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)


def get_supabase_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SECRET_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SECRET_KEY must be set in .env")
    return create_client(url, key)


def load_products() -> list[dict]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data file not found: {DATA_PATH}")
    with DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def update_images_only() -> None:
    """
    Update product_thumbnails and product_images in Supabase
    without touching embeddings or other fields.
    """
    load_env()
    client = get_supabase_client()
    table = client.table("products")
    products = load_products()
    total = len(products)
    print(f"Loaded {total} products from {DATA_PATH}")

    for idx, product in enumerate(products, start=1):
        pid = product.get("pid")
        if not pid:
            continue

        print(f"Updating images for pid={pid} ({idx}/{total})...", flush=True)
        table.update(
            {
                "product_thumbnails": product.get("product_thumbnails") or None,
                "product_images": product.get("product_images") or None,
            }
        ).eq("pid", pid).execute()

    print("Image fields update completed.")


if __name__ == "__main__":
    update_images_only()

