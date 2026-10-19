"""Statistics of the crossing segments at window ends (baseline dynamics, no repair): stretch, region shrink."""
import sys, os, time; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, harness, xing
import carto_flow.flow_cartogram.algorithm as alg

class Diag:
    def __init__(self): self.S=None; self.dts=[]; self.rows=[]; self.n=0
    def reset(self): self.S=None
    def start_window(self, fg): self.S=fg.coords.copy(); self.n+=1
    def record(self, dt): self.dts.append(dt)
    def mark_best(self, fg): pass
    def restore(self, fg, c): pass
    def repair(self, fg, grid, vx, vy, bs, step):
        if self.S is None: return bs
        E=fg.coords; offs=np.asarray(fg.ragged_offsets[0],dtype=np.int64)
        g=xing.Grid(E,offs,6.0); flag=g.crossing()
        first=g.first; S=self.S
        ls=np.hypot(*(S[first+1]-S[first]).T); le=np.hypot(*(E[first+1]-E[first]).T)
        rho=le/np.maximum(ls,1e-12)
        self.rows.append((step, flag.sum(), rho[flag].copy(), rho.copy() if self.n<3 else None, np.flatnonzero(flag)))
        return bs
h=Diag(); alg.VW_HOOK=h
harness.run("county",1000,"diag")
tot=sum(r[1] for r in h.rows); print("windows",len(h.rows),"windows with crossings",sum(r[1]>0 for r in h.rows),"flagged segments total",tot)
allr=np.concatenate([r[2] for r in h.rows if r[1]>0])
print("stretch rho of flagged segments quantiles", np.quantile(allr,[0,.05,.25,.5,.75,.95,1]))
for r in h.rows[:3]:
    if r[3] is not None: print("all-segment rho quantiles at window", r[0], np.quantile(r[3],[0,.01,.05,.25,.5,.75,.95,.99,1]))
print([ (r[0], int(r[1])) for r in h.rows])
