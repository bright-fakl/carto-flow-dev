# Produces gallery_before_after.png, area_vs_weight.png and prints the error table: weighted Voronoi
# cartograms of the US states with the old final-cell extraction (weights ignored) and the current
# one, plus the ExactBackend and geodesic rows with and without the accuracy gate. Run from a
# carto-flow checkout: `uv run python make_figures.py`.
import inspect
import textwrap
import warnings
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import carto_flow.data as examples
import carto_flow.voronoi_cartogram as vor
from carto_flow.voronoi_cartogram.fields import _raster

HERE = Path(__file__).resolve().parent
COL = "Population (Millions)"

us = examples.load_us_census(population=True)
w = us[COL].to_numpy(float)

# --- "before": the extraction as on main (weights not used when labeling the final grid) ---------
_new = _raster.RasterField._build_cells_upsampled
_src = textwrap.dedent(inspect.getsource(_new))
_old_lines = (
    "        use_weights = False  # weights affect target_counts only, not distance formula\n"
    "        use_offsets = self._area_eq_weight > 0.0 and self._power_offsets is not None\n"
)
_start = _src.index("        # Same assignment rule as the relaxation")
_end = _src.index("        if use_weights or use_offsets:")
_src = _src[:_start] + _old_lines + "\n" + _src[_end:]
_ns = dict(vars(_raster))
exec(_src, _ns)  # noqa: S102
_old = _ns["_build_cells_upsampled"]


def set_extraction(version):
    _raster.RasterField._build_cells_upsampled = _old if version == "before" else _new


R = vor.RasterBackend
CASES = {
    "gallery: fixed boundary": (lambda: R(resolution=256, boundary=None), dict(n_iter=300, area_cv_tol=0.05), {}),
    "gallery: ElasticBoundary(0.05)": (
        lambda: R(resolution=256, boundary=vor.ElasticBoundary(strength=0.05)),
        dict(n_iter=300, area_cv_tol=0.05),
        {},
    ),
    "gallery: circular boundary": (lambda: R(resolution=256), dict(n_iter=300, area_cv_tol=0.05), dict(boundary="circle")),
    "default settings (resolution 300, 30 iterations)": (lambda: R(), dict(), {}),
    "resolution 256, 120 iterations": (lambda: R(resolution=256), dict(n_iter=120), {}),
}


def run(version, backend, opts, kw):
    set_extraction(version)
    # "before" had no accuracy gate; max_mean_area_error_pct=None reproduces that
    gate = {"max_mean_area_error_pct": None} if version == "before" else {}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = vor.create_voronoi_cartogram(
            us, weights=COL, backend=backend, options=vor.VoronoiOptions(**opts, **gate), **kw
        )
    a = r.to_geodataframe().geometry.area.to_numpy()
    k = np.polyfit(np.log(w), np.log(a), 1)[0]
    gate_warn = [str(c.message) for c in caught if "Voronoi cell areas deviate" in str(c.message)]
    return r, a, k, gate_warn


results = {}
for name, (mk, opts, kw) in CASES.items():
    for version in ("before", "after"):
        results[name, version] = run(version, mk(), opts, kw)
        r, _, k, _ = results[name, version]
        m = r.metrics
        print(f"{name} [{version}] mean {m['mean_area_error_pct']:.1f} max {m['max_area_error_pct']:.0f} k {k:.2f}", flush=True)

# --- figure 1: maps ---------------------------------------------------------------------------
names = list(CASES)
fig, axes = plt.subplots(len(names), 2, figsize=(13, 3.6 * len(names)))
for i, name in enumerate(names):
    for j, version in enumerate(("before", "after")):
        r, _, k, _ = results[name, version]
        m = r.metrics
        gdf = r.to_geodataframe()
        gdf.plot(COL, ax=axes[i, j], cmap="RdYlGn_r", vmin=0, vmax=40, edgecolor="white", linewidth=0.3)
        axes[i, j].set_title(
            f"{name} - {version}\nmean error {m['mean_area_error_pct']:.1f} %, max {m['max_area_error_pct']:.0f} %, k = {k:.2f}",
            fontsize=9,
        )
        axes[i, j].axis("off")
plt.tight_layout()
plt.savefig(HERE / "gallery_before_after.png", dpi=90)
plt.close()

# --- figure 2: area against population, resolution 256 / 120 iterations -----------------------
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharex=True, sharey=True)
name = "resolution 256, 120 iterations"
for ax, version in zip(axes, ("before", "after")):
    _, a, k, _ = results[name, version]
    share = a / a.sum()
    ax.loglog(w / w.sum(), share, "o", ms=4)
    lim = [(w / w.sum()).min(), (w / w.sum()).max()]
    ax.loglog(lim, lim, "k--", lw=0.8, label="area share = population share")
    ax.set_title(f"{version}: k = {k:.2f}")
    ax.set_xlabel("population share")
    ax.set_ylabel("area share")
    ax.legend(fontsize=8)
plt.tight_layout()
plt.savefig(HERE / "area_vs_weight.png", dpi=100)
plt.close()

# --- table ------------------------------------------------------------------------------------
print("\n| case | mean before | max before | k before | mean after | max after | k after | converged before -> after |")
print("|---|---|---|---|---|---|---|---|")
for name in names:
    b, a_ = results[name, "before"], results[name, "after"]
    mb, ma = b[0].metrics, a_[0].metrics
    print(
        f"| {name} | {mb['mean_area_error_pct']:.1f} % | {mb['max_area_error_pct']:.0f} % | {b[2]:.2f} "
        f"| {ma['mean_area_error_pct']:.1f} % | {ma['max_area_error_pct']:.0f} % | {a_[2]:.2f} "
        f"| {mb['converged']} -> {ma['converged']} |"
    )

# --- ExactBackend and geodesic labeling: weights are ignored, so the run must not report convergence ---
print("\n| backend | mean error | max error | converged before -> after | warning |")
print("|---|---|---|---|---|")
set_extraction("after")
for label, backend, stop in [
    ("ExactBackend, area_cv_tol=1.0", vor.ExactBackend(), dict(area_cv_tol=1.0)),
    ("RasterBackend(resolution=256, distance_mode='geodesic'), tol=5000", R(resolution=256, distance_mode="geodesic"), dict(tol=5000.0)),
]:
    out = {}
    for version in ("before", "after"):
        gate = {"max_mean_area_error_pct": None} if version == "before" else {}
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            r = vor.create_voronoi_cartogram(
                us, weights=COL, backend=backend, options=vor.VoronoiOptions(n_iter=100, **stop, **gate)
            )
        out[version] = (r.metrics, [str(c.message)[:70] for c in caught if "deviate" in str(c.message)])
    mb, ma = out["before"][0], out["after"][0]
    print(
        f"| {label} | {ma['mean_area_error_pct']:.1f} % | {ma['max_area_error_pct']:.0f} % "
        f"| {mb['converged']} -> {ma['converged']} | {'yes' if out['after'][1] else 'no'} |"
    )
