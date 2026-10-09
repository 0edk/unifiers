# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

The project is entirely in the working directory of this CLAUDE.md.
Never look outside this working directory.

## Architecture

### Data archive (one-time, human-run, not part of normal operation)

A standalone script (`gen/fetch_archive.py`) is run manually, once (and again only if we
deliberately want to refresh it), to build a local, offline archive.

Verified against the live site: `keyword:core` is a small, exclusive OEIS designation (~183
sequences total — e.g. primes, Fibonacci, Catalan, partition numbers — *not* the ~15,000 originally
assumed), and OEIS's public search JSON API (`oeis.org/search?q=keyword:core&fmt=json&start=N`)
already returns each matching sequence's name *and* a generous run of leading terms in the same
response — no need to separately parse the full `stripped.gz`/`names.gz` bulk dumps.

- Page through that search endpoint 10 times (`start=0,10,...,90`, 10 results per page), with a
  short pause between requests. Anonymous (unauthenticated) access caps total results at 100, so
  this retrieves 100 of the ~183 core sequences — comfortably enough variety for puzzle generation.
- For each result, keep its `name` and the subset of its `data` terms falling in `[2, 99]`; drop
  any sequence left with fewer than 4 such terms (it could never supply a full group).
- Write the filtered result to `gen/data/core_sequences.json`, checked into the repo, e.g.:
  ```json
  {
    "A000045": { "name": "Fibonacci numbers: F(n) = F(n-1) + F(n-2) with F(0) = 0 and F(1) = 1.", "terms_2_99": [2,3,5,8,13,21,34,55,89] },
    ...
  }
  ```
- This script is never invoked by the generator, the web app, or any automation — it is a manual,
  occasional maintenance step.
- Only Python standard library (`urllib`, `json`, `time`, etc.) is used — no third-party dependencies.

### Puzzle generator (`gen/generate_puzzle.py`)

Run on demand; produces exactly one puzzle per invocation (re-run it to get a different puzzle):

1. Load `gen/data/core_sequences.json`.
2. Randomly pick 4 candidate sequences that each have ≥4 terms in `[2, 99]`.
3. For each, compute its terms in `[2, 99]` that are *not* present in any of the other 3 sequences'
   term sets. If all 4 sequences have ≥4 such exclusive terms, pick 4 at random from each — this is
   the solution. Otherwise, discard this combination and retry with a new random set of 4 (bounded
   retry loop; the core set is large enough this converges quickly). No deliberate biasing toward
   numerically "confusable" sequences in v1 — overlap-avoidance is the only constraint.
4. For each sequence, derive a short, human-readable "clean label" from its OEIS `name` field via a
   text-cleanup heuristic (cut at the first semicolon/colon/formula marker, strip trailing
   punctuation, truncate to a reasonable length). This is fully automatic, not hand-curated, since
   the core set is too large to label by hand.
5. Write `web/puzzle.js` containing something like:
   ```js
   const PUZZLE = {
     groups: [
       { label: "Fibonacci numbers", members: [2, 3, 5, 8] },
       { label: "...", members: [...] },
       { label: "...", members: [...] },
       { label: "...", members: [...] }
     ]
   };
   ```
   A plain `<script>`-loaded JS file (not JSON + `fetch`) so the web app works by just opening
   `index.html` directly as a `file://` URL, with no local server and no CORS issues.

### Web app (`web/`)

Pure static HTML/CSS/vanilla JS, no build step, no dependencies.

- Loads `puzzle.js`, then renders the 16 numbers from all 4 groups as tiles in a shuffled 4×4 grid.
- Clicking a tile selects/deselects it; at most 4 tiles may be selected at once.
- A Submit button is enabled only when exactly 4 tiles are selected. On submit:
  - **Exact match** with one of the remaining (unsolved) groups → that group is solved: its tiles
    are locked/removed from play with a distinct color, and its clean label is displayed.
  - **3-of-4 match** with a single true group (and the 4th from elsewhere) → show a transient
    "One away..." hint, same as NYT Connections, without revealing which tile is wrong.
  - **Otherwise** → plain wrong-guess feedback.
- A plain-text mistake counter (e.g. "Mistakes: 2/4") increments on each wrong guess. No dots/lives
  graphic, no shuffle-tiles button in v1.
- **Win**: all 4 groups solved → show a win message.
- **Loss**: mistake counter reaches 4 → reveal all remaining unsolved groups with their labels, then
  show a loss message.
- No persistence: reloading the page restarts the same `puzzle.js` puzzle from a clean state. There
  is no in-browser "new puzzle" button — getting a new puzzle means re-running the generator.
- Responsive CSS grid/flex layout, playable on mobile and desktop.
- Small, unobtrusive footer credit: "Sequence data from OEIS (oeis.org)".

### Explicit non-goals (v1)

- No server/backend component; no automated or recurring OEIS access at runtime, build, or in CI —
  only the one-time manual archive fetch above.
- No deliberately confusable/trap sequence selection (pure overlap-avoidance only).
- No localStorage/progress persistence across reloads.
- No shuffle-tiles button, no mistake "lives" graphic.
- No density filtering of candidate sequences beyond "≥4 terms available in range" — a sequence
  like "all integers" is excluded implicitly, since by construction no other group's numbers could
  then avoid overlapping with it.
- No attempt at aesthetic CSS styling, only styling for a passable layout
