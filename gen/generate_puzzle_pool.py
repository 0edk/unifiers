#!/usr/bin/env python3
"""Generate a one-year rotating pool of puzzles, one small JS file per puzzle.

Run on demand:

    python3 gen/generate_puzzle_pool.py

Reads gen/data/core_sequences.json and writes, under web/puzzles/:
  - 000.js .. NNN.js, each a single `const PUZZLE = {...};` (one puzzle)
  - manifest.js, `const PUZZLE_POOL_SIZE = N;` / `const PUZZLE_INDEX_WIDTH = W;`

The web app picks one file per calendar day (looping back to the start after
PUZZLE_POOL_SIZE days) and loads only that one file, instead of shipping every puzzle
to every player. Re-run this script to regenerate the whole pool from scratch.
"""
import json
import random
from pathlib import Path

from generate_puzzle import NUM_GROUPS, load_archive, try_build_puzzle

POOL_SIZE = 365
MAX_ATTEMPTS_PER_PUZZLE = 10000
OUTPUT_DIR = Path(__file__).parent.parent / "web" / "puzzles"


def generate_pool(archive: dict, rng: random.Random, size: int) -> list[list[dict]]:
    ids = list(archive.keys())
    used_combos: set[frozenset] = set()
    pool: list[list[dict]] = []
    max_total_attempts = size * MAX_ATTEMPTS_PER_PUZZLE

    attempts = 0
    while len(pool) < size and attempts < max_total_attempts:
        attempts += 1
        chosen_ids = rng.sample(ids, NUM_GROUPS)
        combo = frozenset(chosen_ids)
        if combo in used_combos:
            continue
        groups = try_build_puzzle(archive, chosen_ids, rng)
        if groups is None:
            continue
        used_combos.add(combo)
        pool.append(groups)

    if len(pool) < size:
        raise RuntimeError(
            f"Only found {len(pool)} unique puzzles after {attempts} attempts (wanted {size})"
        )
    return pool


def write_pool(pool: list[list[dict]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for old_file in OUTPUT_DIR.glob("*.js"):
        old_file.unlink()

    width = len(str(len(pool) - 1))
    for i, groups in enumerate(pool):
        path = OUTPUT_DIR / f"{i:0{width}d}.js"
        path.write_text("const PUZZLE = " + json.dumps({"groups": groups}, indent=2) + ";\n")

    manifest = OUTPUT_DIR / "manifest.js"
    manifest.write_text(
        f"const PUZZLE_POOL_SIZE = {len(pool)};\nconst PUZZLE_INDEX_WIDTH = {width};\n"
    )


def main() -> None:
    archive = load_archive()
    rng = random.Random()
    pool = generate_pool(archive, rng, POOL_SIZE)
    write_pool(pool)
    print(f"Wrote {len(pool)} puzzles to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
