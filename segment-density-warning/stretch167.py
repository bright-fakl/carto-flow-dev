import warnings; warnings.filterwarnings("ignore")
import geopandas as gpd, numpy as np, shapely
import carto_flow.data as data
from carto_flow.geo_utils import densify_coverage
S="/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
cty=gpd.read_parquet(f"{S}/cty/acs_county.parquet")
sets={"states":(data.load_us_census(),"Population"),"districts":(data.load_us_census(level="congressional_district"),"Population"),"counties pop":(cty,"pop"),"counties white":(cty,"white"),"counties hisp":(cty,"hisp")}
def seglens(geoms):
    out=[]
    for g in geoms:
        for p in shapely.get_parts(g):
            for ring in (p.exterior,*p.interiors):
                c=np.asarray(ring.coords); out.append(np.hypot(*np.diff(c,axis=0).T))
    return out
for name,(g,col) in sets.items():
    g=g.reset_index(drop=True); v=np.maximum(g[col].to_numpy(float),1.0); geo=np.array(g.geometry.values,dtype=object)
    A=shapely.area(geo); T=v/v.sum()*A.sum(); f=np.sqrt(np.maximum(T/A,1.0))
    minx,miny,maxx,maxy=shapely.total_bounds(geo); ext=max(maxx-minx,maxy-miny)*2.0
    for G in (2048,):
        cell=ext/G
        per=[sl.max()*fi for sl,fi in zip(seglens(geo),f)]
        mx=max(np.array([s.max() for s in seglens(geo)]))
        # per region the max expected length
        reg=np.array([max(s.max() for s in seglens([x]))*fi for x,fi in zip(geo,f)])
        print(f"{name:15s} max stretch {f.max():5.1f} (95th pct {np.percentile(f,95):4.1f}) longest segment {mx/1e3:5.1f} km, finest cell {cell/1e3:4.1f} km | max expected length/cell {reg.max()/cell:6.1f}, regions above 4 cells: {(reg>4*cell).sum()} of {len(g)}; suggested segment <= {4*cell/f.max()/1e3:5.2f} km")
print("---- share of segments and of boundary length whose expected length exceeds 4 finest cells")
for name,(g,col) in sets.items():
    g=g.reset_index(drop=True); v=np.maximum(g[col].to_numpy(float),1.0); geo=np.array(g.geometry.values,dtype=object)
    A=shapely.area(geo); T=v/v.sum()*A.sum(); f=np.sqrt(np.maximum(T/A,1.0))
    minx,miny,maxx,maxy=shapely.total_bounds(geo); cell=max(maxx-minx,maxy-miny)*2.0/2048
    tot=0; flag=0; L=0.0; Lf=0.0
    for x,fi in zip(geo,f):
        for s in seglens([x]):
            e=s*fi; tot+=len(s); flag+=int((e>4*cell).sum()); L+=s.sum(); Lf+=s[e>4*cell].sum()
    print(f"{name:15s} segments flagged {100*flag/tot:5.2f} %  boundary length flagged {100*Lf/L:5.2f} %")
