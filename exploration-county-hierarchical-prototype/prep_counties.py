import geopandas as gpd, pandas as pd, sys
from carto_flow.geo_utils import simplify_coverage
d = sys.argv[1]
g = gpd.read_file(f"zip://{d}/cb_2020_us_county_500k.zip")
g = g[~g.STATEFP.isin(["02", "15", "72", "78", "66", "60", "69"])].to_crs("ESRI:102008")
p = pd.read_csv(f"{d}/pop.csv", encoding="latin-1", dtype={"STATE": str, "COUNTY": str})
p = p[p.SUMLEV == 50]
p["GEOID"] = p.STATE.str.zfill(2) + p.COUNTY.str.zfill(3)
g = g.merge(p[["GEOID", "CENSUS2010POP", "POPESTIMATE2020"]], on="GEOID")
g["pop"] = g.POPESTIMATE2020.astype(float)
g = g[["GEOID", "STATEFP", "NAME", "pop", "geometry"]].reset_index(drop=True)
g = simplify_coverage(g, 1000, max_segment_length=5000)
print(len(g), g["pop"].min(), g["pop"].median(), g["pop"].max(), g.geometry.is_valid.all())
g.to_parquet(f"{d}/counties_prepared.parquet")
