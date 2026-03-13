import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from supabase import create_client


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

gemini = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])


def search(query: str, limit: int = 5):
    resp = gemini.models.embed_content(model="gemini-embedding-001", contents=query)
    query_embedding = resp.embeddings[0].values

    result = supabase.rpc(
        "match_products",
        {
            "query_embedding": query_embedding,
            "match_count": limit,
        },
    ).execute()

    print(f'\nResults for: "{query}"\n' + "=" * 60)
    for i, row in enumerate(result.data, 1):
        price = f"₹{row['price']:,.0f}" if row.get("price") else "Price on Request"
        print(f"\n{i}. {row['name']}")
        print(f"   Category:   {row.get('category', '-')}")
        print(f"   Collection: {row.get('collection', '-')}")
        print(f"   Material:   {row.get('material', '-')}")
        print(f"   Price:      {price}")
        print(f"   Similarity: {1 - row.get('distance', 0):.3f}")


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Subtle everyday diamond piece"
    search(query)

