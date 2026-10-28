"""Same as tree_probe.py, but fill_region is forced to outline="straight" (new isotile): separates the tile set from the offset path."""
import functools
import sys

import isotile

orig = isotile.IsohedralTiling.fill_region


@functools.wraps(orig)
def straight(self, *a, **kw):
    kw.setdefault("outline", "straight")
    return orig(self, *a, **kw)


isotile.IsohedralTiling.fill_region = straight
sys.argv = ["tree_probe.py", *sys.argv[1:]]
exec(open("/home/fakl/carto-flow-dev/isotile-adoption-pin-bump-pr/tree_probe.py").read())
