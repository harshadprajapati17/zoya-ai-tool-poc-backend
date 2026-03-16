import json
from pathlib import Path

from scraper import fetch_html, parse_product_media


ROOT = Path(__file__).resolve().parent


def main() -> None:
    json_path = ROOT / "zoya_products.json"
    with open(json_path, "r", encoding="utf-8") as f:
        products = json.load(f)

    # take first 2 products that have a link
    selected = [p for p in products if p.get("link")][:2]

    for idx, product in enumerate(selected, start=1):
        pid = product.get("pid", "")
        link = product.get("link")
        print(f"[media] ({idx}/2) {pid} -> {link}")

        if not link:
            print("  - no link, skipping")
            continue

        page_html = fetch_html(link)
        if not page_html:
            print("  - failed to fetch HTML")
            continue

        media = parse_product_media(page_html)
        thumbnails = media.get("product_thumbnails") or []
        images = media.get("product_images") or []

        print(f"  - thumbnails: {len(thumbnails)}")
        if thumbnails:
            print(f"    first thumbnail: {thumbnails[0]}")

        print(f"  - images: {len(images)}")
        if images:
            print(f"    first image: {images[0]}")


if __name__ == "__main__":
    main()

