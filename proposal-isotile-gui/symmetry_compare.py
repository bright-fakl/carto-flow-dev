"""The GUI's own symmetry rule (utils/symmetry.py enforce_curve_symmetry) against isotile.enforce_symmetry, on the
curves the editor produces, and the edit operations of the curve editor expressed with isotile.

Part 1: curves in the form the editor stores (full curve with both end points; S always with the midpoint (0.5, 0); U with
or without the midpoint), a random first half (x may exceed 0.5), then both functions: same result?
Part 2: the editor's operations (move node, add node, remove node) applied by the GUI code path and by the model of
editor_model.py, on random curves: same curve?

Run: python symmetry_compare.py > symmetry_compare.txt     (GUI_SRC set)
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.environ["GUI_SRC"])
sys.path.insert(0, os.path.dirname(__file__))
from isotile import enforce_symmetry  # noqa: E402
from tactile import EdgeShape  # noqa: E402
from isohedral_tiling_ui.utils.symmetry import enforce_curve_symmetry  # noqa: E402
import editor_model as em  # noqa: E402

rng = np.random.default_rng(3)
SHAPE = {"J": EdgeShape.J, "U": EdgeShape.U, "S": EdgeShape.S}


def ui_curve(shape: str, k: int, midpoint: bool) -> list[tuple[float, float]]:
    """k points in the first half after (0, 0), as the editor stores them."""
    first = [(0.0, 0.0)] + [(float(rng.uniform(-0.2, 0.8)), float(rng.uniform(-0.4, 0.4))) for _ in range(k)]
    if shape == "S":
        mid = [(0.5, 0.0)]
        second = [(1 - x, -y) for x, y in reversed(first)]
    else:
        mid = [(0.5, float(rng.uniform(-0.3, 0.3)))] if midpoint else []
        second = [(1 - x, y) for x, y in reversed(first)]
    return first + mid + second if (shape == "S" or midpoint) else first + second


print("== part 1: enforce_curve_symmetry (GUI) against enforce_symmetry (isotile) ==")
for shape in ("J", "U", "S"):
    for midpoint in (True, False):
        if shape != "U" and not midpoint:
            continue
        same = total = 0
        worst = 0.0
        for _ in range(500):
            k = int(rng.integers(0, 6))
            c = ui_curve(shape, k, midpoint)
            # a drag moves editable first-half points only; the symmetric part is left stale
            m = len(c)
            moved = [list(p) for p in c]
            for i in range(1, m // 2):
                moved[i] = [moved[i][0] + rng.normal(0, 0.1), moved[i][1] + rng.normal(0, 0.1)]
            a = np.array(enforce_curve_symmetry([tuple(p) for p in moved], SHAPE[shape]))
            b = enforce_symmetry(moved, shape)
            total += 1
            if a.shape == b.shape:
                d = float(np.abs(a - b).max())
                worst = max(worst, d)
                same += d < 1e-12
            else:
                worst = max(worst, float("inf"))
        print(f"{shape} midpoint={midpoint!s:5}: same curve in {same} of {total}, largest difference {worst:.3g}")

# the difference cases
print("\nU curve whose midpoint was moved in x (the table lets x vary; the GUI fixes x = 0.5 only if it is already 0.5):")
c = [(0, 0), (0.2, 0.1), (0.55, 0.2), (0.8, 0.1), (1, 0)]
print("  GUI     :", [tuple(round(v, 3) for v in p) for p in enforce_curve_symmetry(c, EdgeShape.U)])
print("  isotile :", [tuple(round(float(v), 3) for v in p) for p in enforce_symmetry(c, "U")])
print("S curve with an even number of points (a node inserted on the curve without its pair):")
c = [(0, 0), (0.2, 0.1), (0.4, 0.05), (0.6, -0.05), (0.8, -0.1), (1, 0)]
print("  GUI     :", len(enforce_curve_symmetry(c, EdgeShape.S)), "points (adds the midpoint (0.5, 0))")
print("  isotile :", len(enforce_symmetry(c, "S")), "points (keeps the count, pairs by index)")

print("\n== part 2: editor operations, GUI code against editor_model ==")


def gui_add(curve, shape, click_x, click_y):
    """curve_editor.py 438 to 447 (_on_double_tap, add branch)."""
    curve = list(curve)
    insert_after = 0
    for i in range(len(curve) - 1):
        if curve[i][0] <= click_x:
            insert_after = i
    curve.insert(insert_after + 1, (click_x, click_y))
    return enforce_curve_symmetry(curve, SHAPE[shape])


def gui_remove(curve, shape, i):
    """curve_editor.py 399 to 404 (_on_double_tap, remove branch)."""
    curve = list(curve)
    curve.pop(i)
    return enforce_curve_symmetry(curve, SHAPE[shape])


def summarize(label, same, total, extra=""):
    print(f"{label}: same result in {same} of {total}{extra}")


for shape in ("J", "U", "S"):
    for midpoint in (True, False):
        if shape != "U" and not midpoint:
            continue
        same = total = 0
        counts = {"gui": [], "model": []}
        for _ in range(400):
            c = ui_curve(shape, int(rng.integers(1, 5)), midpoint)
            # a click in the first half, as the editor allows (U: x <= 0.5)
            x = float(rng.uniform(0.02, 0.48))
            y = float(rng.uniform(-0.3, 0.3))
            a = np.array(gui_add(c, shape, x, y))
            b = np.array(em.add_node(em._tup(c), shape, x, y))
            total += 1
            same += a.shape == b.shape and bool(np.abs(a - b).max() < 1e-12)
            counts["gui"].append(len(a) - len(c))
            counts["model"].append(len(b) - len(c))
        summarize(f"add node {shape} midpoint={midpoint!s:5}", same, total, f"; points added: GUI {sorted(set(counts['gui']))}, model {sorted(set(counts['model']))}")
        same = total = 0
        for _ in range(400):
            c = ui_curve(shape, int(rng.integers(2, 6)), midpoint)
            cand = [i for i in range(len(c)) if em.editable(shape, len(c), i)]
            if not cand:
                continue
            i = int(rng.choice(cand))
            a = np.array(gui_remove(c, shape, i))
            b = np.array(em.remove_node(em._tup(c), shape, i))
            total += 1
            same += a.shape == b.shape and bool(np.abs(a - b).max() < 1e-12)
        summarize(f"remove node {shape} midpoint={midpoint!s:5}", same, total)
        same = total = 0
        for _ in range(400):
            c = ui_curve(shape, int(rng.integers(1, 6)), midpoint)
            cand = [i for i in range(len(c)) if em.editable(shape, len(c), i)]
            if not cand:
                continue
            i = int(rng.choice(cand))
            x, y = rng.uniform(-0.2, 0.5), rng.uniform(-0.4, 0.4)
            if shape == "U" and abs(i - (len(c) - 1) / 2) < 1e-9:
                x = 0.5  # the editor fixes the middle node of a U curve at x = 0.5
            moved = [list(p) for p in c]
            moved[i] = [x, y]
            a = np.array(enforce_curve_symmetry([tuple(p) for p in moved], SHAPE[shape]))
            b = np.array(em.move_node(em._tup(c), shape, i, x, y))
            total += 1
            same += a.shape == b.shape and bool(np.abs(a - b).max() < 1e-12)
        summarize(f"move node {shape} midpoint={midpoint!s:5}", same, total)
