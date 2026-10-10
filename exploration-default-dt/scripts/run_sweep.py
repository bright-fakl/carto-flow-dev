"""usage: run_sweep.py <group>  appends one JSON line per run to ../data/<group>.jsonl and stores the output geometries
(WKB, for the shape comparison) in the scratch directory. Already finished keys are skipped."""
import json
import pickle
import sys

from common import *

DTS = [0.2, 0.3, 0.4, 0.5, 0.6, 0.8]
R = 0.01


def jobs(group):
    J = []  # (case, grid, dt, rr, rre, tight)
    if group == "main256":
        for case in ("states", "horiz", "tang", "tilt", "districts"):
            for dt in DTS:
                J.append((case, 256, dt, R, None, False))
    elif group == "refs256":
        for case in ("states", "horiz", "tang", "tilt", "districts"):
            for rr in (0.2, None):
                for dt in DTS:
                    J.append((case, 256, dt, rr, None, False))
    elif group == "grids":
        for grid in (128, 512):
            for dt in DTS:
                J.append(("states", grid, dt, R, None, False))
        for dt in DTS:
            J.append(("districts", 512, dt, R, None, False))
        for dt in (0.2, 0.4, 0.6):
            J.append(("states", 512, dt, None, None, False))
    elif group == "mr":
        for rr in (R, None):
            for dt in DTS:
                J.append(("states_mr", 128, dt, rr, None, False))
    elif group == "tight":
        for case in ("states", "districts"):
            for dt in DTS:
                J.append((case, 256, dt, R, None, True))
        for dt in (0.2, 0.4, 0.6):
            J.append(("states", 256, dt, None, None, True))
    elif group == "rre":
        for case in ("states", "districts", "horiz", "tang", "tilt"):
            for dt, rre in [(0.2, 5), (0.2, 20), (0.4, 5), (0.4, 20), (0.6, 5), (0.6, 20), (0.8, 5)]:
                J.append((case, 256, dt, R, rre, False))
    elif group == "fine":
        fine = [0.1, 0.15, 0.25, 0.35, 0.45, 0.55, 0.7, 1.0]
        for case in ("states", "districts", "horiz", "tang", "tilt"):
            for dt in fine:
                J.append((case, 256, dt, R, None, False))
        for case in ("states", "districts"):
            for dt in fine:
                J.append((case, 256, dt, R, None, True))
    elif group == "g1024":
        for dt in (0.2, 0.4, 0.6):
            J.append(("states", 1024, dt, R, None, False))
    elif group == "counties":
        for dt in (0.2, 0.4, 0.6, 0.8):
            J.append(("counties", 256, dt, R, None, False))
    return J


def main(group):
    out = os.path.join(DATA, f"{group}.jsonl")
    shp = os.path.join(SCRATCH, "shapes", f"{group}.pkl")
    os.makedirs(os.path.dirname(shp), exist_ok=True)
    done = set()
    if os.path.exists(out):
        done = {key_of(json.loads(l)) for l in open(out)}
    shapes = pickle.load(open(shp, "rb")) if os.path.exists(shp) else {}
    g, col, sc, extra, n0 = load_case("states")
    run_one("states", 64, 0.2, R, g=g.iloc[:30])  # numba warm-up
    for case, grid_size, dt, rr, rre, tight in jobs(group):
        gridobj = None
        if case == "states_mr":
            from carto_flow.flow_cartogram.workflow import CartogramWorkflow

            o = MorphOptions(show_progress=False, stall_patience=None, n_iter=10, recompute_every=10, area_scale=sc)
            wf = CartogramWorkflow(g, col, None, None, o)
            wf.morph_multiresolution(min_resolution=grid_size, levels=2, options=o)
            gridobj = wf.results[1].grid
        k = f"{case}|{grid_size}|{dt}|{rr}|{rre if rre else 10}|{int(tight)}"
        if k in done:
            continue
        try:
            rec, _, geoms = run_one(case, grid_size, dt, rr, rre, tight, grid=gridobj)
        except Exception as e:  # noqa
            print("ERROR", k, repr(e)[:200], flush=True)
            continue
        shapes[k] = [x.wkb for x in geoms]
        pickle.dump(shapes, open(shp, "wb"))
        open(out, "a").write(json.dumps(rec) + "\n")
        print(k, {a: (round(b, 3) if isinstance(b, float) else b) for a, b in rec.items() if a != "score"}, flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
