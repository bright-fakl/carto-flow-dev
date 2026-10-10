---
pr: 51
title: Use US spelling in prose throughout src/ and docs/
description: British spellings converted to US in docstrings, comments, Markdown and notebook Markdown cells. Prose only — no identifier, kwarg or API value changed.
url: https://github.com/bright-fakl/carto-flow/pull/51
branch: spelling-us
base: main
date: 2026-09-23 15:37
kind: pr
topic: infra
---

**No figures, by nature of the change.** Nothing that renders is affected: no
plotting default, color value, layout parameter or algorithm constant was
touched, so a before/after figure pair would be bit-identical by construction.
The evidence carried here is textual instead — the token-level scan that proves
no identifier moved, plus the full build and test record.

## What changed

246 occurrences across 47 files, all of them inside docstrings, comments,
Markdown, or notebook Markdown cells.

| term | n | | term | n |
|---|---|---|---|---|
| `colour*` | 102 | | `grey` | 7 |
| `neighbour*` | 47 | | `serialis*` | 5 |
| `normalis*` | 31 | | `honour*` | 4 |
| `centre*` | 13 | | `initialis*` | 4 |
| `behaviour*` | 12 | | `artefact` | 3 |
| `visualis*` | 9 | | `analyse*` | 3 |
| `labelled` | 2 | | `minimis`, `optimis`, `prioritis`, `summaris` | 1 each |

The starting estimate of 226 was low: it missed `grey` (7), `honour*` (4),
`initialis*` (4), `serialis*` (5) and `minimis*` (1), and counted `normalis*`
as 30 rather than 31.

Searched for and found **zero** occurrences of: `licence`, `defence`,
`practise`, `modelling`, `travelling`, `cancelled`, `judgement`, `organis*`,
`recognis*`, `utilis*`, `maximis*`, `specialis*`, `standardis*`, `catalogue`,
`dialogue`, `programme`, `flavour`, `favour`, `armour`, `archaeo*`.
`analysis`/`analyses` (the noun) is US-correct and was left alone; only the
verb forms `analyse`/`Analyse`/`analyses` (3) were changed.

## Why no identifier could break

A tokenize pass over every `.py` file in `src/` and `docs/` listed every token
containing a British spelling that was **not** a `COMMENT` or `STRING` token.
The result was empty: there is no British-spelled name, attribute, parameter or
import anywhere in the tracked source. The edit script then applied
replacements only inside `COMMENT` and `STRING` token spans, so a name could
not have been rewritten even if one had existed.

Markdown was checked the same way: every inline `` `code` `` span in `docs/`
was extracted and searched — none contained a British spelling (the API names
in the mosaic explanation are already `neighbor_weight`, `neighbor_bfs`).
Every fenced-code hit was a `#` comment inside the block.

## Deliberately left alone

- **All identifiers, everywhere.** `neighbor_weight`, `neighbor_bfs`,
  `size_normalization`, `normalization`, `penalize_disconnected`,
  `edgecolor`, `facecolor`, `colormap`, `color=` kwargs in examples. Renaming
  any of these is a breaking API change, not a spelling fix.
- **`emphasis`** (1, `docs/tutorials/basic-proportional-cartogram.ipynb`) —
  already correct US English, not a British form.
- **`analysis` / `Analysis`** (68) — same.
- **`tests/`** (~33 occurrences, including local variables named
  `neighbours`) — outside the stated `src/` + `docs/` scope. Worth a
  follow-up; the local variables there are private to the tests, so they
  could be renamed safely, unlike anything in `src/`.
- **`visual_checks/mosaic-distance-normalisation/`** — a directory name in
  this review workspace; renaming it would orphan the built index entry.

## Judgment calls

Ten hits were string literals rather than docstrings or comments. All ten are
prose a user reads — error and warning message text, and one plot axis label
(`"Normalised inertia (relative to group mean)"`). They were converted. None
is an API value, and a grep over `tests/` confirmed no test asserts on any of
these strings (`pytest.raises(match=...)` included), so nothing was coupled to
the old wording.

One notebook **code**-cell line was changed:
`plt.suptitle("Boundary behaviour — …")` → `"Boundary behavior — …"` in
`docs/how-to/voronoi_cartogram/boundaries.ipynb`. It is a figure title string,
not code behavior.

One substitution artifact was caught and fixed before committing: a substring
rule turned `centred` into `center` + `d`. Two occurrences
(`flow_cartogram/density.py`, `symbol_cartogram/symbols.py`) were repaired to
`centered`. Every resulting word form was then listed and checked by eye —
all 37 distinct forms are valid English.

## Verification

- `make check` — clean: pre-commit (ruff check, ruff format, nbstripout, JSON
  and YAML validity), mypy on 82 source files, deptry.
- Full test suite — **712 passed**, 0 failed, in 83 s.
- `uv run mkdocs build -s` — **exit 0**, built in 593 s, no warnings promoted
  to errors.
- All four touched notebooks executed end to end with nbclient,
  `kernel_name="python3"`, `allow_errors=False`: `boundaries.ipynb`,
  `inspect-convergence.ipynb`, `topology.ipynb`,
  `basic-voronoi-cartogram.ipynb` — all OK.
- Whole `git diff` read line by line (234 changed lines) before pushing. No
  changed line contains an assignment, a call argument, or an import.
- Pushed tree re-checked with `git show origin/spelling-us:<path>` on five
  files, including `layouts/mosaic/__init__.py`, `symbol_cartogram/tiling.py`
  and `boundaries.ipynb`: zero residual British spellings in each.
- No file under `docs/examples/` was created or modified.
