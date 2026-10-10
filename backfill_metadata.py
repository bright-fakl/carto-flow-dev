#!/usr/bin/env python3
"""One-off: add kind, topic, status, outcome and related to the existing pages.

The values are guesses made from each page's title and history; review the
printed table.  Without --apply nothing is written.  Pages that already carry
a key keep it.

    python3 backfill_metadata.py            # print the table
    python3 backfill_metadata.py --apply    # write summary.md headers
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# directory -> (topic, status, outcome, related); kind follows from the page's `pr` key,
# except where a row says otherwise through KIND.  `-` leaves a field unset.
PAGES = {
    # explorations and investigations
    "adaptive-recompute-experiment": ("flow", "led-to", "-", "pr110-stall-detection"),
    "exploration-adaptive-step": ("flow", "open", "-", "exploration-overview"),
    "exploration-area-coverage": ("flow", "open", "-", "exploration-overview"),
    "exploration-default-dt": ("flow", "open", "-", "exploration-overview"),
    "exploration-gsm-preview": ("flow", "on-hold", "-", "exploration-overview"),
    "exploration-gsm-scale": ("flow", "on-hold", "-", "exploration-overview"),
    "exploration-overview": ("flow", "on-hold", "-", "-"),
    "exploration-voronoi-options": ("voronoi", "open", "-", "pr111-voronoi-power-weights, pr112-voronoi-premorph"),
    "flow-1.1.2-vs-2.0.0": ("flow", "no-action", "the speedups were recorded in the 2.0.0 changelog (#61); nothing else follows", "-"),
    "grid-vs-mosaic-similarity": ("symbol", "led-to", "-", "pr40-mosaic-interior-bonus, pr55-docs-grid-vs-mosaic-guidance, pr56-mosaic-option-behavior-docs"),
    "mosaic-distance-normalisation": ("symbol", "on-hold", "-", "-"),
    "mosaic-options-sweep": ("symbol", "led-to", "-", "mosaic-inert-verify, pr48-mosaic-honest-hungarian-defaults, pr56-mosaic-option-behavior-docs"),
    "mosaic-world-islands": ("symbol", "led-to", "-", "pr44-contiguity-reachability-precheck, pr46-mosaic-component-pool-overlap, pr47-mosaic-min-one-tile, pr48-mosaic-honest-hungarian-defaults"),
    "packing-symbol-scale-investigation": ("symbol", "led-to", "-", "pr42-size-normalization-total"),
    "pr-TBD-voronoi-weights-extraction": ("voronoi", "superseded", "-", "pr111-voronoi-power-weights"),
    # PR pages: topic only
    "mosaic-inert-verify": ("symbol", "-", "-", "-"),
    "pr-mosaic-performance": ("symbol", "-", "-", "-"),
    "pr101-shrink-area-tolerance": ("proportional", "-", "-", "-"),
    "pr102-mosaic-symbol-size": ("symbol", "-", "-", "-"),
    "pr108-census-hispanic-total": ("data", "-", "-", "-"),
    "pr110-stall-detection": ("flow", "-", "-", "-"),
    "pr111-voronoi-power-weights": ("voronoi", "-", "-", "-"),
    "pr112-voronoi-premorph": ("voronoi", "-", "-", "-"),
    "pr23-mosaic-group-ids": ("symbol", "-", "-", "-"),
    "pr24-voronoi-degenerate-cells": ("voronoi", "-", "-", "-"),
    "pr25-voronoi-cell-extraction": ("voronoi", "-", "-", "-"),
    "pr27-voronoi-smoothing-tolerance": ("voronoi", "-", "-", "-"),
    "pr28-simplify-coverage-slivers": ("voronoi", "-", "-", "-"),
    "pr29-mosaic-repair-objective": ("symbol", "-", "-", "-"),
    "pr30-mosaic-chain-swap-repair": ("symbol", "-", "-", "-"),
    "pr31-mosaic-ring-swapback": ("symbol", "-", "-", "-"),
    "pr32-mosaic-enclosed-holes": ("symbol", "-", "-", "-"),
    "pr33-mosaic-multipart-regions": ("symbol", "-", "-", "-"),
    "pr34-mosaic-ring-swapback-reach": ("symbol", "-", "-", "-"),
    "pr35-flow-zero-value-metric": ("flow", "-", "-", "-"),
    "pr37-housekeeping": ("infra", "-", "-", "-"),
    "pr38-prescale-abs-and-zero-area": ("flow", "-", "-", "-"),
    "pr39-group-by-unsupported-error": ("symbol", "-", "-", "-"),
    "pr40-mosaic-interior-bonus": ("symbol", "-", "-", "-"),
    "pr41-packing-zero-size": ("symbol", "-", "-", "-"),
    "pr41b-all-zero-sizing": ("symbol", "-", "-", "-"),
    "pr42-size-normalization-total": ("symbol", "-", "-", "-"),
    "pr44-contiguity-reachability-precheck": ("symbol", "-", "-", "-"),
    "pr45-world-dataset-validity": ("data", "-", "-", "-"),
    "pr46-mosaic-component-pool-overlap": ("symbol", "-", "-", "-"),
    "pr47-mosaic-min-one-tile": ("symbol", "-", "-", "-"),
    "pr48-mosaic-honest-hungarian-defaults": ("symbol", "-", "-", "-"),
    "pr49-contiguity-precheck-test": ("symbol", "-", "-", "-"),
    "pr50-visual-checks-index-sort": ("infra", "-", "-", "-"),
    "pr51-us-spelling": ("infra", "-", "-", "-"),
    "pr52-mosaic-gallery-examples": ("symbol", "-", "-", "-"),
    "pr53-doc-fixes": ("infra", "-", "-", "-"),
    "pr54-remove-physics-layout": ("symbol", "-", "-", "-"),
    "pr55-docs-grid-vs-mosaic-guidance": ("symbol", "-", "-", "-"),
    "pr56-mosaic-option-behavior-docs": ("symbol", "-", "-", "-"),
    "pr57-tile-count-mosaic-rewrite": ("symbol", "-", "-", "-"),
    "pr58-changelog-migration-guide": ("infra", "-", "-", "-"),
    "pr62-multiresolution-tutorial-fixes": ("flow", "-", "-", "-"),
    "pr63-docs-progress-and-mosaic-quickstart": ("infra", "-", "-", "-"),
    "pr64-covid-waves-example": ("flow", "-", "-", "-"),
    "pr65-mathjax-textmacros": ("infra", "-", "-", "-"),
    "pr66-population-example-densify": ("flow", "-", "-", "-"),
    "pr67-release-prerelease-routing": ("infra", "-", "-", "-"),
    "pr68-wheel-smoke-test": ("infra", "-", "-", "-"),
    "pr69-release-docs-kernel": ("infra", "-", "-", "-"),
    "pr70-releasing-testpypi-command": ("infra", "-", "-", "-"),
    "pr71-releasing-uv-cache": ("infra", "-", "-", "-"),
    "pr96-symbol-plot-string-dtype": ("symbol", "-", "-", "-"),
    "pr97-morph-snapshot-coords-copy": ("flow", "-", "-", "-"),
}


def split_header(text):
    match = re.match(r"(---\n)(.*?)(\n---\n)", text, re.S)
    return (match.group(2), text[match.end() :]) if match else (None, text)


def main():
    apply = "--apply" in sys.argv
    dirs = sorted(p for p in ROOT.iterdir() if p.is_dir() and not p.name.startswith(".") and (p / "summary.md").is_file())
    missing = [p.name for p in dirs if p.name not in PAGES]
    unknown = [name for name in PAGES if not (ROOT / name).is_dir()]
    if missing or unknown:
        sys.exit(f"pages without a row: {missing}; rows without a page: {unknown}")
    print(f"{'directory':<44} {'kind':<12} {'topic':<13} {'status':<11} related")
    for directory in dirs:
        topic, status, outcome, related = PAGES[directory.name]
        text = (directory / "summary.md").read_text(encoding="utf-8")
        header, body = split_header(text)
        if header is None:
            sys.exit(f"{directory.name}: no metadata header")
        has_pr = re.search(r"^pr:\s*\d+", header, re.M) is not None
        kind = "pr" if has_pr else "exploration"
        add = {"kind": kind, "topic": topic}
        if not has_pr:
            add.update({"status": status, "outcome": outcome, "related": related})
        elif status != "-":
            add["status"] = status
        for key, value in add.items():
            if value == "-" or re.search(rf"^{key}:", header, re.M) and key != "status":
                continue
            header = re.sub(rf"^{key}:.*\n?", "", header, flags=re.M).rstrip("\n") if key == "status" else header
            header += f"\n{key}: {value}"
        print(f"{directory.name:<44} {kind:<12} {topic:<13} {status if not has_pr else '(github)':<11} {related if related != '-' else ''}")
        if apply:
            (directory / "summary.md").write_text(f"---\n{header}\n---\n{body}", encoding="utf-8")
    if not apply:
        print("\n(dry run; pass --apply to write)")


if __name__ == "__main__":
    main()
