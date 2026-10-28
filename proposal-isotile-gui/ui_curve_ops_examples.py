"""Concrete cases for the page: the editor operations of the old GUI on U and S curves (see symmetry_compare.py)."""
import os, sys
sys.path.insert(0, os.environ["GUI_SRC"]); sys.path.insert(0, os.path.dirname(__file__))
from tactile import EdgeShape
from isohedral_tiling_ui.utils.symmetry import enforce_curve_symmetry
import editor_model as em

def fmt(c): return [tuple(round(float(v), 3) for v in p) for p in c]

u = [(0, 0), (0.2, 0.1), (0.5, 0.15), (0.8, 0.1), (1, 0)]
print("U curve, 5 points:", fmt(u))
ins = list(u); ins.insert(2, (0.35, 0.2))   # double click at x = 0.35, as _on_double_tap inserts it
print("  GUI add node at (0.35, 0.2):  ", fmt(enforce_curve_symmetry(ins, EdgeShape.U)), "<- 5 points, the middle node is gone")
print("  model add node (pair):         ", fmt(em.add_node(em._tup(u), "U", 0.35, 0.2)))
r = list(u); r.pop(1)
print("  GUI remove node 1:            ", fmt(enforce_curve_symmetry(r, EdgeShape.U)))
print("  model remove node 1 (pair):    ", fmt(em.remove_node(em._tup(u), "U", 1)))
s = [(0, 0), (0.2, 0.1), (0.5, 0), (0.8, -0.1), (1, 0)]
ins = list(s); ins.insert(2, (0.35, 0.2))
print("S curve, 5 points:", fmt(s))
print("  GUI add node at (0.35, 0.2):  ", fmt(enforce_curve_symmetry(ins, EdgeShape.S)))
print("  model add node (pair):         ", fmt(em.add_node(em._tup(s), "S", 0.35, 0.2)))
ins = list(s); ins.insert(3, (0.65, 0.2))
print("  GUI add node at (0.65, 0.2) (second half):", fmt(enforce_curve_symmetry(ins, EdgeShape.S)))
