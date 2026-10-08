"""Layout-agnostic fidelity/integrity metrics for tiled symbol-cartogram layouts.

Everything here is computed *externally* from a ``LayoutResult`` plus the input
GeoDataFrame, so grid and mosaic are measured by exactly the same code.  Neither
layout's own ``AlgorithmMetrics.algorithm`` payload is consulted.

Uniform representation
----------------------
Both layouts carry a ``TilingResult`` and an ``assignments`` array, but they
index it differently:

* ``GridLayoutResult.assignments[i]``  = tile index for *item* i;
  ``source_indices[i]`` = region index for item i (or identity when None).
* ``MosaicLayoutResult.assignments[j]`` = tile index of the j-th *assigned tile*;
  ``source_indices[j]`` = region index for that tile.

Both therefore reduce to a list of ``(tile_index, region_index)`` pairs, which is
the only thing the metrics below read.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field

import numpy as np
import shapely
from shapely.affinity import scale as shp_scale
from shapely.affinity import translate as shp_translate
from shapely.geometry import Point
from shapely.ops import unary_union


# --------------------------------------------------------------------------
# uniform extraction
# --------------------------------------------------------------------------


@dataclass
class Placement:
    """Layout-agnostic view of a tiled layout result."""

    tile_of_region: list[list[int]]  # region -> list of tile indices
    region_of_tile: dict[int, int]
    tile_adj: np.ndarray  # (m, m) bool edge adjacency
    tile_centers: np.ndarray  # (m, 2)
    tile_size: float
    tile_area: float
    tile_edge_len: float
    tile_sides: int
    n_lattice_tiles: int
    tiling_name: str
    duplicate_tile_assignments: int


def extract_placement(result, n_regions: int) -> Placement:
    tr = result.tiling_result
    if tr is None:
        raise ValueError("result has no tiling_result")
    assignments = np.asarray(result.assignments, dtype=np.intp)
    src = result.source_indices

    if result.layout_type == "mosaic":
        if src is None:
            raise ValueError("mosaic result without source_indices")
        regions = np.asarray(src, dtype=np.intp)
        tiles = assignments
    else:  # grid (and any other item-indexed layout)
        tiles = assignments
        regions = np.asarray(src, dtype=np.intp) if src is not None else np.arange(len(assignments), dtype=np.intp)
    if len(tiles) != len(regions):
        raise ValueError(f"length mismatch tiles={len(tiles)} regions={len(regions)}")

    tile_of_region: list[list[int]] = [[] for _ in range(n_regions)]
    region_of_tile: dict[int, int] = {}
    dupes = 0
    for t, g in zip(tiles.tolist(), regions.tolist()):
        if t in region_of_tile:
            dupes += 1
        region_of_tile[t] = g
        tile_of_region[g].append(int(t))

    canon = tr.canonical_tile
    sides = tr.n_base_vertices or max(3, len(canon.exterior.coords) - 1)
    edge_len = canon.length / sides

    return Placement(
        tile_of_region=tile_of_region,
        region_of_tile=region_of_tile,
        tile_adj=np.asarray(tr.adjacency, dtype=bool),
        tile_centers=tr.centers,
        tile_size=float(tr.tile_size),
        tile_area=float(canon.area),
        tile_edge_len=float(edge_len),
        tile_sides=int(sides),
        n_lattice_tiles=int(tr.n_tiles),
        tiling_name=type(canon).__name__ if not hasattr(tr, "tile_size") else "",
        duplicate_tile_assignments=dupes,
    )


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def _adj_list(adj: np.ndarray) -> list[list[int]]:
    return [np.flatnonzero(row).tolist() for row in adj]


def _pct(values, q):
    if len(values) == 0:
        return None
    return float(np.percentile(np.asarray(values, dtype=float), q))


def _components(nodes: list[int], nbrs: list[list[int]]) -> int:
    """Number of connected components of ``nodes`` in the induced subgraph."""
    s = set(nodes)
    seen: set[int] = set()
    n = 0
    for start in nodes:
        if start in seen:
            continue
        n += 1
        stack = [start]
        seen.add(start)
        while stack:
            t = stack.pop()
            for nb in nbrs[t]:
                if nb in s and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
    return n


def _multi_source_bfs(sources: list[int], nbrs: list[list[int]], m: int) -> np.ndarray:
    dist = np.full(m, -1, dtype=np.int32)
    q = deque()
    for s in sources:
        dist[s] = 0
        q.append(s)
    while q:
        t = q.popleft()
        d = dist[t] + 1
        for nb in nbrs[t]:
            if dist[nb] < 0:
                dist[nb] = d
                q.append(nb)
    return dist


def input_adjacent_pairs(adjacency_G: np.ndarray) -> list[tuple[int, int]]:
    a = np.asarray(adjacency_G)
    iu = np.triu_indices(a.shape[0], k=1)
    mask = a[iu] > 0
    return list(zip(iu[0][mask].tolist(), iu[1][mask].tolist()))


def input_components(adjacency_G: np.ndarray) -> np.ndarray:
    """Connected-component label per input region."""
    a = np.asarray(adjacency_G) > 0
    n = a.shape[0]
    labels = np.full(n, -1, dtype=np.intp)
    c = 0
    for i in range(n):
        if labels[i] >= 0:
            continue
        stack = [i]
        labels[i] = c
        while stack:
            u = stack.pop()
            for v in np.flatnonzero(a[u]).tolist():
                if labels[v] < 0:
                    labels[v] = c
                    stack.append(v)
        c += 1
    return labels


# --------------------------------------------------------------------------
# silhouette (area-based only)
# --------------------------------------------------------------------------


def _inter_area(a, b) -> float:
    """Intersection area, retried through GEOS robustness failures.

    The scaled footprint occasionally trips a ``TopologyException`` against the
    morphed union.  Retry with validated geometries, then on a snapped
    precision grid (1 unit = 1 metre here, far below tile size).  NaN if all
    three fail, so one bad geometry cannot lose a whole sweep.
    """
    try:
        return float(a.intersection(b).area)
    except Exception:
        pass
    try:
        return float(shapely.make_valid(a).intersection(shapely.make_valid(b)).area)
    except Exception:
        pass
    try:
        return float(shapely.set_precision(a, 1.0).intersection(shapely.set_precision(b, 1.0)).area)
    except Exception:
        return float("nan")


def silhouette_metrics(occupied_polygons, centres, study_union) -> dict:
    """How closely the occupied tile footprint reproduces the map outline.

    Area-based only.  No perimeter measure is taken on the unioned footprint:
    unioning tiles leaves hairline internal edges whose perimeter is not
    reproducible.

    Two families of numbers are returned.

    *Raw* numbers use the tilegram exactly where the layout put it.  They
    conflate shape with the fact that the two layouts choose different tile
    sizes, so a tilegram can cover more or less total area than the map.

    *Aligned* numbers remove that confound with a similarity transform chosen
    without reference to either layout: the footprint is scaled about its own
    centroid until its area equals the study union's area, then translated so
    the two centroids coincide.  No rotation and no shear, so nothing can
    "fit" a shape it does not have; only overall size and position are taken
    out.  What remains is silhouette fidelity.
    """
    occ = unary_union(list(occupied_polygons))
    b_area = float(study_union.area)
    a_raw = float(occ.area)
    if a_raw <= 0 or b_area <= 0:
        return {}

    inter_raw = _inter_area(occ, study_union)
    inside = sum(1 for c in centres if study_union.contains(Point(float(c[0]), float(c[1]))))

    s = math.sqrt(b_area / a_raw)
    a = shp_scale(occ, xfact=s, yfact=s, origin=occ.centroid)
    a = shp_translate(a, xoff=study_union.centroid.x - a.centroid.x, yoff=study_union.centroid.y - a.centroid.y)
    inter = _inter_area(a, study_union)
    a_area = float(a.area)
    union_area = a_area + b_area - inter

    return {
        "area_ratio_raw": a_raw / b_area,
        "frac_input_covered_raw": inter_raw / b_area,
        "frac_footprint_on_input_raw": inter_raw / a_raw,
        "frac_tile_centres_inside": inside / len(centres) if len(centres) else None,
        "iou_aligned": inter / union_area if union_area > 0 else None,
        "symdiff_norm_aligned": (a_area + b_area - 2 * inter) / b_area,
        "frac_input_covered_aligned": inter / b_area,
    }


# --------------------------------------------------------------------------
# the metric set
# --------------------------------------------------------------------------


def compute_metrics(
    result,
    *,
    orig_centroids: np.ndarray,
    adjacency_G: np.ndarray,
    requested_counts: np.ndarray,
    input_bounds: tuple[float, float, float, float],
    group_labels: np.ndarray | None = None,
    study_union=None,
    min_overlap_frac: float = 0.1,
    working_union=None,
    working_centroids: np.ndarray | None = None,
) -> dict:
    """All fidelity + integrity metrics for one layout result.

    Parameters
    ----------
    result
        A ``GridLayoutResult`` or ``MosaicLayoutResult``.
    orig_centroids
        (G, 2) original geometry centroids.
    adjacency_G
        (G, G) input region adjacency.
    requested_counts
        (G,) tiles each region should have received.
    input_bounds
        Bounds of the input geometries.
    group_labels
        (G,) group id per region when ``group_by`` was used, else None.
    study_union
        Union of the *original* input geometries.  Used for the core-tile test
        and as **reference 2** for the silhouette metric: the only reference
        that is comparable across layouts, because grid never morphs and so
        never sees anything else.
    working_union
        The footprint the layout actually tiled against -- the *morphed* union
        for ``MosaicLayout(morph=True)``, which builds ``working_union`` from
        the morphed geometries.  Used as **reference 1** for the silhouette
        metric ("did the layout cover what it was asked to cover").  Reference 1
        is NOT comparable across layouts: different runs aim at different
        shapes.  Pass None when the layout worked against the original union,
        in which case reference 1 equals reference 2.
    working_centroids
        (G, 2) centroids of the morphed geometries, when the layout morphed.
        Adds a secondary displacement measured from those, which separates
        "the assignment moved the region" from "the morph moved the region".
        The headline displacement is always measured from the original
        centroids, for every run.
    """
    G = len(orig_centroids)
    p = extract_placement(result, G)
    nbrs = _adj_list(p.tile_adj)
    m = p.n_lattice_tiles
    out: dict = {}

    # ---- tiling context -------------------------------------------------
    out["tiling"] = {
        "tile_size": p.tile_size,
        "tile_area": p.tile_area,
        "tile_edge_len": p.tile_edge_len,
        "tile_sides": p.tile_sides,
        "n_lattice_tiles": m,
        "n_assigned_tiles": len(p.region_of_tile),
        "duplicate_tile_assignments": p.duplicate_tile_assignments,
    }

    # ---- block centroids ------------------------------------------------
    block_centroid = np.full((G, 2), np.nan)
    for g, tiles in enumerate(p.tile_of_region):
        if tiles:
            block_centroid[g] = p.tile_centers[tiles].mean(axis=0)
    placed = ~np.isnan(block_centroid[:, 0])

    # ---- 1. displacement (~origin_weight) -------------------------------
    d = np.linalg.norm(block_centroid[placed] - orig_centroids[placed], axis=1)
    if working_centroids is not None:
        dm = np.linalg.norm(block_centroid[placed] - np.asarray(working_centroids)[placed], axis=1)
        morphed_med, morphed_p90 = _pct(dm / p.tile_size, 50), _pct(dm / p.tile_size, 90)
    else:
        morphed_med = morphed_p90 = None
    out["displacement"] = {
        "median": _pct(d, 50),
        "p90": _pct(d, 90),
        "median_tiles": _pct(d / p.tile_size, 50),
        "p90_tiles": _pct(d / p.tile_size, 90),
        "max_tiles": float(np.max(d / p.tile_size)) if len(d) else None,
        "n_regions_placed": int(placed.sum()),
        # secondary, morph=True runs only: measured from the MORPHED centroids
        "median_tiles_vs_working": morphed_med,
        "p90_tiles_vs_working": morphed_p90,
    }

    # ---- 2. adjacency preservation (~neighbor_weight) -------------------
    pairs = input_adjacent_pairs(adjacency_G)
    # region -> set of lattice neighbours of its tiles
    halo: list[set[int]] = []
    tset: list[set[int]] = []
    for g in range(G):
        ts = set(p.tile_of_region[g])
        tset.append(ts)
        h: set[int] = set()
        for t in ts:
            h.update(nbrs[t])
        halo.append(h)

    edge_adj = 0
    nonadj_hops: list[int] = []
    bfs_cache: dict[int, np.ndarray] = {}
    for a, b in pairs:
        if not tset[a] or not tset[b]:
            continue
        if halo[a] & tset[b]:
            edge_adj += 1
            continue
        if a not in bfs_cache:
            bfs_cache[a] = _multi_source_bfs(sorted(tset[a]), nbrs, m)
        dist = bfs_cache[a]
        dd = [int(dist[t]) for t in tset[b] if dist[t] >= 0]
        nonadj_hops.append(min(dd) if dd else -1)

    n_eval = edge_adj + len(nonadj_hops)
    out["adjacency"] = {
        "n_input_pairs": len(pairs),
        "n_evaluated": n_eval,
        "frac_edge_adjacent": (edge_adj / n_eval) if n_eval else None,
        "n_broken": len(nonadj_hops),
        "broken_hops_median": _pct([h for h in nonadj_hops if h >= 0], 50),
        "broken_hops_p90": _pct([h for h in nonadj_hops if h >= 0], 90),
        "broken_hops_max": max([h for h in nonadj_hops if h >= 0], default=None),
        "n_unreachable": sum(1 for h in nonadj_hops if h < 0),
    }

    # ---- 3. direction preservation (~topology_weight) -------------------
    devs: list[float] = []
    for a, b in pairs:
        if not (placed[a] and placed[b]):
            continue
        v0 = orig_centroids[b] - orig_centroids[a]
        v1 = block_centroid[b] - block_centroid[a]
        n0, n1 = np.linalg.norm(v0), np.linalg.norm(v1)
        if n0 == 0 or n1 == 0:
            continue
        ang = math.degrees(
            math.atan2(float(v0[0] * v1[1] - v0[1] * v1[0]), float(v0[0] * v1[0] + v0[1] * v1[1]))
        )
        devs.append(abs(ang))
    out["direction"] = {
        "n_pairs": len(devs),
        "median_abs_dev_deg": _pct(devs, 50),
        "p90_abs_dev_deg": _pct(devs, 90),
        "frac_reversed_gt90": (sum(1 for x in devs if x > 90) / len(devs)) if devs else None,
    }

    # ---- 4. spread (~compactness) ---------------------------------------
    occ = sorted(p.region_of_tile)
    if occ:
        c = p.tile_centers[occ]
        w = float(c[:, 0].max() - c[:, 0].min())
        h = float(c[:, 1].max() - c[:, 1].min())
    else:
        w = h = 0.0
    ixmin, iymin, ixmax, iymax = input_bounds
    iw, ih = ixmax - ixmin, iymax - iymin
    occ_area = w * h
    tiles_area = len(occ) * p.tile_area
    out["spread"] = {
        "occupied_bbox_w_tiles": w / p.tile_size if p.tile_size else None,
        "occupied_bbox_h_tiles": h / p.tile_size if p.tile_size else None,
        "occupied_aspect": (w / h) if h > 0 else None,
        "input_aspect": (iw / ih) if ih > 0 else None,
        "aspect_ratio_vs_input": ((w / h) / (iw / ih)) if h > 0 and ih > 0 else None,
        "bbox_fill_frac": (tiles_area / occ_area) if occ_area > 0 else None,
        "occupied_bbox_area_vs_input": (occ_area / (iw * ih)) if iw * ih > 0 else None,
    }

    # combinatorial Polsby-Popper on the tile adjacency graph
    pp: list[float] = []
    for g in range(G):
        ts = tset[g]
        if not ts:
            continue
        perim_edges = 0
        for t in ts:
            same = sum(1 for nb in nbrs[t] if nb in ts)
            perim_edges += p.tile_sides - same
        if perim_edges <= 0:
            continue
        area = len(ts) * p.tile_area
        perim = perim_edges * p.tile_edge_len
        pp.append(4 * math.pi * area / (perim * perim))
    out["compactness"] = {
        "polsby_popper_median": _pct(pp, 50),
        "polsby_popper_mean": float(np.mean(pp)) if pp else None,
        "polsby_popper_p10": _pct(pp, 10),
        "n_regions": len(pp),
    }

    # ---- 5. integrity ----------------------------------------------------
    got = np.array([len(p.tile_of_region[g]) for g in range(G)], dtype=np.intp)
    req = np.asarray(requested_counts, dtype=np.intp)
    noncontig = 0
    for g in range(G):
        if p.tile_of_region[g] and _components(p.tile_of_region[g], nbrs) > 1:
            noncontig += 1

    integrity = {
        "regions_correct": int(np.sum(got == req)),
        "regions_total": G,
        "tiles_short_total": int(np.sum(np.maximum(req - got, 0))),
        "tiles_excess_total": int(np.sum(np.maximum(got - req, 0))),
        "n_regions_missing_tiles": int(np.sum(got == 0)),
        "n_noncontiguous_regions": noncontig,
    }

    # split groups (group_by only)
    if group_labels is not None:
        comp = input_components(adjacency_G)
        raw_split = 0
        adj_split = 0
        for gid in np.unique(group_labels):
            members = np.flatnonzero(group_labels == gid).tolist()
            ts: list[int] = []
            for g in members:
                ts.extend(p.tile_of_region[g])
            if not ts:
                continue
            blocks = _components(ts, nbrs)
            expected = len(set(comp[g] for g in members))
            if blocks > 1:
                raw_split += 1
            if blocks > expected:
                adj_split += 1
        integrity["n_groups"] = int(len(np.unique(group_labels)))
        integrity["n_split_groups_raw"] = raw_split
        integrity["n_split_groups_component_adjusted"] = adj_split
    else:
        integrity["n_groups"] = None
        integrity["n_split_groups_raw"] = 0
        integrity["n_split_groups_component_adjusted"] = 0

    # unassigned core tiles, against the ORIGINAL input union (same test for
    # both layouts; note mosaic internally uses its own, possibly morphed, union)
    if study_union is not None:
        from shapely.strtree import STRtree

        polys = result.tiling_result.polygons
        tree = STRtree([study_union])
        core = []
        for t in range(m):
            poly = polys[t]
            if len(tree.query(poly)) == 0:
                continue
            inter = poly.intersection(study_union).area
            if poly.area > 0 and inter / poly.area >= min_overlap_frac:
                core.append(t)
        integrity["n_core_tiles"] = len(core)
        integrity["n_unassigned_core_tiles"] = sum(1 for t in core if t not in p.region_of_tile)
    else:
        integrity["n_core_tiles"] = None
        integrity["n_unassigned_core_tiles"] = None

    # enclosed unassigned tiles: unassigned cells all of whose lattice
    # neighbours are assigned (core status deliberately ignored)
    occupied = set(p.region_of_tile)
    enclosed = 0
    for t in range(m):
        if t in occupied:
            continue
        nb = nbrs[t]
        if nb and all(x in occupied for x in nb):
            enclosed += 1
    integrity["n_enclosed_unassigned_tiles"] = enclosed

    out["integrity"] = integrity

    # ---- 6. silhouette ---------------------------------------------------
    # reference 2 (cross-layout comparable, the headline): ORIGINAL input union
    # reference 1 (internal fidelity, NOT cross-layout comparable): the
    #   footprint the layout actually tiled against
    if study_union is not None and occ:
        polys = result.tiling_result.polygons
        occ_polys = [polys[t] for t in occ]
        occ_centres = p.tile_centers[occ]
        out["silhouette_vs_original"] = silhouette_metrics(occ_polys, occ_centres, study_union)
        if working_union is not None:
            out["silhouette_vs_working"] = silhouette_metrics(occ_polys, occ_centres, working_union)
            out["silhouette_working_is_original"] = False
        else:
            out["silhouette_vs_working"] = out["silhouette_vs_original"]
            out["silhouette_working_is_original"] = True
    else:
        out["silhouette_vs_original"] = {}
        out["silhouette_vs_working"] = {}
        out["silhouette_working_is_original"] = True

    return out


def build_study_union(gdf):
    return unary_union(list(gdf.geometry))
