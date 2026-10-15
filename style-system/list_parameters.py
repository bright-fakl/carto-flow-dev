"""List every parameter of the public plot, animate and preview functions and the plot options dataclasses.

    uv run python list_parameters.py > data/plot_parameters.md   # in a checkout of main
"""
import ast
import collections
import glob

rows = collections.defaultdict(list)
for f in sorted(glob.glob("src/carto_flow/**/*.py", recursive=True)):
    if "checkpoints" in f or "mosaic_cartogram" in f:
        continue
    short = f.replace("src/carto_flow/", "").replace(".py", "")
    tree = ast.parse(open(f).read())
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and not n.name.startswith("_") and (n.name.startswith(("plot", "animate", "preview")) or n.name == "plot"):
            for a in n.args.args + n.args.kwonlyargs:
                if a.arg not in ("self", "cls"):
                    rows[a.arg].append(f"{short}.{n.name}")
        if isinstance(n, ast.ClassDef) and n.name.endswith("PlotOptions"):
            for b in n.body:
                if isinstance(b, ast.AnnAssign) and isinstance(b.target, ast.Name):
                    rows[b.target.id].append(f"{short}.{n.name}")
print("| parameter | functions |\n|---|---|")
for k in sorted(rows):
    print(f"| `{k}` | {', '.join(sorted(set(rows[k])))} |")
