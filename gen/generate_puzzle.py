#!/usr/bin/env python3
"""Generate one Connections-style puzzle from the local OEIS core-sequence archive.

Run on demand:

    python3 gen/generate_puzzle.py

Reads gen/data/core_sequences.json (built once by fetch_archive.py) and writes web/puzzle.js,
overwriting any previous puzzle. Re-run this script to get a different puzzle.
"""
import json
import random
import re
from pathlib import Path

ARCHIVE_PATH = Path(__file__).parent / "data" / "core_sequences.json"
OUTPUT_PATH = Path(__file__).parent.parent / "web" / "puzzle.js"
NUM_GROUPS = 4
GROUP_SIZE = 4
MAX_ATTEMPTS = 10000
LABEL_MAX_LEN = 56

_FORMULA_PREFIX_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*\s*\(")


def _looks_like_formula(text: str) -> bool:
    return bool(_FORMULA_PREFIX_RE.match(text.strip()))


def _finalize(label: str) -> str:
    label = label.strip().strip(",;:. ")
    if len(label) > LABEL_MAX_LEN:
        label = label[:LABEL_MAX_LEN].rsplit(" ", 1)[0]
    if label.count("(") > label.count(")"):
        label = label.rsplit("(", 1)[0]
    label = label.strip().strip(",;:. ")
    if label:
        label = label[0].upper() + label[1:]
    return label


def _find_top_level(text: str, delimiters: str) -> int:
    """Index of the first delimiter character not nested inside parentheses, or -1."""
    depth = 0
    for i, c in enumerate(text):
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        elif depth <= 0 and c in delimiters:
            return i
    return -1


def clean_label(name: str) -> str:
    """Derive a short human-readable label from an OEIS sequence's raw `name` field.

    OEIS names are written as encyclopedia entries, not puzzle labels, e.g.
    "Fibonacci numbers: F(n) = F(n-1) + F(n-2) ..." or "a(n) = sigma(n), the sum of the
    divisors of n.". This heuristic prefers a descriptive clause over a formula, splitting
    only on top-level punctuation so it doesn't cut inside a parenthesized formula.
    """
    first_sentence = re.split(r"\.(?:\s|$)", name, maxsplit=1)[0]
    colon_idx = _find_top_level(first_sentence, ":")
    if colon_idx != -1:
        prefix, rest = first_sentence[:colon_idx], first_sentence[colon_idx + 1 :]
        if _looks_like_formula(prefix):
            if rest.strip():
                return _finalize(rest)
        else:
            return _finalize(prefix)
    comma_idx = _find_top_level(first_sentence, ",")
    if comma_idx != -1:
        prefix, rest = first_sentence[:comma_idx], first_sentence[comma_idx + 1 :]
        if _looks_like_formula(prefix) and rest.strip():
            return _finalize(rest)
    return _finalize(first_sentence)


def load_archive() -> dict:
    return json.loads(ARCHIVE_PATH.read_text())


def try_build_puzzle(archive: dict, chosen_ids: list[str], rng: random.Random):
    term_sets = [set(archive[a]["terms_2_99"]) for a in chosen_ids]
    groups = []
    for i, a_id in enumerate(chosen_ids):
        others = set().union(*(term_sets[j] for j in range(NUM_GROUPS) if j != i))
        exclusive = sorted(term_sets[i] - others)
        if len(exclusive) < GROUP_SIZE:
            return None
        members = rng.sample(exclusive, GROUP_SIZE)
        groups.append({"label": clean_label(archive[a_id]["name"]), "members": members})
    return groups


def generate_puzzle(archive: dict, rng: random.Random) -> list[dict]:
    ids = list(archive.keys())
    for _ in range(MAX_ATTEMPTS):
        chosen_ids = rng.sample(ids, NUM_GROUPS)
        groups = try_build_puzzle(archive, chosen_ids, rng)
        if groups is not None:
            return groups
    raise RuntimeError(
        f"Could not find {NUM_GROUPS} non-overlapping sequences after {MAX_ATTEMPTS} attempts"
    )


def main() -> None:
    archive = load_archive()
    rng = random.Random()
    groups = generate_puzzle(archive, rng)

    js = "const PUZZLE = " + json.dumps({"groups": groups}, indent=2) + ";\n"
    OUTPUT_PATH.write_text(js)

    print(f"Wrote puzzle to {OUTPUT_PATH}")
    for g in groups:
        print(f"  {g['label']}: {g['members']}")


if __name__ == "__main__":
    main()
