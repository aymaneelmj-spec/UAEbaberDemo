#!/usr/bin/env python3
"""
split_leads_to_site_data.py

Converts a scraped leads array (name, phone, city, country, niche, address,
images_count, demo_url, whatsapp) into one per-business data.json matching
the barbershop-demo site's expected schema, ready to drop into:

    data/<id>/data.json

Usage:
    python3 split_leads_to_site_data.py leads.json output_data

Then upload the contents of output_data/ into your site's data/ folder,
e.g. output_data/1/data.json -> data/1/data.json
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Map scraper's free-text "country" field -> currency code used by the site.
# Extend this as you scrape more countries.
COUNTRY_TO_CURRENCY = {
    "united arab emirates": "AED",
    "saudi arabia": "SAR",
    "qatar": "QAR",
    "bahrain": "BHD",
    "kuwait": "KWD",
    "oman": "OMR",
    "morocco": "MAD",
    "algeria": "DZD",
    "tunisia": "TND",
    "egypt": "EGP",
}
DEFAULT_CURRENCY = "SAR"  # fallback if country isn't recognized

DEFAULT_HOURS = "يومياً 10:00 ص – 12:00 ص"


def extract_gallery(demo_url: str):
    """Pull the comma-separated image URLs out of demo_url's ?images= param."""
    if not demo_url:
        return []
    try:
        query = parse_qs(urlparse(demo_url).query)
        images_raw = query.get("images", [""])[0]
        return [u for u in images_raw.split(",") if u.strip()]
    except Exception:
        return []


def clean_phone(phone: str) -> str:
    return re.sub(r"[^0-9]", "", str(phone or ""))


def convert_entry(entry: dict) -> dict:
    phone_digits = clean_phone(entry.get("phone"))
    country_key = str(entry.get("country") or "").strip().lower()
    currency = COUNTRY_TO_CURRENCY.get(country_key, DEFAULT_CURRENCY)

    return {
        "businessName": entry.get("name") or "",
        "currency": currency,
        "whatsapp": phone_digits,
        "phoneDisplay": f"+{phone_digits}" if phone_digits else "",
        "address": entry.get("address") or "",
        "hours": DEFAULT_HOURS,
        "gallery": extract_gallery(entry.get("demo_url", "")),
        # These three are left out on purpose: the site already falls back
        # to sensible defaults (@diwan_barber / instagram.com / tiktok.com)
        # when they're missing. Fill them in per-client if you have real
        # social links for that business.
        # "instagram": "@handle",
        # "instagramUrl": "https://instagram.com/handle",
        # "tiktokUrl": "https://tiktok.com/@handle",
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 split_leads_to_site_data.py <leads.json> <output_dir>")
        sys.exit(1)

    leads_path = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    leads = json.loads(leads_path.read_text(encoding="utf-8"))
    if not isinstance(leads, list):
        print("Expected a JSON array of leads at the top level.")
        sys.exit(1)

    index_map = {}  # id -> business name, for your own reference
    for i, entry in enumerate(leads, start=1):
        site_data = convert_entry(entry)
        business_dir = out_dir / str(i)
        business_dir.mkdir(parents=True, exist_ok=True)
        (business_dir / "data.json").write_text(
            json.dumps(site_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        index_map[i] = entry.get("name", "")
        print(f"  id={i:<4} -> {entry.get('name')}")

    (out_dir / "_index_map.json").write_text(
        json.dumps(index_map, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nDone. {len(leads)} businesses written to {out_dir}/<id>/data.json")


if __name__ == "__main__":
    main()
