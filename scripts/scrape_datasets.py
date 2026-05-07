import argparse
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://dasatama.magetan.go.id"
API_URL = BASE_URL + "/api/detail/{id}"
PAGE_URL = BASE_URL + "/detail/{id}"

DATASETS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "datasets")
)
INDEX_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "datasets_index.json")
)
DIRECTORIES_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "directories.json")
)
CATEGORIES_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "categories.json")
)

REQUEST_TIMEOUT = 30
RETRY_WAITS = [2, 5, 10]
USER_AGENT = "Mozilla/5.0 (compatible; opendata-magetan-scraper/1.0)"

API_RESERVED_KEYS = {"opdTitle", "opdId", "dataId"}

METADATA_MAP = {
    "Konsep":          ("concept",        "string"),
    "Klasifikasi":     ("classification", "string"),
    "Ukuran":          ("measure",        "string"),
    "Satuan":          ("unit",           "string"),
    "Periode":         ("period",         "string"),
    "Dataset Dibuat":  ("created_at",     "datetime"),
    "Dataset Diubah":  ("updated_at",     "datetime"),
}


def build_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def fetch(session: requests.Session, url: str) -> requests.Response:
    last_exc = None
    for i, wait in enumerate(RETRY_WAITS, start=1):
        try:
            resp = session.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            last_exc = exc
            logging.warning("Attempt %d failed (%s): %s", i, url, exc)
            if i < len(RETRY_WAITS):
                time.sleep(wait)
    raise last_exc


def load_sub_items(directories_path: str) -> list[dict]:
    with open(directories_path, encoding="utf-8") as f:
        data = json.load(f)
    items = []
    for dept in data["items"]:
        for sub in dept["sub_items"]:
            items.append({
                "id": sub["id"],
                "title": sub["title"],
                "item_title": dept["title"],
                "url": sub["url"],
            })
    return items


def build_category_lookup(categories_path: str) -> dict[str, str]:
    with open(categories_path, encoding="utf-8") as f:
        data = json.load(f)
    lookup = {}
    for cat in data["categories"]:
        for sub in cat["sub_items"]:
            lookup[sub["id"]] = cat["name"]
    return lookup


def infer_type(raw_values: list[str]) -> str:
    cleaned = [v.strip().replace(",", "") for v in raw_values if v.strip()]
    if not cleaned:
        return "string"
    try:
        for v in cleaned:
            int(v)
        return "integer"
    except ValueError:
        pass
    try:
        for v in cleaned:
            float(v)
        return "number"
    except ValueError:
        pass
    return "string"


def cast(value: str, typ: str):
    v = value.strip().replace(",", "")
    if not v:
        return None
    if typ == "integer":
        try:
            return int(v)
        except ValueError:
            return v
    if typ == "number":
        try:
            return float(v)
        except ValueError:
            return v
    return value.strip()


def parse_api_data(api_json: dict) -> tuple[str, list[dict]]:
    data_key = next(k for k in api_json if k not in API_RESERVED_KEYS)
    rows = api_json[data_key]
    return data_key, rows


def build_timeseries(rows: list[dict]) -> list[dict]:
    if not rows:
        return []

    rows_sorted = sorted(rows, key=lambda r: int(r.get("year", 0)))
    columns = [k for k in rows_sorted[0].keys() if k != "year"]

    series = []
    for col in columns:
        raw_vals = [str(r.get(col, "")) for r in rows_sorted]
        typ = infer_type(raw_vals)
        values = [
            {"year": int(r["year"]), "value": cast(str(r.get(col, "")), typ)}
            for r in rows_sorted
        ]
        yrs = [v["year"] for v in values]
        series.append({
            "name": col,
            "type": typ,
            "years": {
                "total": len(values),
                "min": min(yrs) if yrs else None,
                "max": max(yrs) if yrs else None,
            },
            "values": values,
        })

    return series


def parse_metadata(html: str) -> dict:
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    tables = soup.find_all("table")
    if len(tables) < 2:
        return {}

    meta_table = tables[1]
    result = {}
    for row in meta_table.find_all("tr"):
        cells = row.find_all(["td", "th"])
        if len(cells) < 3:
            continue
        label = cells[1].get_text(strip=True)
        value = cells[2].get_text(strip=True)
        if label in METADATA_MAP:
            key, _typ = METADATA_MAP[label]
            result[key] = value

    return result


def get_opd_id(api_json: dict) -> int | None:
    opd_id = api_json.get("opdId")
    if opd_id is None:
        return None
    try:
        return int(opd_id)
    except (ValueError, TypeError):
        return opd_id


def save_json(data: dict, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def scrape_dataset(
    session: requests.Session,
    item: dict,
    category: str,
    scraped_at: str,
) -> dict:
    dataset_id = item["id"]

    api_url = API_URL.format(id=dataset_id)
    page_url = PAGE_URL.format(id=dataset_id)

    api_resp = fetch(session, api_url)
    api_json = api_resp.json()

    _data_key, rows = parse_api_data(api_json)
    timeseries = build_timeseries(rows)

    page_resp = fetch(session, page_url)
    page_resp.encoding = page_resp.apparent_encoding
    metadata = parse_metadata(page_resp.text)

    opd_id = get_opd_id(api_json)

    result = {
        "id": dataset_id,
        "title": item["title"],
        "item_title": item["item_title"],
        "opd_id": opd_id,
        "category": category,
        "url": item["url"],
        "scraped_at": scraped_at,
        "metadata": metadata,
        "total_data": len(timeseries),
        "data": timeseries,
    }
    return result


def build_index(
    all_items: list[dict],
    results: dict[str, dict],
    indexed_at: str,
) -> dict:
    success = 0
    failed = 0
    datasets = []

    for item in all_items:
        dataset_id = item["id"]
        status = results.get(dataset_id, {})

        if status.get("status") == "failed":
            failed += 1
            datasets.append({
                "id": dataset_id,
                "title": item["title"],
                "item_title": item["item_title"],
                "status": "failed",
                "error": status.get("error", "unknown"),
            })
            continue

        path = os.path.join(DATASETS_DIR, f"{dataset_id}.json")
        if not os.path.exists(path):
            failed += 1
            datasets.append({
                "id": dataset_id,
                "title": item["title"],
                "item_title": item["item_title"],
                "status": "failed",
                "error": "file not found",
            })
            continue

        with open(path, encoding="utf-8") as f:
            d = json.load(f)

        success += 1
        datasets.append({
            "id": d["id"],
            "title": d["title"],
            "item_title": d["item_title"],
            "opd_id": d.get("opd_id"),
            "category": d.get("category"),
            "series": [{"name": s["name"], "type": s["type"], "years": s.get("years")} for s in d.get("data", [])],
            "scraped_at": d.get("scraped_at"),
            "status": "success",
        })

    return {
        "total": len(all_items),
        "success": success,
        "failed": failed,
        "indexed_at": indexed_at,
        "datasets": datasets,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape datasets from dasatama.magetan.go.id")
    parser.add_argument("--delay", type=float, default=0.3, help="Delay between requests in seconds")
    parser.add_argument("--force", action="store_true", help="Re-scrape already downloaded datasets")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    for path, name in [(DIRECTORIES_PATH, "directories.json"), (CATEGORIES_PATH, "categories.json")]:
        if not os.path.exists(path):
            logging.error("Required input not found: %s", path)
            logging.error("Run extract_menu.py and categorize.py first.")
            sys.exit(1)

    all_items = load_sub_items(DIRECTORIES_PATH)
    category_lookup = build_category_lookup(CATEGORIES_PATH)
    total = len(all_items)

    logging.info("Loaded %d datasets to scrape", total)
    os.makedirs(DATASETS_DIR, exist_ok=True)

    session = build_session()
    results: dict[str, dict] = {}
    success_count = 0
    skip_count = 0
    fail_count = 0

    for i, item in enumerate(all_items, start=1):
        dataset_id = item["id"]
        out_path = os.path.join(DATASETS_DIR, f"{dataset_id}.json")

        if os.path.exists(out_path) and not args.force:
            logging.info("[%d/%d] [SKIP] id=%s %s", i, total, dataset_id, item["title"])
            skip_count += 1
            continue

        scraped_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        category = category_lookup.get(dataset_id, "")

        try:
            data = scrape_dataset(session, item, category, scraped_at)
            save_json(data, out_path)
            results[dataset_id] = {"status": "success"}
            success_count += 1
            logging.info("[%d/%d] id=%s %s", i, total, dataset_id, item["title"])
        except Exception as exc:
            err = str(exc)
            results[dataset_id] = {"status": "failed", "error": err}
            fail_count += 1
            logging.warning("[%d/%d] [FAIL] id=%s %s — %s", i, total, dataset_id, item["title"], err)

        if args.delay > 0:
            time.sleep(args.delay)

    logging.info("Done: %d success, %d skipped, %d failed", success_count, skip_count, fail_count)

    indexed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    index = build_index(all_items, results, indexed_at)
    save_json(index, INDEX_PATH)
    logging.info("Index saved to %s", INDEX_PATH)


if __name__ == "__main__":
    main()
