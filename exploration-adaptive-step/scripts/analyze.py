"""Markdown tables from the jsonl result files: python analyze.py grid.jsonl [more.jsonl ...]"""

import json
import sys
from collections import defaultdict

import numpy as np


def load(paths):
    rows = []
    for p in paths:
        rows += [json.loads(line) for line in open(p)]
    return rows


def robustness(rows, by=("variant", "rr", "R")):
    """Counts per group: converged / stalled / diverged / incomplete, median iterations and cost of the converged."""
    g = defaultdict(list)
    for r in rows:
        g[tuple(r[k] for k in by)].append(r)
    out = ["| " + " | ".join(by) + " | runs | conv | stall | div | incompl | med it (conv) | med cost (conv) | med max err % (conv) |", "|" + "---|" * (len(by) + 8)]
    for k, rs in sorted(g.items(), key=lambda kv: tuple(str(x) for x in kv[0])):
        c = defaultdict(int)
        for r in rs:
            c[r["cls"]] += 1
        conv = [r for r in rs if r["cls"] == "converged"]
        med = lambda key: f"{np.median([r[key] for r in conv]):.0f}" if conv else "-"
        mx = f"{np.median([r['out_max'] for r in conv]):.1f}" if conv else "-"
        out.append("| " + " | ".join(str(x) for x in k) + f" | {len(rs)} | {c['converged']} | {c['stalled']} | {c['diverged']} | {c['incomplete']} | {med('it')} | {med('cost')} | {mx} |")
    return "\n".join(out)


if __name__ == "__main__":
    rows = load(sys.argv[1:])
    print(robustness(rows))
