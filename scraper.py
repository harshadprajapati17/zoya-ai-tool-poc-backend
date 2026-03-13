import json
import time
import csv
import html
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent

BASE_URL = (
    "https://www.zoya.in/on/demandware.store/Sites-Zoya-Site/en_IN/"
    "Search-UpdateGrid?cgid=zo-collections&start={start}&sz=24"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_html(url: str) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        print(f"  [error] Failed to fetch URL={url}: {e}")
        return None


def fetch_listing_page(start: int) -> str | None:
    url = BASE_URL.format(start=start)
    return fetch_html(url)


def parse_products(page_html: str) -> list[dict]:
    soup = BeautifulSoup(page_html, "html.parser")
    products = []

    for tile in soup.select("div.product[data-gtmdata]"):
        gtm_raw = tile.get("data-gtmdata", "{}")
        gtm = json.loads(html.unescape(gtm_raw))

        link_tag = tile.select_one("div.image-container a[href]")
        link = link_tag["href"] if link_tag else None

        products.append({
            "pid": gtm.get("item_id", ""),
            "name": gtm.get("item_name", ""),
            "price": gtm.get("price", ""),
            "currency": gtm.get("currency", ""),
            "category": gtm.get("item_category2", ""),
            "material": gtm.get("item_category4", ""),
            "stock_status": gtm.get("stockStatus", ""),
            "link": link,
        })

    return products


def parse_product_details(page_html: str) -> dict:
    """
    Parse the product details block on an individual product page.

    The DOM has: div.details (heading "Product Details") followed by a sibling
    div.collapse that holds div.card-body > two columns of labels and values.
    We locate the correct collapse block, then zip labels with values.
    """
    soup = BeautifulSoup(page_html, "html.parser")

    # Find the "Product Details" heading, then grab the next sibling collapse div
    details_heading = None
    for d in soup.select("div.details"):
        if "Product Details" in d.get_text():
            details_heading = d
            break

    if not details_heading:
        return {}

    collapse_div = details_heading.find_next_sibling("div", class_="collapse")
    if not collapse_div:
        return {}

    labels = [el.get_text(strip=True) for el in collapse_div.select("div.product-info")]
    values = [el.get_text(strip=True) for el in collapse_div.select("div.product-info-details")]

    label_key_map = {
        "Purity": "purity",
        "Gem Stone 1": "gem_stone_1",
        "Gem Stone 2": "gem_stone_2",
        "Collection": "collection",
        "Product Details": "product_details",
        "Product details": "product_details",
        "Metal Colour": "metal_colour",
        "Metal Color": "metal_colour",
        "Diamond Caratage": "diamond_caratage",
        "Diamond Clarity": "diamond_clarity",
        "Diamond Colour": "diamond_colour",
        "Diamond Color": "diamond_colour",
    }

    details: dict[str, str] = {}
    for label, value in zip(labels, values):
        clean_label = label.rstrip(":").strip()
        key = label_key_map.get(clean_label)
        if key and value:
            details[key] = value

    return details


def scrape_all() -> list[dict]:
    all_products = []
    start = 0
    page_num = 1

    while True:
        print(f"Page {page_num} (start={start}) ...", end=" ", flush=True)
        page_html = fetch_listing_page(start)

        if not page_html:
            break

        products = parse_products(page_html)
        if not products:
            print("0 products — reached the end.")
            break

        print(f"{len(products)} products found.")
        all_products.extend(products)

        if len(products) < 24:
            print("Last page (fewer than 24 products).")
            break

        start += 24
        page_num += 1
        time.sleep(1)

    return all_products


def save_csv(products: list[dict], path: str = str(ROOT / "zoya_products.csv")):
    if not products:
        print("No products to save.")
        return

    fields = [
        "pid",
        "name",
        "price",
        "currency",
        "category",
        "material",
        "stock_status",
        "link",
        "purity",
        "gem_stone_1",
        "gem_stone_2",
        "collection",
        "product_details",
        "metal_colour",
        "diamond_caratage",
        "diamond_clarity",
        "diamond_colour",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(products)
    print(f"Saved {len(products)} products to {path}")


def save_json(products: list[dict], path: str = str(ROOT / "zoya_products.json")):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(products)} products to {path}")


if __name__ == "__main__":
    print("=" * 60)
    print("Zoya Product Link Scraper")
    print("=" * 60)

    products = scrape_all()

    print(f"\nTotal products scraped from listing pages: {len(products)}")
    unique_links = [p["link"] for p in products if p.get("link")]
    unique_links = list(dict.fromkeys(unique_links))  # preserve order, ensure uniqueness
    print(f"Unique product links found:  {len(unique_links)}")

    # Enrich each product with details from its own page
    total = len(products)
    for idx, product in enumerate(products, start=1):
        link = product.get("link")
        if not link:
            continue

        print(f"[details] ({idx}/{total}) {product.get('pid', '')} -> {link}", end=" ", flush=True)
        page_html = fetch_html(link)
        if not page_html:
            print("- failed to fetch")
            continue

        details = parse_product_details(page_html)
        product.update(details)
        print(f"- ok ({len(details)} fields)")
        time.sleep(0.5)

    save_csv(products)
    save_json(products)

    print("\nDone!")

