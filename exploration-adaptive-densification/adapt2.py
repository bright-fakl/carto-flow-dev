import warnings,time,sys; warnings.filterwarnings("ignore")
sys.path.insert(0,"/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad")
import numpy as np, shapely, geopandas as gpd
import carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
from carto_flow.flow_cartogram.resolution import auto_start, auto_levels
import adapt as A

def pilot(g,col="Population"):
    v=g[col].to_numpy(float); gdf=g[["geometry"]].assign(v=v)
    w=CartogramWorkflow(gdf,"v",validate=False)
    w.morph_multiresolution(min_resolution="auto",levels="auto",options=MorphOptions(area_scale=1e-6,n_iter=1000,show_progress=False))
    outs=[np.array(c.get_geometry(),dtype=object) for i,c in enumerate(w) if i>0]
    return outs,max(w.last.grid.dx,w.last.grid.dy)

def seg_lengths(geoms):
    return [np.hypot(*np.diff(np.asarray(r.coords),axis=0).T) for g in geoms for r in A.rings(g)]

def adaptive_max(g_in,outs,cell,c):
    geos=np.array(g_in.geometry.values,dtype=object)
    # per ring max output length over levels
    per=[]
    for lv in outs:
        per.append(seg_lengths(lv))
    mx=[np.max([p[k] for p in per],axis=0) for k in range(len(per[0]))]
    # emulate adaptive() with provided lengths
    need={}; k=0
    for gi in geos:
        for ri in A.rings(gi):
            ci=np.asarray(ri.coords); n=np.maximum(np.ceil(mx[k]/(c*cell)).astype(int),1); k+=1
            for s in np.flatnonzero(n>1):
                a=tuple(ci[s]); b=tuple(ci[s+1]); key=(a,b) if a<b else (b,a)
                if need.get(key,1)<n[s]: need[key]=int(n[s])
    def build(ring):
        cc=np.asarray(ring.coords); out=[cc[0]]
        for s in range(len(cc)-1):
            a=tuple(cc[s]); b=tuple(cc[s+1]); key=(a,b) if a<b else (b,a); n=need.get(key,1)
            for j in range(1,n): out.append(cc[s]+(cc[s+1]-cc[s])*j/n)
            out.append(cc[s+1])
        return out
    new=[]
    for gi in geos:
        polys=[shapely.Polygon(build(p.exterior),[build(r) for r in p.interiors]) for p in shapely.get_parts(gi)]
        new.append(shapely.MultiPolygon(polys) if len(polys)>1 else polys[0])
    g2=g_in.copy(); g2["geometry"]=gpd.GeoSeries(new,index=g_in.index,crs=g_in.crs); return g2

if __name__=="__main__":
    cty=data.load_us_census(level="county").reset_index(drop=True)
    outs,cell=pilot(cty)
    for cc in (1.0,0.5,0.25):
        g2=adaptive_max(cty,outs,cell,cc); A.run(g2,label=f"adaptive, max over levels (c={cc})")
    # second round from the c=0.5 result
    g2=adaptive_max(cty,outs,cell,0.5); outs2,_=pilot(g2); g3=adaptive_max(g2,outs2,cell,0.5); A.run(g3,label="adaptive, 2 rounds (c=0.5)")
