import sys, pickle, warnings, os
from common import *
import geopandas as gpd
warnings.filterwarnings("ignore")
SP = "/tmp/claude-1000/-home-fakl-carto-flow/1d808732-154c-4811-8451-b398efcea29f/scratchpad/"
case, grid = sys.argv[1], int(sys.argv[2])
pols = sys.argv[3].split(",") if len(sys.argv) > 3 and sys.argv[3] != "all" else list(POLICIES)
out = SP + f"adaptive/out_{case}_{grid}.pkl"
states = data.load_us_census(population=True).reset_index(drop=True)
BAL = MorphOptions.preset_balanced().copy_with(area_scale=1e-6, n_iter=400, show_progress=False)
aniso = {"horiz": DirectionalTensor(theta=0, Dpar=4, Dperp=0.3),
         "tang": DirectionalTensor.tangential(Dpar=4, Dperp=0.3),
         "tilt": DirectionalTensor(theta=np.pi / 6, Dpar=4, Dperp=0.3)}
if case == "states":
    g, col, base = states, "Population", dict(n_iter=400)
elif case in aniso:
    g, col = states, "Population"
    base = {k: getattr(BAL, k) for k in ("dt", "Dx", "Dy", "density_mod", "mean_tol", "max_tol") if hasattr(BAL, k)}
    base.update(area_scale=1e-6, n_iter=400, anisotropy=aniso[case])
elif case == "districts":
    g, col, base = data.load_us_census(level="congressional_district").reset_index(drop=True), "Population", dict(n_iter=400)
elif case == "counties":
    g, col, base = gpd.read_parquet(SP + "counties_prepared.parquet"), "total_votes", dict(area_scale=1e-6, n_iter=int(os.environ.get("NITER", 300)))
res = {}
if os.path.exists(out):
    res = pickle.load(open(out, "rb"))
for p in pols:
    if p in res:
        continue
    r, full = run(g, col, base, p, grid=grid)
    alg_st = dict(alg.ALL_STATS[-1])
    r["score"] = score_hist(full, full.options).tolist()
    r["refresh_iters"] = alg_st["refresh_iters"]
    res[p] = r
    print(case, grid, p, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if k not in ("score", "refresh_iters")}, flush=True)
    pickle.dump(res, open(out, "wb"))
