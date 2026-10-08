import sys, time, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "mosaic-options-sweep"))
from run_all import load_case, run, fingerprint
label = sys.argv[1]
reps = int(sys.argv[2]) if len(sys.argv) > 2 else 2
out = []
for case, budget in [("world", 800), ("world", 1500), ("districts", 0)]:
    for morph in (True, False):
        gdf, tc, gb = load_case(case, budget)
        ts = []
        for _ in range(reps):
            res, e = run(gdf, tc, gb, morph=morph)
            ts.append(e)
        rec = dict(label=label, case=case, budget=budget, morph=morph,
                   best=min(ts), times=[round(t, 2) for t in ts],
                   fp=fingerprint(res, len(gdf)))
        out.append(rec)
        print(f"[{label}] {case} b{budget} morph={int(morph)} best={min(ts):6.2f}s {rec['times']} fp={rec['fp']}", flush=True)
(HERE / f"timing_{label}.json").write_text(json.dumps(out, indent=1))
