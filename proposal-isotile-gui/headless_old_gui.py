"""What can be run of the current GUI (eb7b79e) without a browser, and what it does with invalid input.

The Panel components are created in a plain Python process (no server, no websocket): their Python callbacks are called
directly the way Bokeh would call them (a change of `ColumnDataSource.data`, a slider event). Nothing here exercises the
JavaScript (`CustomJS` callbacks of the two figures), the Bokeh tools or the browser rendering.

Checked:
 1. app.py imports and builds the template (time).
 2. a slider change of IH41 (the cost of the watcher chain `_update_tiling` + both figure updates, and the preview thread).
 3. a curve drag as Python sees it (`_cp_source.data` assignment) on a preset.
 4. an invalid state: parameters outside the valid range, and a self-crossing curve: the old GUI takes both without a message.
 5. the preview render of the current code (`_render_strip_png`).

Run: python headless_old_gui.py > headless_old_gui.txt    (GUI_SRC set; carto-flow 2.0.0 checkout installed)
"""
from __future__ import annotations

import contextlib
import io
import os
import sys
import time
import warnings

warnings.simplefilter("ignore")
sys.path.insert(0, os.environ["GUI_SRC"])
import numpy as np  # noqa: E402
import panel as pn  # noqa: E402

t0 = time.perf_counter()
buf = io.StringIO()
with contextlib.redirect_stdout(buf):  # the GUI prints DEBUG lines
    import isohedral_tiling_ui.app as app  # noqa: E402
print(f"1. import of app.py and construction of the template: {time.perf_counter() - t0:.2f} s; DEBUG lines printed: {len(buf.getvalue().splitlines())}")
from isohedral_tiling_ui.components import CurveEditor, PreviewStrip, PrototileEditor  # noqa: E402

# the components that app.py created are held by the layout; make fresh ones that watch the same state
from isohedral_tiling_ui.state import TilingState  # noqa: E402

state = TilingState()
pe, ce, ps = PrototileEditor(state=state), CurveEditor(state=state), PreviewStrip(state=state)


def quiet(fn, *a, **k):
    with contextlib.redirect_stdout(io.StringIO()):
        t = time.perf_counter()
        r = fn(*a, **k)
        return (time.perf_counter() - t) * 1000, r


ms, _ = quiet(state.load_preset, "puzzle_piece")
print(f"   load_preset('puzzle_piece'): {ms:.1f} ms in the callers (preview render runs in a thread)")

state.load_preset("regular_hexagon")
quiet(state.__class__._update_tiling, state)
# 2. slider change: IH41 has 2 parameters
from isohedral_tiling_ui.components.type_selector import TileTypeSelector  # noqa: E402

sel = TileTypeSelector(state=state)
quiet(sel._on_type_select, 41)
times = []
for v in np.linspace(0.3, 0.7, 9):
    ev = type("E", (), {"new": float(v)})()
    ms, _ = quiet(pe._on_slider_change, ev, 0)
    times.append(ms)
print(f"2. slider events on IH41 (state.parameters assignment -> _update_tiling -> PrototileEditor and CurveEditor figure updates): median {np.median(times):.1f} ms, max {max(times):.1f} ms")

# 3. curve drag on a preset
quiet(state.load_preset, "wavy_square")
sid = state.active_curve_id
curve = list(state.edge_curves[sid])
times = []
for k in range(9):
    d = dict(ce._cp_source.data)
    d["y"] = [y + 0.002 * (k + 1) for y in d["y"]]
    ms, _ = quiet(ce._cp_source.__setattr__, "data", d)
    times.append(ms)
print(f"3. curve drag as Python sees it (cp_source.data assignment -> _on_curve_change -> state.edge_curves -> watchers): median {np.median(times):.1f} ms, max {max(times):.1f} ms")

# 4. invalid input
quiet(sel._on_type_select, 1)
info = state._type_info
from isotile import check_prototile  # noqa: E402

bad = None
for v in np.linspace(0, 1, 101):
    p = list(state.parameters)
    p[0] = float(v)
    if not check_prototile(1, p).valid:
        bad = p
        break
if bad is None:
    # search other types
    from isotile import get_type, tiling_types

    for n in tiling_types():
        t = get_type(n)
        if t.n_params and np.isfinite(t.safe_ranges[0][1]) and t.safe_ranges[0][1] < 1:
            quiet(sel._on_type_select, n)
            bad = list(t.default_params)
            bad[0] = t.safe_ranges[0][1] + 0.05
            break
try:
    ms, _ = quiet(setattr, state, "parameters", bad)
    print(f"4. invalid parameters {np.round(bad, 3).tolist()} for IH{state.tiling_type} (isotile: {check_prototile(state.tiling_type, bad).message}): accepted by the old GUI without a message, {ms:.1f} ms")
except Exception as e:  # pragma: no cover
    print("4. invalid parameters raised in the old GUI:", e)

quiet(state.load_preset, "puzzle_piece")
crossing = [(0, 0), (0.8, 0.5), (0.2, 0.5), (1, 0)]
cid = state.active_curve_id
curves = dict(state.edge_curves)
curves[cid] = crossing
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    ms, _ = quiet(setattr, state, "edge_curves", curves)
print(f"   self-crossing curve on shape {cid}: accepted by the old GUI ({len(w)} warnings: {sorted({str(x.message)[:60] for x in w})}); the tiles are repaired with make_valid in generate")

# 5. render
quiet(state.load_preset, "puzzle_piece")
import threading  # noqa: E402

for th in threading.enumerate():
    if th is not threading.current_thread() and th.daemon and th.name.startswith("Thread"):
        th.join(timeout=30)  # the render threads started by the state changes above
first, png = quiet(ps._render_strip_png)
second = [quiet(ps._render_strip_png)[0] for _ in range(5)]
print(f"5. PreviewStrip._render_strip_png (generate + matplotlib + PNG), puzzle_piece: first call {first:.0f} ms (imports), then median {np.median(second):.0f} ms, {len(png)} bytes")

# 6. linear modes after a preset load: the state has them, the tiling that the preview draws does not
quiet(state.load_preset, "arrow_quad")
print(f"6. after load_preset('arrow_quad'): state.edge_curve_modes = {state.edge_curve_modes}, state._tiling._edge_curve_modes = {state._tiling._edge_curve_modes} "
      f"(the preview strip and the exports draw the tiling, so the 'linear' curves are drawn as splines until the mode is toggled)")
