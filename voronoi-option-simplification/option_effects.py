"""Effect of the regular Voronoi options on the 49 US states (the numbers the behavioral tests assert on).

Run from a carto-flow checkout of the PR branch (bundled data only):
    NUMBA_NUM_THREADS=8 uv run python option_effects.py
"""

import time
import warnings
from pathlib import Path

import numpy as np

from carto_flow import data
from carto_flow.voronoi_cartogram import ElasticBoundary, RasterBackend, VoronoiOptions, create_voronoi_cartogram

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
(HERE / "data").mkdir(exist_ok=True)
S = data.load_us_census(population=True).reset_index(drop=True)
OUT = []


def log(line=""):
    print(line, flush=True)
    OUT.append(line)


def union_vertices(result):
    u = result.to_geodataframe().geometry.union_all()
    return sum(len(p.exterior.coords) for p in (u.geoms if hasattr(u, "geoms") else [u]))


log("## adjacency_spring (resolution 150, 60 iterations, no weights)\n")
log("| adjacency_spring | fraction of input-adjacent pairs that stay adjacent |\n|---|---|")
for sp in (0.0, 0.1, 0.3, 0.6):
    r = create_voronoi_cartogram(S, backend=RasterBackend(resolution=150, adjacency_spring=sp), options=VoronoiOptions(n_iter=60))
    a = r.analyze_topology()
    log(f"| {sp} | {1 - a.n_violated_adjacency / a.n_adjacency_pairs:.3f} |")

log("\n## intra_group_spring with group_by (resolution 100, adjacency_spring 0.1, 60 iterations)\n")
log("| group_by | intra_group_spring | discontiguous groups |\n|---|---|---|")
for gcol in ("Division",):
    for isp in (None, 0.5, 1.0):
        r = create_voronoi_cartogram(S, group_by=gcol, backend=RasterBackend(resolution=100, adjacency_spring=0.1, intra_group_spring=isp), options=VoronoiOptions(n_iter=60))
        log(f"| {gcol} | {isp} | {r.analyze_topology(group_by=gcol).n_discontiguous_groups} |")

log("\n## ElasticBoundary strength (resolution 120, 40 iterations)\n")
log("| strength | area of the cell union / area of the input union |\n|---|---|")
area = S.geometry.union_all().area
for st in (0.0, 0.05, 0.3):
    r = create_voronoi_cartogram(S, backend=RasterBackend(resolution=120, boundary=ElasticBoundary(strength=st) if st else None), options=VoronoiOptions(n_iter=40))
    log(f"| {st} | {r.to_geodataframe().geometry.union_all().area / area:.3f} |")

log("\n## boundary (resolution 100, 20 iterations)\n")
log("| boundary | union area / input union area | roundness 4 pi A / P^2 | share of the input covered |\n|---|---|---|---|")
union = S.geometry.union_all()
for spec in ("union", "bbox", "convex_hull", "circle"):
    r = create_voronoi_cartogram(S, boundary=spec, backend=RasterBackend(resolution=100), options=VoronoiOptions(n_iter=20))
    u = r.to_geodataframe().geometry.union_all()
    log(f"| {spec} | {u.area / union.area:.2f} | {4 * np.pi * u.area / u.length ** 2:.2f} | {u.intersection(union).area / union.area:.3f} |")

log("\n## simplify_tol (resolution 120, 10 iterations)\n")
log("| simplify_tol (m) | vertices of the cell union |\n|---|---|")
for st in (None, 20000.0, 100000.0):
    r = create_voronoi_cartogram(S, backend=RasterBackend(resolution=120), options=VoronoiOptions(n_iter=10, simplify_tol=st))
    log(f"| {st} | {union_vertices(r)} |")
(HERE / "data" / "tables.md").write_text("\n".join(OUT) + "\n")
