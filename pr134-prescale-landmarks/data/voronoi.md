| case | premorph iterations | premorph mean / max error % | Voronoi cell area error mean / max % | seconds |
|---|---|---|---|---|
| premorph=True, VoronoiOptions.prescale_components=True (cascades) | 58 | 1.3 / 8.4 | 0.0 / 0.1 | 2.2 |
| premorph=MorphOptions(prescale_components=False), Voronoi flag on (the behavior before) | 168 | 1.2 / 9.8 | 0.0 / 0.0 | 2.1 |
| premorph=True, no pre-scaling | 168 | 1.2 / 9.8 | 6.33 / 35.4 | 2.1 |
