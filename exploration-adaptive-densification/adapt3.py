import warnings,time,sys; warnings.filterwarnings("ignore")
sys.path.insert(0,"/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad")
import numpy as np, shapely, geopandas as gpd
from scipy.spatial import cKDTree
import carto_flow.data as data
import adapt as A, adapt2 as B

def ring_need(co,cell,c,alpha):
    """segments needing subdivision in a ring: stretch criterion (length > c*cell) and local-width criterion (length > alpha * local feature size)."""
    n=len(co)-1
    L=np.hypot(*np.diff(co,axis=0).T)
    need=np.maximum(np.ceil(L/(c*cell)).astype(int),1)
    if alpha and n>6:
        pts=co[:-1]; tree=cKDTree(pts); k=min(12,n)
        d,idx=tree.query(pts,k=k)
        gap=np.abs(idx-np.arange(n)[:,None]); gap=np.minimum(gap,n-gap)
        d=np.where(gap>3,d,np.inf); lfs_v=d.min(axis=1)
        lfs_s=np.minimum(lfs_v,np.roll(lfs_v,-1))
        lfs_s=np.where(np.isfinite(lfs_s),lfs_s,np.inf)
        need=np.maximum(need,np.ceil(L/(alpha*lfs_s)).astype(int))
    return need

def adaptive_lfs(g_in,outs,cell,c,alpha):
    geos=np.array(g_in.geometry.values,dtype=object)
    needs=None
    for lv in outs:
        cur=[]
        for g in lv:
            for r in A.rings(g): cur.append(ring_need(np.asarray(r.coords),cell,c,alpha))
        needs=cur if needs is None else [np.maximum(a,b) for a,b in zip(needs,cur)]
    key_need={}; k=0
    for gi in geos:
        for ri in A.rings(gi):
            ci=np.asarray(ri.coords); nn=needs[k]; k+=1
            for s in np.flatnonzero(nn>1):
                a=tuple(ci[s]); b=tuple(ci[s+1]); key=(a,b) if a<b else (b,a)
                if key_need.get(key,1)<nn[s]: key_need[key]=int(min(nn[s],200))
    def build(ring):
        cc=np.asarray(ring.coords); out=[cc[0]]
        for s in range(len(cc)-1):
            a=tuple(cc[s]); b=tuple(cc[s+1]); key=(a,b) if a<b else (b,a); n=key_need.get(key,1)
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
    outs,cell=B.pilot(cty)
    for c,alpha in ((1.0,0.0),(1.0,1.0),(1.0,0.5),(0.5,0.5)):
        g2=adaptive_lfs(cty,outs,cell,c,alpha); A.run(g2,label=f"adaptive stretch c={c}, width alpha={alpha}")
