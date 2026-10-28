"""cProfile of GridBasedLayout on the 432 congressional districts: profile_districts.py <tiling>"""
import cProfile, pstats, sys, warnings
warnings.simplefilter("ignore")
from carto_flow.data import load_us_census
from carto_flow.symbol_cartogram import create_layout
from carto_flow.symbol_cartogram.layouts.grid import GridBasedLayout
d = load_us_census(population=True, level="congressional_district").reset_index(drop=True)
pr = cProfile.Profile()
pr.enable()
create_layout(d, layout=GridBasedLayout(tiling=sys.argv[1]), show_progress=False)
pr.disable()
pstats.Stats(pr).sort_stats("tottime").print_stats(12)
