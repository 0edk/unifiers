#!/usr/bin/env python3
"""One-time fetch of OEIS's "core" sequences into a local, offline archive.

Run manually:

    python3 gen/fetch_archive.py

Hits oeis.org's public search API a small, bounded number of times (one request per page of
the `keyword:core` search) and writes the filtered result to gen/data/core_sequences.json.
Not invoked by the generator, the web app, or any automation -- this is a manual, occasional
maintenance step, not a recurring access pattern.

Anonymous (unauthenticated) access to oeis.org search results is capped at the first 100
matches. keyword:core has ~183 sequences total, so this retrieves 100 of them -- comfortably
enough variety to generate puzzles from.
"""
import json
import time
import urllib.request
from pathlib import Path

SEARCH_URL = "https://oeis.org/search?q=keyword:core&fmt=json&start={start}"
PAGE_SIZE = 10
MAX_PAGES = 10
REQUEST_DELAY_SECONDS = 1.0
MIN_TERMS_IN_RANGE = 4
RANGE_LO, RANGE_HI = 2, 99
OUTPUT_PATH = Path(__file__).parent / "data" / "core_sequences.json"
USER_AGENT = "unifiers-connections-puzzle (one-time archive fetch; github.com oeis.org user)"


def fetch_page(start: int) -> list[dict]:
    req = urllib.request.Request(SEARCH_URL.format(start=start), headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def main() -> None:
    sequences: dict[str, dict] = {}
    for page in range(MAX_PAGES):
        start = page * PAGE_SIZE
        results = fetch_page(start)
        if not results:
            break
        for entry in results:
            a_number = f"A{entry['number']:06d}"
            terms = [int(t) for t in entry["data"].split(",") if t.strip()]
            terms_in_range = sorted({t for t in terms if RANGE_LO <= t <= RANGE_HI})
            if len(terms_in_range) < MIN_TERMS_IN_RANGE:
                continue
            sequences[a_number] = {"name": entry["name"], "terms_2_99": terms_in_range}
        if page < MAX_PAGES - 1:
            time.sleep(REQUEST_DELAY_SECONDS)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(sequences, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {len(sequences)} core sequences to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
