import warnings
import carto_flow.data as data
import carto_flow.flow_cartogram as flow
from carto_flow.geo_utils import densify_coverage
for name,g,col in (("states",data.load_us_census(),"Population"),("districts",data.load_us_census(level="congressional_district"),"Population"),("counties",data.load_us_census(level="county"),"Population")):
    for lab,gg in (("5 km",g),("1 km",densify_coverage(g,max_segment_length=1000))):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            flow.create_flow_cartogram(gg,col,options=flow.MorphOptions(grid="auto",area_scale=1e-6,n_iter=5,show_progress=False))
        msgs=[str(x.message)[:230] for x in w if "Vertex density" in str(x.message)]
        print(name,lab,"->",msgs[0] if msgs else "no vertex-density warning", f"[{w[0].filename.split('/')[-1]}]" if msgs else "")
