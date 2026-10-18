import warnings,re; warnings.filterwarnings("ignore")
import numpy as np, shapely, geopandas as gpd
import carto_flow.data as data
from carto_flow.geo_utils import densify_coverage
from carto_flow.flow_cartogram import MorphOptions, create_flow_cartogram
cty=data.load_us_census(level="county"); g=densify_coverage(cty,max_segment_length=1000).reset_index(drop=True)
v=g["Population"].to_numpy(float)
c=create_flow_cartogram(g[["geometry"]].assign(v=v),"v",options=MorphOptions(grid="auto",area_scale=1e-6,n_iter=1000,show_progress=False))
o=np.array(c.get_geometry(),dtype=object); inv=np.flatnonzero(~shapely.is_valid(o))
gr=c.grid; cell=max(gr.dx,gr.dy); print("grid",gr.sx,"cell km",cell/1e3,"invalid",len(inv))
a=shapely.area(o); t=v/v.sum()*a.sum(); orig=shapely.area(np.array(g.geometry.values,dtype=object))
rows=[]
for i in inv:
    reason=shapely.is_valid_reason(o[i]); m=re.search(r"\[([\d.\-e+]+) ([\d.\-e+]+)\]",reason)
    P=np.array([float(m.group(1)),float(m.group(2))])
    best=(1e99,0,0)
    for p in shapely.get_parts(o[i]):
        for ring in (p.exterior,*p.interiors):
            cc=np.asarray(ring.coords); seg=np.diff(cc,axis=0); L=np.hypot(*seg.T)
            mid=(cc[:-1]+cc[1:])/2; d=np.hypot(*(mid-P).T); j=int(d.argmin())
            if d[j]<best[0]: best=(d[j],L[j],L.max())
    rows.append((g["County Name"].iloc[i][:24] if "County Name" in g else i, t[i]/cell**2, a[i]/orig[i], best[1]/cell, best[2]/cell, shapely.get_num_coordinates(o[i])))
rows.sort(key=lambda r:-r[3])
print("county                  target cells  area/orig  seg at crossing /cell  longest seg /cell  vertices")
for r in rows[:15]: print(f"{r[0]:24s} {r[1]:9.2f} {r[2]:9.2f} {r[3]:12.2f} {r[4]:16.2f} {r[5]:9d}")
arr=np.array([[r[1],r[2],r[3],r[4]] for r in rows])
print("medians: target cells %.2f, area/orig %.2f, segment at crossing/cell %.3f, longest seg/cell %.2f"%tuple(np.median(arr,axis=0)))
print("share with segment at crossing > 1 cell: %.0f%%, > 0.25 cell: %.0f%%; target<1 cell: %.0f%%; area growth>3x: %.0f%%"%(100*(arr[:,2]>1).mean(),100*(arr[:,2]>0.25).mean(),100*(arr[:,0]<1).mean(),100*(arr[:,1]>3).mean()))
