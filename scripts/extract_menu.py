import json
import logging
import os
import re
import sys
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://dasatama.magetan.go.id"
OUTPUT_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "directories.json")
)
REQUEST_TIMEOUT = 30
RETRY_WAITS = [2, 5, 10]
USER_AGENT = "Mozilla/5.0 (compatible; opendata-magetan-scraper/1.0)"

SIDEBAR_SELECTORS = [
    "nav.sidebar",
    "aside.sidebar",
    "div.sidebar",
    "nav#sidebar",
    "div#sidebar",
    "div.left-sidebar",
    "nav.nav-sidebar",
    ".side-nav",
    ".sidenav",
]


def fetch_page(url: str) -> str:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    last_exc = None
    for i, wait in enumerate(RETRY_WAITS, start=1):
        try:
            resp = session.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding
            return resp.text
        except requests.RequestException as exc:
            last_exc = exc
            logging.warning("Attempt %d failed: %s", i, exc)
            if i < len(RETRY_WAITS):
                time.sleep(wait)
    raise last_exc


def find_sidebar_ul(soup: BeautifulSoup):
    # Strategy 1: named CSS selectors
    for selector in SIDEBAR_SELECTORS:
        container = soup.select_one(selector)
        if container and container.find("a", href="#"):
            logging.info("Sidebar found via selector: %s", selector)
            return container

    # Strategy 2: structural — outermost ul with >= 2 parent items (a[href="#"] + nested ul)
    for ul in soup.find_all("ul"):
        parent_items = [
            li for li in ul.find_all("li", recursive=False)
            if li.find("a", href="#") and li.find("ul")
        ]
        if len(parent_items) >= 2:
            logging.info("Sidebar found via structural inference (%d parent items)", len(parent_items))
            return ul

    return None


def is_dashboard(href: str) -> bool:
    if not href or href == "#":
        return False
    normalized = href.rstrip("/")
    base = BASE_URL.rstrip("/")
    return normalized == base or href == "/"


def normalize_url(href: str) -> str | None:
    if not href or href == "#":
        return None
    if href.startswith("http://") or href.startswith("https://"):
        return href
    return urljoin(BASE_URL, href)


def parse_menu(sidebar) -> list[dict]:
    results = []

    # Sidebar may be a container div — unwrap to the inner <ul>
    if sidebar.name != "ul":
        top_ul = sidebar.find("ul")
        if not top_ul:
            return []
        sidebar = top_ul

    for li in sidebar.find_all("li", recursive=False):
        anchor = li.find("a", recursive=False)
        if not anchor:
            continue

        href = anchor.get("href", "").strip()
        title = anchor.get_text(strip=True)

        if is_dashboard(href) or not title:
            continue

        # Each sub-item lives in its own <ul class="nav nav-treeview"> —
        # collect all of them rather than just the first
        sub_uls = li.find_all("ul")
        if not sub_uls:
            continue

        sub_items = []
        for sub_ul in sub_uls:
            for sub_li in sub_ul.find_all("li", recursive=False):
                sub_a = sub_li.find("a")
                if not sub_a:
                    continue
                sub_href = sub_a.get("href", "").strip()
                sub_title = sub_a.get_text(strip=True)
                sub_url = normalize_url(sub_href)
                if sub_url and "/detail/" in sub_url:
                    m = re.search(r"/detail/(\d+)", sub_url)
                    sub_id = m.group(1) if m else ""
                    sub_items.append({"id": sub_id, "title": sub_title, "url": sub_url})

        if sub_items:
            results.append({
                "title": title,
                "total_sub_items": len(sub_items),
                "sub_items": sub_items,
            })

    return results


def save_json(items: list[dict], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {
        "total_items": len(items),
        "items": items,
    }
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    logging.info("Fetching %s", BASE_URL)
    html = fetch_page(BASE_URL)

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    sidebar = find_sidebar_ul(soup)
    if not sidebar:
        logging.error("Could not locate sidebar navigation. The page structure may have changed.")
        sys.exit(1)

    data = parse_menu(sidebar)
    total_sub = sum(e["total_sub_items"] for e in data)
    logging.info("Found %d departments, %d sub-items total", len(data), total_sub)

    save_json(data, OUTPUT_PATH)
    logging.info("Saved to %s", OUTPUT_PATH)


if __name__ == "__main__":
    main()
