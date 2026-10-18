import warnings,time,sys; warnings.filterwarnings("ignore")
import geopandas as gpd, numpy as np, shapely
import carto_flow.data as data
from carto_flow.geo_utils import densify_coverage
from carto_flow.flow_cartogram import MorphOptions, create_flow_cartogram, LadderSpec
cty=data.load_us_census(level="county",race=True)
st=data.load_us_census(); di=data.load_us_census(level="congressional_district")
rng=np.random.default_rng(0)
def ln(n,s): return np.exp(rng.normal(0,s,n))
sets={}
dc=densify_coverage(cty,max_segment_length=1000); dd=densify_coverage(di,max_segment_length=1000)
sets["states pop"]=(st,st["Population"].to_numpy(float))
sets["districts pop"]=(dd,dd["Population"].to_numpy(float))
sets["districts lognormal1"]=(dd,ln(len(dd),1.0)); sets["districts lognormal2"]=(dd,ln(len(dd),2.0))
sets["counties pop"]=(dc,dc["Population"].to_numpy(float)); sets["counties white"]=(dc,dc["White"].to_numpy(float))
sets["counties lognormal1"]=(dc,ln(len(dc),1.0))
for name,(g,v) in sets.items():
    gdf=g[["geometry"]].copy(); gdf["v"]=v
    for start in ("auto",64,128,256,512):
        t=time.time()
        try:
            spec=LadderSpec("auto","auto") if start=="auto" else LadderSpec(start,int(np.log2(2048/start))+1)
            c=create_flow_cartogram(gdf,"v",options=MorphOptions(grid=spec,area_scale=1e-6,n_iter=1000,show_progress=False))
        except Exception as e:
            print(name,start,"ERR",str(e)[:80]); continue
        o=np.array(c.get_geometry(),dtype=object); a=shapely.area(o); tt=v/v.sum()*a.sum(); e=abs(a-tt)/tt*100
        print(f"{name:21s} start {str(start):4s} {c.status.name:9s} {time.time()-t:5.1f}s mean {e.mean():7.2f} med {np.median(e):6.2f} p95 {np.percentile(e,95):7.1f} invalid {int((~shapely.is_valid(o)).sum())}",flush=True)
