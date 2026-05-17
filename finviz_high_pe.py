"""
Extract all Finviz tickers with P/E ratio > 100 from the screener.

Usage:
    python finviz_high_pe.py                      # print tickers to stdout
    python finviz_high_pe.py --output tickers.csv # save to CSV
    python finviz_high_pe.py --proxy http://host:port

Note: Finviz blocks datacenter/cloud IPs. Run from a residential connection
or pass --proxy with a residential proxy.
"""

import argparse
import csv
import sys
import time

import requests
from bs4 import BeautifulSoup

SCREENER_URL = "https://finviz.com/screener.ashx"
PAGE_SIZE = 20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Referer": "https://finviz.com/",
}


def build_session(proxy: str | None = None) -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    # Warm up with a homepage visit to pick up Finviz session cookies
    session.get("https://finviz.com/", timeout=15)
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}
    return session


def fetch_page(row_offset: int, session: requests.Session) -> BeautifulSoup:
    params = {
        "v": "111",        # overview view (includes P/E column)
        "f": "fa_pe_o100", # filter: P/E over 100
        "r": row_offset,   # 1-based row offset for pagination
    }
    resp = session.get(SCREENER_URL, params=params, timeout=15)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def parse_total(soup: BeautifulSoup) -> int:
    for tag in soup.find_all("td"):
        text = tag.get_text(strip=True)
        if "Total:" in text:
            # "Total: 342 #1"  →  342
            parts = text.replace("Total:", "").strip().split()
            if parts and parts[0].replace(",", "").isdigit():
                return int(parts[0].replace(",", ""))
    return 0


def parse_tickers(soup: BeautifulSoup) -> list[str]:
    return [
        a.get_text(strip=True)
        for a in soup.find_all("a", class_="screener-link-primary")
        if a.get_text(strip=True)
    ]


def get_high_pe_tickers(proxy: str | None = None) -> list[str]:
    session = build_session(proxy)
    all_tickers: list[str] = []

    soup = fetch_page(1, session)
    total = parse_total(soup)
    if total == 0:
        print("No tickers found or unable to parse total.", file=sys.stderr)
        return all_tickers

    print(f"Finviz reports {total} tickers with P/E > 100", file=sys.stderr)
    all_tickers.extend(parse_tickers(soup))

    offset = 1 + PAGE_SIZE
    while offset <= total:
        time.sleep(0.6)  # avoid hammering the server
        soup = fetch_page(offset, session)
        batch = parse_tickers(soup)
        if not batch:
            break
        all_tickers.extend(batch)
        print(f"  {len(all_tickers)}/{total} fetched...", file=sys.stderr)
        offset += PAGE_SIZE

    return all_tickers


def save_csv(tickers: list[str], path: str) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ticker"])
        writer.writerows([[t] for t in tickers])
    print(f"Saved {len(tickers)} tickers to {path}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", metavar="FILE", help="Save tickers to CSV file")
    parser.add_argument("--proxy", metavar="URL", help="HTTP/HTTPS proxy URL")
    args = parser.parse_args()

    tickers = get_high_pe_tickers(proxy=args.proxy)
    print(f"\nFound {len(tickers)} tickers with P/E > 100\n", file=sys.stderr)

    if args.output:
        save_csv(tickers, args.output)
    else:
        print("\n".join(tickers))


if __name__ == "__main__":
    main()
