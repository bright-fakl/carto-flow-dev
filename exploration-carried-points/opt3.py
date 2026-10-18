import warnings,time,sys; warnings.filterwarnings("ignore")
import numpy as np, shapely
import carto_flow.data as data
from carto_flow.geo_utils import densify_coverage
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
seg=float(sys.argv[1]) if len(sys.argv)>1 else 500
g=data.load_us_census(level="county",max_segment_length=1000).reset_index(drop=True)
v=g["Population"].to_numpy(float); gdf=g[["geometry"]].assign(v=v)
dense=densify_coverage(g,max_segment_length=seg)
D=shapely.get_coordinates(dense.geometry.values)
print("input pts",len(shapely.get_coordinates(g.geometry.values)),"dense pts",len(D),flush=True)
def err(geoms):
    o=np.array(geoms,dtype=object); a=shapely.area(o); t=v/v.sum()*a.sum(); e=abs(a-t)/t*100
    return e.mean(),np.median(e),int((~shapely.is_valid(o)).sum())
opts=lambda: MorphOptions(area_scale=1e-6,n_iter=1000,show_progress=False)
for label,coords in (("carried",D),):
    t=time.time(); w=CartogramWorkflow(gdf,"v",coords=coords,validate=False); w.morph_multiresolution(min_resolution="auto",levels="auto",options=opts())
    c=w[-1] if hasattr(w,"__getitem__") else w.latest
    dt=time.time()-t
    print(label,f"{dt:.1f}s mean/med/invalid of morph output:",err(c.get_geometry()),flush=True)
    if coords is not None:
        for uni in (False,):
            D2=np.asarray(c.get_coords(uniform=uni))
            rebuilt=shapely.set_coordinates(dense.geometry.values.copy(),D2)
            print("  rebuilt uniform=",uni,err(rebuilt),flush=True)
