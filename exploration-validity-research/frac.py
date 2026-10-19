"""Final step fraction of the step controller per level, baseline vs validated windows (fixed schedule)."""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, harness, vwd as vw
import carto_flow.flow_cartogram.algorithm as alg
from carto_flow.flow_cartogram import stepsize
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
m, dt = sys.argv[1], float(sys.argv[2])
if m.startswith("vw"): alg.VW_HOOK = vw.VW(check_every=int(m[2:]))
inst = []; orig = stepsize.StepController.update
def upd(self, le, score):
    orig(self, le, score)
    if not inst or inst[-1][0] is not self: inst.append([self, []])
    inst[-1][1].append((self.fraction, float((np.sign(le) != 0).mean())))
stepsize.StepController.update = upd
gdf, v = harness.load("county")
w = CartogramWorkflow(gdf, "v", validate=False)
w.morph_multiresolution(min_resolution="auto", levels="auto", options=[MorphOptions(area_scale=1e-6, n_iter=k, show_progress=False, stall_patience=None, dt=dt) for k in (600, 150, 400)])
for li, (o, hist) in enumerate(inst):
    fr = [h[0] for h in hist]
    print(f"{m} dt{dt} level {li+1}: iterations {len(fr)} step fraction at start {fr[0]:.3f}, at 25%/50%/75%/end: {fr[len(fr)//4]:.3f} {fr[len(fr)//2]:.3f} {fr[3*len(fr)//4]:.3f} {fr[-1]:.3f}")
