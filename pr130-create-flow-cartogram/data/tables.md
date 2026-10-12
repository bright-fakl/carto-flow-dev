| input | call | result | largest bounds difference to the deprecated call |
|---|---|---|---|
| states | `morph_gdf` (deprecated) | converged, 112 it, grid 256, mean 0.204 / max 0.79 % | |
| states | `create_flow_cartogram` | converged, 112 it, grid 256, mean 0.204 / max 0.79 % | 0 |
| states | `multiresolution_morph(min_resolution=128, levels=4)` (deprecated) | converged, 63 it, grid 128, mean 1.607 / max 9.18 % | |
| states | `create_flow_cartogram` with `LadderSpec(128, 4)` | converged, 63 it, grid 128, mean 1.607 / max 9.18 % | 0 |
| states | `create_flow_cartogram` with `grid="auto"` | converged, 63 it, grid 128, mean 1.607 / max 9.18 % | |
| districts | `morph_gdf` (deprecated) | converged, 145 it, grid 256, mean 1.417 / max 9.76 % | |
| districts | `create_flow_cartogram` | converged, 145 it, grid 256, mean 1.417 / max 9.76 % | 0 |
| districts | `multiresolution_morph(min_resolution=128, levels=4)` (deprecated) | converged, 123 it, grid 128, mean 0.769 / max 9.05 % | |
| districts | `create_flow_cartogram` with `LadderSpec(128, 4)` | converged, 123 it, grid 128, mean 0.769 / max 9.05 % | 0 |
| districts | `create_flow_cartogram` with `grid="auto"` | converged, 123 it, grid 128, mean 0.769 / max 9.05 % | |
