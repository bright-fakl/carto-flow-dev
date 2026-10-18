import warnings,re,sys; warnings.filterwarnings("ignore")
sys.path.insert(0,"/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad")
import numpy as np, shapely, geopandas as gpd
import carto_flow.data as data
import adapt as A, adapt2 as B
cty=data.load_us_census(level="county").reset_index(drop=True)
outs,cell=B.pilot(cty); g2=B.adaptive_max(cty,outs,cell,0.25)
c,o=A.run(g2,label="adaptive c=0.25")
geo_in=np.array(g2.geometry.values,dtype=object); inv=np.flatnonzero(~shapely.is_valid(o))
va=cty["Population"].to_numpy(float); a=shapely.area(o); orig=shapely.area(np.array(cty.geometry.values,dtype=object)); t=va/va.sum()*a.sum()
print("reasons:",{k:int(v) for k,v in zip(*np.unique([shapely.is_valid_reason(o[i]).split('[')[0] for i in inv],return_counts=True))})
rows=[]
for i in inv:
    m=re.search(r"\[([\d.\-e+]+) ([\d.\-e+]+)\]",shapely.is_valid_reason(o[i])); P=np.array([float(m.group(1)),float(m.group(2))])
    best=None
    for pi,po in zip(shapely.get_parts(geo_in[i]),shapely.get_parts(o[i])):
        for ri,ro in zip((pi.exterior,*pi.interiors),(po.exterior,*po.interiors)):
            ci=np.asarray(ri.coords); co=np.asarray(ro.coords)
            if len(ci)!=len(co): continue
            lo=np.hypot(*np.diff(co,axis=0).T); li=np.hypot(*np.diff(ci,axis=0).T); mid=(co[:-1]+co[1:])/2; d=np.hypot(*(mid-P).T); j=int(d.argmin())
            if best is None or d[j]<best[0]: best=(d[j],lo[j],li[j],len(co),j)
    rows.append((cty["County Name"].iloc[i][:26],t[i]/cell**2,a[i]/orig[i],best[1]/cell,best[2]/1e3,best[1]/max(best[2],1e-9),best[0]/cell))
rows.sort(key=lambda r:r[3])
print("county                      target cells area/orig  out seg/cell  in seg km  elongation  dist to point/cell")
for r in rows[:12]+rows[-6:]: print(f"{r[0]:27s} {r[1]:9.1f} {r[2]:9.2f} {r[3]:11.3f} {r[4]:9.3f} {r[5]:10.2f} {r[6]:9.3f}")
arr=np.array([r[1:] for r in rows]); print("medians: target cells %.1f area/orig %.2f out seg/cell %.3f in seg km %.3f elongation %.2f"%tuple(np.median(arr[:,:5],axis=0)))
states=cty["State Abbreviation"].iloc[inv].value_counts().head(6).to_dict(); print("states:",states)
print("---- which segments cross: ring index distance between the two segments nearest the crossing point")
adj=[];far=[]
for i in inv:
    m=re.search(r"\[([\d.\-e+]+) ([\d.\-e+]+)\]",shapely.is_valid_reason(o[i])); P=np.array([float(m.group(1)),float(m.group(2))])
    best=None
    for po in shapely.get_parts(o[i]):
        for ro in (po.exterior,*po.interiors):
            co=np.asarray(ro.coords); n=len(co)-1
            # distance from P to each segment
            A_=co[:-1]; Bv=co[1:]; AB=Bv-A_; t=np.clip(np.einsum('ij,ij->i',P-A_,AB)/np.maximum(np.einsum('ij,ij->i',AB,AB),1e-18),0,1)
            d=np.hypot(*(A_+AB*t[:,None]-P).T); idx=np.argsort(d)[:2]
            cand=(d[idx[1]],idx,n,np.hypot(*AB.T)[idx])
            if best is None or cand[0]<best[0]: best=cand
    _,idx,n,L=best; gap=min(abs(idx[0]-idx[1]),n-abs(idx[0]-idx[1])); (adj if gap<=2 else far).append((gap,L/cell))
print("crossing segments adjacent in the ring (gap<=2):",len(adj)," far apart:",len(far))
print("far apart: ring-index gaps",sorted(g for g,_ in far)[:10],"... median",np.median([g for g,_ in far]) if far else None)
print("adjacent: segment lengths/cell medians",np.median([l for _,l in adj],axis=0) if adj else None)
print("---- input separation of the two crossing segments (same ring, before the morph)")
seps=[]
for i in inv:
    m=re.search(r"\[([\d.\-e+]+) ([\d.\-e+]+)\]",shapely.is_valid_reason(o[i])); P=np.array([float(m.group(1)),float(m.group(2))])
    best=None
    for pi,po in zip(shapely.get_parts(geo_in[i]),shapely.get_parts(o[i])):
        for ri,ro in zip((pi.exterior,*pi.interiors),(po.exterior,*po.interiors)):
            co=np.asarray(ro.coords); ci=np.asarray(ri.coords)
            if len(ci)!=len(co): continue
            A_=co[:-1]; Bv=co[1:]; AB=Bv-A_; t=np.clip(np.einsum('ij,ij->i',P-A_,AB)/np.maximum(np.einsum('ij,ij->i',AB,AB),1e-18),0,1)
            d=np.hypot(*(A_+AB*t[:,None]-P).T); idx=np.argsort(d)[:2]
            if best is None or d[idx[1]]<best[0]: best=(d[idx[1]],idx,ci)
    _,idx,ci=best
    s0=shapely.LineString(ci[idx[0]:idx[0]+2]); s1=shapely.LineString(ci[idx[1]:idx[1]+2])
    seps.append((shapely.distance(s0,s1),abs(idx[0]-idx[1]),shapely.length(s0),shapely.length(s1)))
seps=np.array(seps); print("input distance between the two crossing segments: m, min %.3g median %.3g max %.3g"%(seps[:,0].min(),np.median(seps[:,0]),seps[:,0].max()))
print("share touching in the input (distance < 1 m): %.0f%%, < 100 m: %.0f%%"%(100*(seps[:,0]<1).mean(),100*(seps[:,0]<100).mean()))
print("index gap of the pairs:",sorted(seps[:,1].astype(int))[:12])
