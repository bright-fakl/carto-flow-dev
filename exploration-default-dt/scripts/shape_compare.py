"""Compare the final geometry of each run with the dt 0.2 run of the same setup (same case, grid, refresh_on_rise,
recompute_every, tolerances). Writes ../data/shape.json: key -> symmetric difference (share of total area),
mean and max vertex displacement in cells, regions whose centroid moved more than 0.5 cell, mean/max centroid shift in cells.
Reads the output geometries from the scratch directory (written by run_sweep.py and run_extra.py)."""
import glob
import json
import pickle

from common import *

import shapely


def cell_of(case, grid):
    g, col, sc, extra, _ = load_case("states" if case == "states_mr" else case)
    o = options_for(grid, 10, sc, extra, 0.2, 0.01, None, False)
    if case == "states_mr":
        from carto_flow.flow_cartogram.workflow import CartogramWorkflow

        o0 = MorphOptions(show_progress=False, stall_patience=None, n_iter=10, recompute_every=10, area_scale=sc)
        wf = CartogramWorkflow(g, col, None, None, o0)
        wf.morph_multiresolution(min_resolution=grid, levels=2, options=o0)
        return float(wf.results[1].grid.dx)
    return float(morph_gdf(g, col, options=o).grid.dx)


def main():
    shapes = {}
    for f in glob.glob(os.path.join(SCRATCH, "shapes", "*.pkl")):
        if "landmarks" in f:
            continue
        shapes.update(pickle.load(open(f, "rb")))
    out, cells = {}, {}
    for k, wkb in shapes.items():
        p = k.split("|")
        if k.startswith("pipeline"):
            _, case, dt, rr = p
            ref = f"pipeline|{case}|0.2|{rr}"
            case_cell = (case, 512)
        elif k.startswith("presets"):
            _, case, preset, dt = p
            ref = None
            continue
        else:
            case, grid, dt, rr, rre, tight = p
            ref = f"{case}|{grid}|0.2|{rr}|{rre}|{tight}"
            case_cell = (case, int(grid))
        if float(dt) == 0.2 or ref not in shapes:
            continue
        if case_cell not in cells:
            cells[case_cell] = cell_of(*case_cell) if not k.startswith("pipeline") else None
        if k.startswith("pipeline"):
            if ("pipeline", case) not in cells:
                g, col, sc, _, _ = load_case(case)
                o = MorphOptions(show_progress=False, n_iter=10, grid_size=512, area_scale=sc)
                cells[("pipeline", case)] = float(morph_gdf(g, col, options=o).grid.dx)
            cell = cells[("pipeline", case)]
        else:
            cell = cells[case_cell]
        A = shapely.from_wkb(shapes[ref])
        B = shapely.from_wkb(wkb)
        sd = float(sum(shapely.symmetric_difference(shapely.make_valid(a), shapely.make_valid(b)).area for a, b in zip(A, B)) / sum(shapely.area(A)))
        ca, cb = shapely.get_coordinates(A), shapely.get_coordinates(B)
        d = np.hypot(*(ca - cb).T) / cell
        cc = np.hypot(*(shapely.get_coordinates(shapely.centroid(A)) - shapely.get_coordinates(shapely.centroid(B))).T) / cell
        out[k] = dict(symdiff=sd, vdisp_mean=float(d.mean()), vdisp_max=float(d.max()), cent_gt05=int((cc > 0.5).sum()),
                      cent_mean=float(cc.mean()), cent_max=float(cc.max()), cell=cell)
    json.dump(out, open(os.path.join(DATA, "shape.json"), "w"), indent=0)
    print(len(out), "comparisons")


if __name__ == "__main__":
    main()
