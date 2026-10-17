import warnings; warnings.filterwarnings("ignore")
import geopandas as gpd, numpy as np, shapely
from carto_flow.flow_cartogram import MorphOptions
from carto_flow.flow_cartogram.algorithm import morph_geometries
S="/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
g=gpd.read_parquet(f"{S}/cty/acs_county.parquet"); v=g["pop"].to_numpy(float); geo=list(g.geometry)
i=int(np.flatnonzero(g.NAME=="Suffolk County, New York")[0])
c=morph_geometries(geo,v,options=MorphOptions(grid=128,grid_margin=0.5,grid_square=True,area_scale=1e-6,n_iter=1,show_progress=False,stall_patience=None,snapshot_every=1))
new=c.snapshots.get_snapshot(1).geometry[i]; old=geo[i]
print(type(old).__name__, shapely.get_num_geometries(old), shapely.get_num_coordinates(old))
print(shapely.is_valid_reason(new))
# which parts / where
import re
m=re.search(r"\[([\d.\-]+) ([\d.\-]+)\]",shapely.is_valid_reason(new)); P=shapely.Point(float(m.group(1)),float(m.group(2)))
oc=shapely.get_coordinates(old); nc=shapely.get_coordinates(new)
d=np.hypot(*(nc-P.coords[0]).T); idx=np.argsort(d)[:8]
for j in sorted(idx): print(j, np.round(oc[j]), np.round(nc[j]), "disp km", round(float(np.hypot(*(nc[j]-oc[j])))/1e3,2), "seg len next km", round(float(np.hypot(*(oc[(j+1)%len(oc)]-oc[j])))/1e3,2))
print("cell km:", 2*max(np.ptp(shapely.get_coordinates(np.array(geo,dtype=object)),axis=0))/128/1e3)
print("---- alignment check")
for part_o,part_n in zip(shapely.get_parts(old),shapely.get_parts(new)):
    ro=np.array(part_o.exterior.coords); rn=np.array(part_n.exterior.coords)
    d=rn-ro; dd=np.hypot(*np.diff(d,axis=0).T); el=np.hypot(*np.diff(ro,axis=0).T)
    print(len(ro),len(rn),"max |Δdisp|/edge:",round(float((dd/np.maximum(el,1)).max()),2),"max disp km",round(float(np.hypot(*d.T).max())/1e3,1), "edge-length range km",round(el.min()/1e3,2),round(el.max()/1e3,2))
print("---- internals")
c2=morph_geometries(geo,v,options=MorphOptions(grid=128,grid_margin=0.5,grid_square=True,area_scale=1e-6,n_iter=1,show_progress=False,stall_patience=None,snapshot_every=1,save_internals=True))
print([k for k in dir(c2) if "intern" in k.lower() or k=="grid"])
from carto_flow.flow_cartogram.displacement import displace_coords_numba, max_abs_velocity
sn=c2.internals.get_snapshot(1) if hasattr(c2.internals,"get_snapshot") else c2.internals.latest
vx,vy=sn.vx,sn.vy; gr=c2.grid
print("grid",gr.sx,gr.sy,gr.dx/1e3,"km; vmax",float(np.hypot(vx,vy).max()), "vx range",float(vx.min()),float(vx.max()))
ring=np.array(shapely.get_parts(old)[3].exterior.coords)
dt_prime=0.2*min(gr.dx,gr.dy)/max_abs_velocity(vx,vy)
new_ring=displace_coords_numba(ring,gr.x_coords,gr.y_coords,vx,vy,dt_prime,gr.dx,gr.dy,use_parallel=False)
d=new_ring-ring; print("recomputed max |Δdisp|/edge", float((np.hypot(*np.diff(d,axis=0).T)/np.maximum(np.hypot(*np.diff(ring,axis=0).T),1)).max()))
# local field variation: vx around the ring location in cell units
ix=((ring[:,0]-gr.x_coords[0])/gr.dx); iy=((ring[:,1]-gr.y_coords[0])/gr.dy); print("ring spans cells x",ix.min(),ix.max(),"y",iy.min(),iy.max())
sub=vx[int(iy.min()):int(iy.max())+2,int(ix.min()):int(ix.max())+2]; print("vx in those cells:\n",np.round(sub,3)); print("vy:\n",np.round(vy[int(iy.min()):int(iy.max())+2,int(ix.min()):int(ix.max())+2],3))
r=np.hypot(*np.diff(d,axis=0).T)/np.maximum(np.hypot(*np.diff(ring,axis=0).T),1); j=int(r.argmax())
for k in (j,j+1):
    x,y=ring[k]; fx=(x-gr.x_coords[0])/gr.dx; fy=(y-gr.y_coords[0])/gr.dy
    print(k,"pos",round(x),round(y),"cell coords",round(fx,3),round(fy,3),"disp",np.round(d[k]/1e3,2))
print("edge len km",np.hypot(*(ring[j+1]-ring[j]))/1e3)
print("---- grid consistency")
xc=gr.x_coords; print("dx",gr.dx,"spacing",np.diff(xc)[:3],"uniform:",np.allclose(np.diff(xc),gr.dx), "n",len(xc),gr.sx)
for k in (112,113):
    x=ring[k,0]; ix=int((x-xc[0])/gr.dx); tx=(x-xc[ix])/gr.dx; print(k,"ix",ix,"tx",tx)
