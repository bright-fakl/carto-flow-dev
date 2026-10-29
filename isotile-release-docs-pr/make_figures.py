# Figures of the page: the catalog as a contact sheet (all 81 types, as the catalog page of the docs draws them) and the
# benchmark of benchmarks/bench.py as a chart. Run from an isotile checkout on branch release-docs (docs group synced):
#   uv run --group docs python <this directory>/make_figures.py
# Writes catalog_sheet.png and benchmark_chart.png next to this file.
import importlib.util
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

here = Path(__file__).parent
root = Path.cwd()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


hooks = load(root / "docs" / "hooks.py", "docs_hooks")
figs = hooks._figures()
from isotile import tiling_types

# Catalog sheet: 81 panels of the light theme.
numbers = tiling_types()
cols = 9
fig, axes = plt.subplots(9, cols, figsize=(13.5, 14), dpi=80)
for ax in axes.ravel():
    ax.axis("off")
for ax, number in zip(axes.ravel(), numbers, strict=False):
    f = hooks.type_figure(number)(figs.LIGHT)
    f.canvas.draw()
    ax.imshow(f.canvas.buffer_rgba())
    ax.set_title(f"IH{number}", fontsize=8)
    plt.close(f)
fig.tight_layout()
fig.savefig(here / "catalog_sheet.png", facecolor="white")

# Benchmark chart
bench = load(root / "benchmarks" / "bench.py", "bench")
sizes = [1000, 10000, 100000]
ops = ("fill_region", "adjacency", "neighbor_lists", "geometric")
fig, axes = plt.subplots(1, 4, figsize=(13, 3.4), sharey=True)
for ax, (name, case) in zip(axes, bench.CASES, strict=True):
    rows = [bench.run_case(name, case, n, 1, None) for n in sizes]
    for op in ops:
        ax.loglog([r["n_tiles"] for r in rows], [r[op] for r in rows], "o-", label=op)
    ax.set_title(name)
    ax.set_xlabel("tiles")
    ax.grid(alpha=0.3)
axes[0].set_ylabel("seconds (1 run)")
axes[0].legend(fontsize=8)
fig.tight_layout()
fig.savefig(here / "benchmark_chart.png", facecolor="white", dpi=90)
