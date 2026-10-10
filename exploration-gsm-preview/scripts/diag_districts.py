"""Which districts end far from target in the GSM-style runs, and do they contain a grid cell centre initially?"""
import numpy as np
import shapely
from common import *  # noqa: F403

g, col, sc = load("districts")
vals = g[col].to_numpy(float)
b, r = baseline(g.iloc[:20], col, sc, 64, n_iter=12)
b, r = baseline(g, col, sc, 256)
grid = r.grid
X, Y = np.meshgrid(grid.x_coords, grid.y_coords)
n0 = np.array([int(shapely.contains_xy(x, X.ravel(), Y.ravel()).sum()) for x in g.geometry])
print("districts with 0 cell centres initially:", int((n0 == 0).sum()), " with <=2:", int((n0 <= 2).sum()))
for blur in (1, 2):
    out = gp.run(g.geometry, vals, grid, blur0=blur, max_pass=12)
    a = np.array([x.area for x in out["geoms"]])
    err = np.abs((a / a.sum()) / (vals / vals.sum()) - 1)
    worst = np.argsort(-err)[:5]
    print(f"blur {blur}: worst districts (idx, err %, initial cell centres, target share %):",
          [(int(i), round(100 * err[i], 1), int(n0[i]), round(100 * vals[i] / vals.sum(), 3)) for i in worst])
    print("   regions with err > 10 %:", int((err > 0.1).sum()), " of which with 0 initial centres:", int(((err > 0.1) & (n0 == 0)).sum()))
