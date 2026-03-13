import json
import time
from pathlib import Path
from typing import List, Dict, Any

from dotenv import load_dotenv
import os

from google import genai
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
        raise RuntimeError("SUPABASE_URL and SUPABASE_SECRET_KEY must be set in the environment/.env")
    return create_client(url, key)


def load_products() -> List[Dict[str, Any]]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data file not found: {DATA_PATH}")
    with DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_embedding_text(product: Dict[str, Any]) -> str:
    """
    Build a rich text representation of a product for embeddings.
    """
    parts = []
    name = product.get("name") or ""
    parts.append(name)

    category = product.get("category")
    if category:
        parts.append(f"Category: {category}")

    collection = product.get("collection")
    if collection:
        parts.append(f"Collection: {collection}")

    material = product.get("material") or product.get("metal_colour")
    if material:
        parts.append(f"Material: {material}")

    purity = product.get("purity")
    if purity:
        parts.append(f"Purity: {purity}")

    gem1 = product.get("gem_stone_1")
    if gem1:
        parts.append(f"Gem Stone 1: {gem1}")

    gem2 = product.get("gem_stone_2")
    if gem2:
        parts.append(f"Gem Stone 2: {gem2}")

    price = product.get("price")
    currency = product.get("currency") or "INR"
    if price:
        parts.append(f"Price: {price} {currency}")

    carat = product.get("diamond_caratage")
    if carat:
        parts.append(f"Diamond Caratage: {carat}")

    clarity = product.get("diamond_clarity")
    if clarity:
        parts.append(f"Diamond Clarity: {clarity}")

    colour = product.get("diamond_colour")
    if colour:
        parts.append(f"Diamond Colour: {colour}")

    stock = product.get("stock_status")
    if stock:
        parts.append(f"Stock Status: {stock}")

    details = product.get("product_details")
    if details:
        parts.append(f"Product Type: {details}")

    return ". ".join(parts)


def generate_embeddings(
    client: genai.Client,
    products: List[Dict[str, Any]],
    model: str = "gemini-embedding-001",
) -> List[List[float]]:
    """
    Generate embeddings for all products using Gemini (google-genai).
    """
    texts = [build_embedding_text(p) for p in products]
    embeddings: List[List[float]] = []

    batch_size = 20
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        print(f"Embedding batch {i}–{i + len(batch) - 1} ...", flush=True)
        resp = client.models.embed_content(model=model, contents=batch)
        for emb in resp.embeddings:
            embeddings.append(emb.values)
        time.sleep(15)

    if len(embeddings) != len(products):
        raise RuntimeError("Embedding count does not match products count")

    return embeddings


def upsert_products_with_embeddings(
    client: Client,
    products: List[Dict[str, Any]],
    embeddings: List[List[float]],
) -> None:
    rows: List[Dict[str, Any]] = []
    for product, emb in zip(products, embeddings):
        price = product.get("price")
        if price == "" or price is None:
            price = None

        row = {
            "pid": product.get("pid"),
            "name": product.get("name"),
            "price": price,
            "currency": product.get("currency") or None,
            "category": product.get("category") or None,
            "material": product.get("material") or None,
            "stock_status": product.get("stock_status") or None,
            "link": product.get("link") or None,
            "purity": product.get("purity") or None,
            "gem_stone_1": product.get("gem_stone_1") or None,
            "gem_stone_2": product.get("gem_stone_2") or None,
            "collection": product.get("collection") or None,
            "product_details": product.get("product_details") or None,
            "metal_colour": product.get("metal_colour") or None,
            "diamond_caratage": product.get("diamond_caratage") or None,
            "diamond_clarity": product.get("diamond_clarity") or None,
            "diamond_colour": product.get("diamond_colour") or None,
            "embedding": emb,
        }
        rows.append(row)

    table = client.table("products")
    batch_size = 100
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        print(f"Upserting rows {i}–{i + len(batch) - 1} ...", flush=True)
        table.upsert(batch, on_conflict="pid").execute()


def main() -> None:
    load_env()
    products = load_products()
    print(f"Loaded {len(products)} products from {DATA_PATH}")

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY must be set in the environment/.env")

    gemini_client = genai.Client(api_key=api_key)
    supabase_client = get_supabase_client()

    embeddings = generate_embeddings(gemini_client, products)
    print("Embeddings generated.")

    upsert_products_with_embeddings(supabase_client, products, embeddings)
    print("Upsert completed.")


if __name__ == "__main__":
    main()

