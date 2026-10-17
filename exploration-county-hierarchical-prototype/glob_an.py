import warnings; warnings.filterwarnings("ignore")
import geopandas as gpd, numpy as np, shapely
S="/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
g=gpd.read_parquet(f"{S}/cty/counties_prepared.parquet"); pop=g["pop"].to_numpy(float)
for grid in (1024,2048):
    o=np.array(gpd.read_parquet(f"{S}/glob_{grid}_orig.parquet").geometry.values,dtype=object)
    a=shapely.area(o); t=pop/pop.sum()*a.sum(); e=abs(a-t)/t*100
    minx,miny,maxx,maxy=shapely.total_bounds(o); cell=(1.5*max(maxx-minx,maxy-miny)/grid)**2  # margin 0.5 -> grid spans 2x? approximate
    side=max(maxx-minx,maxy-miny)*2.0/grid; cells=t/side**2
    inv=~shapely.is_valid(o)
    print(grid,"err>5%:",(e>5).sum(),"err>10%:",(e>10).sum(),"err>50%:",(e>50).sum(),"| target<1 cell:",(cells<1).sum(),"| of err>10%, target<1 cell:",((e>10)&(cells<1)).sum(),"| invalid:",inv.sum(),"| invalid with err<5%:",(inv&(e<5)).sum())
    print("  invalid reasons:",{k:int(v) for k,v in zip(*np.unique([shapely.is_valid_reason(x).split('[')[0] for x in o[inv]],return_counts=True))})
