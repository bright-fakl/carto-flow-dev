"""Where the dots of the growing region of the two-square case are after the morph (#86): inside it, inside the other region, or outside both.

    NUMBA_NUM_THREADS=8 uv run python where_are_the_dots.py
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, shapely, geopandas as gpd
import carto_flow.flow_cartogram as flow
import two_regions as tr
c=flow.create_flow_cartogram(tr.gdf,"v",landmarks=tr.landmarks,options=flow.MorphOptions(n_iter=400,show_progress=False,mean_tol=0.005,max_tol=0.01,grid=256))
fin=c.snapshots[-1]; P=np.array([[p.x,p.y] for p in fin.landmarks]); geoms=[x.buffer(0) for x in fin.geometry]
shared=geoms[0].boundary.intersection(geoms[1].boundary)
pts=shapely.points(P[tr.owner==1]); d=shapely.distance(pts,shared)/np.sqrt(geoms[1].area)
inB=shapely.contains(geoms[1],pts); inA=shapely.contains(geoms[0],pts)
edges=tr.EDGES
print("B dots by distance to the shared border: share inside B / inside A / outside both")
for a,b in zip(edges[:-1],edges[1:]):
    m=(d>=a)&(d<b)
    if m.sum(): print(f"{a:g}-{b:g}: n={m.sum():5d}  inB {inB[m].mean():.2f}  inA {inA[m].mean():.2f}  outside {(~inB[m]&~inA[m]).mean():.2f}")
# where do the dots outside both lie
out=~inB&~inA
print("outside both: n",out.sum(),"mean distance to B boundary / sqrt(area)", float(np.mean(shapely.distance(pts[out],geoms[1].boundary))/np.sqrt(geoms[1].area)))
print("B bounds",geoms[1].bounds)
