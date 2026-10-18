import warnings,time,sys; warnings.filterwarnings("ignore")
import numpy as np, shapely, geopandas as gpd
import carto_flow.data as data
from carto_flow.geo_utils import densify_coverage
from carto_flow.flow_cartogram import MorphOptions, create_flow_cartogram

def run(g,col="Population",label=""):
    v=g[col].to_numpy(float); t=time.time()
    c=create_flow_cartogram(g[["geometry"]].assign(v=v),"v",options=MorphOptions(grid="auto",area_scale=1e-6,n_iter=1000,show_progress=False))
    o=np.array(c.get_geometry(),dtype=object); a=shapely.area(o); tt=v/v.sum()*a.sum(); e=abs(a-tt)/tt*100
    nv=sum(shapely.get_num_coordinates(x) for x in g.geometry)
    print(f"{label:34s} vertices {nv:8d} {time.time()-t:5.1f}s {c.status.name:9s} mean {e.mean():6.2f} med {np.median(e):5.2f} p95 {np.percentile(e,95):6.1f} invalid {int((~shapely.is_valid(o)).sum()):3d}",flush=True)
    return c,o

def rings(geom):
    for p in shapely.get_parts(geom):
        yield p.exterior; yield from p.interiors

def adaptive(g_in,out_geoms,cell,c):
    """Insert points in every input segment whose pilot output length exceeds c * cell; shared edges get the same count."""
    need={}
    geos_in=np.array(g_in.geometry.values,dtype=object)
    for gi,go in zip(geos_in,out_geoms):
        for ri,ro in zip(rings(gi),rings(go)):
            ci=np.asarray(ri.coords); co=np.asarray(ro.coords)
            if len(ci)!=len(co): continue
            lo=np.hypot(*np.diff(co,axis=0).T)
            n=np.maximum(np.ceil(lo/(c*cell)).astype(int),1)
            for k in range(len(n)):
                if n[k]>1:
                    a=tuple(ci[k]); b=tuple(ci[k+1]); key=(a,b) if a<b else (b,a)
                    if need.get(key,1)<n[k]: need[key]=int(n[k])
    def build(ring):
        cc=np.asarray(ring.coords); out=[cc[0]]
        for k in range(len(cc)-1):
            a=tuple(cc[k]); b=tuple(cc[k+1]); key=(a,b) if a<b else (b,a); n=need.get(key,1)
            for s in range(1,n): out.append(cc[k]+(cc[k+1]-cc[k])*s/n)
            out.append(cc[k+1])
        return out
    new=[]
    for gi in geos_in:
        polys=[]
        for p in shapely.get_parts(gi):
            polys.append(shapely.Polygon(build(p.exterior),[build(r) for r in p.interiors]))
        new.append(shapely.MultiPolygon(polys) if len(polys)>1 else polys[0])
    g2=g_in.copy(); g2["geometry"]=gpd.GeoSeries(new,index=g_in.index,crs=g_in.crs); return g2

if __name__=="__main__":
    cty=data.load_us_census(level="county").reset_index(drop=True)
    c0,o0=run(cty,label="uniform 5 km (bundled)")
    cell=max(c0.grid.dx,c0.grid.dy); print("finest cell km",cell/1e3)
    for km in (2000,1000,500): run(densify_coverage(cty,max_segment_length=km),label=f"uniform {km/1000:g} km")
    for cc in (1.0,0.5,0.25):
        g2=adaptive(cty,o0,cell,cc); run(g2,label=f"adaptive from pilot (c={cc})")
