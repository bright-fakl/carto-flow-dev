| | main | fix |
|---|---|---|
| mixed landmarks | ValueError: Point geometries are not supported as cartogram input; this operation requires polygon geometries. Convert point features to small polygons (e.g. by buffering) before passing them in. | types kept: ['Point', 'LineString', 'Polygon', 'MultiPoint'], holes kept: 1 |
| rebuild 45000 landmark vertices | n/a | 5.7 ms |
