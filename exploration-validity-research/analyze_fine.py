import os, numpy as np
d = os.path.dirname(os.path.abspath(__file__)) + "/out/"
for n in (200, 400, 800):
    z = {m: np.load(d + f"fine_vw1_{m}_{n}_nostall.npz") for m in ("base", "vw1", "vw10") if os.path.exists(d + f"fine_vw1_{m}_{n}_nostall.npz")}
    if len(z) < 3: continue
    v = z["base"]["v"]; I = np.all([z[m]["valid"] for m in z], axis=0)
    out = []
    for m in z:
        a = z[m]["area"]; T = v / v[I].sum() * a[I].sum(); e = (np.abs(a - T) / T * 100)[I]
        out.append(f"{m}: inv {int((~z[m]['valid']).sum())} mean {e.mean():.3f} med {np.median(e):.3f} p95 {np.percentile(e,95):.2f} >10% {int((e>10).sum())} >5% {int((e>5).sum())}")
    print(f"n={n} common valid {int(I.sum())}: " + " | ".join(out))
