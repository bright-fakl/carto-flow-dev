import sys, numpy as np, os
d=os.path.dirname(os.path.abspath(__file__))+"/out/"
ds="county"
a=np.load(d+sys.argv[1]+f"_{ds}.npz"); bv=a["valid"]; v=a["v"]
cell=float(sys.argv[3]) if len(sys.argv)>3 else 4.3e3
for name in sys.argv[1:2]+[sys.argv[2]]:
    z=np.load(d+name+f"_{ds}.npz"); T=v/v[bv].sum()*z["area"][bv].sum(); e=np.abs(z["area"]-T)/T*100
    big=bv&(T>=5*cell**2)
    print(f"{name:12s} baseline-valid n={bv.sum()} mean {e[bv].mean():.2f} med {np.median(e[bv]):.3f} >10 {int((e[bv]>10).sum())} | T>=5 cells n={big.sum()} mean {e[big].mean():.2f} med {np.median(e[big]):.3f} p95 {np.percentile(e[big],95):.2f} max {e[big].max():.1f} >10 {int((e[big]>10).sum())} >5 {int((e[big]>5).sum())}")
