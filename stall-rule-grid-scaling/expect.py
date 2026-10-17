import warnings,sys; warnings.filterwarnings("ignore")
import geopandas as gpd, numpy as np, shapely
import carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions
from carto_flow.flow_cartogram import algorithm as alg
from carto_flow.flow_cartogram.stepsize import StepController
S="/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
cty=gpd.read_parquet(f"{S}/cty/acs_county.parquet")
st=data.load_us_census().reset_index(drop=True); di=data.load_us_census(level="congressional_district").reset_index(drop=True)
rng=np.random.default_rng(0)
cases={"AZ":(cty[cty["State Abbreviation"]=="AZ"].reset_index(drop=True),"pop",None),"states":(st,"Population",None),"districts":(di,"Population",None),
       "counties":(cty,"pop",None),"districts lognormal2":(di,"Population",("ln",2.0))}
LOG={"vm":[],"ctrl":[]}
orig_vm=alg.max_velocity_magnitude
def vm(vx,vy):
    r=orig_vm(vx,vy); LOG["vm"].append(r); return r
alg.max_velocity_magnitude=vm
orig_cur=StepController.current
def cur(self,step):
    r=orig_cur(self,step); LOG["ctrl"].append(r); return r
StepController.current=cur
def run(name,grid,n=400):
    g,col,mod=cases[name]; v=g[col].to_numpy(float)
    if mod: v=np.exp(np.random.default_rng(0).normal(0,mod[1],len(v)))
    LOG["vm"].clear(); LOG["ctrl"].clear()
    o=MorphOptions(grid=grid,grid_margin=0.5,grid_square=True,area_scale=1e-6,n_iter=n,show_progress=False,stall_patience=None,recompute_every=10,recompute_on_rise=None)
    c=alg.morph_geometries(list(g.geometry),v,options=o)
    gr=c.grid; cell=min(gr.dx,gr.dy)
    me=np.asarray(c.convergence.mean_log_errors)*np.log(2)   # natural log of area ratio, mean over regions
    k=len(me); vmraw=np.array(LOG["vm"]); ctrl=np.array(LOG["ctrl"][:k])
    # velocity raw max at each step = value at the last recompute at or before the step (recompute every 10 from step 0)
    vstep=np.array([vmraw[min(i//10,len(vmraw)-1)] for i in range(k)])
    dtau=o.dt*ctrl*cell/vstep       # expected fractional reduction per iteration (natural time)
    return me,dtau,k,c
if __name__=="__main__":
    for name,grids in (("AZ",[128,256,512,1024]),("states",[256,1024]),("districts",[256,1024]),("counties",[1024]),("districts lognormal2",[256])):
        for grid in grids:
            me,dtau,k,c=run(name,grid)
            # per window of 10 iterations: observed log-decrease of mean log error vs expected
            rows=[]
            for w in range(0,k-10,40):
                e0,e1=me[w],me[min(w+10,k-1)]
                exp_frac=1-np.exp(-dtau[w:w+10].sum()); obs_frac=(e0-e1)/e0 if e0>0 else 0
                rows.append((w,round(exp_frac,4),round(obs_frac,4)))
            print(f"{name:20s} grid {grid:5d} k={k:4d} status {c.status.name:9s} sum dtau first10 {dtau[:10].sum():.4f} | windows (start, expected frac, observed frac): {rows[:6]}",flush=True)
