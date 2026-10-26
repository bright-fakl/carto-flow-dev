"""The categorical, diverging and overlay colors of the default and dark styles under simulated color vision deficiency."""
import sys, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, "/home/fakl/carto-flow/tests")
from test_style_accessibility import simulate, VISIONS, STYLES, categorical_colors, OVERLAYS, to_rgb, mpl
out = sys.argv[1]
fig, axs = plt.subplots(len(VISIONS), 2, figsize=(11, 6.6))
for j, name in enumerate(STYLES):
    st = STYLES[name]()
    div = mpl.colormaps[st.palettes.diverging]
    rows = [categorical_colors(st), [div(t)[:3] for t in np.linspace(0, 1, 10)], [to_rgb(getattr(st, o)) for o in OVERLAYS]]
    for i, v in enumerate(VISIONS):
        ax = axs[i, j]; ax.set_xlim(0, 10); ax.set_ylim(0, 3); ax.axis("off"); ax.set_facecolor(st.rc["axes.facecolor"])
        ax.add_patch(plt.Rectangle((0, 0), 10, 3, color=st.rc["axes.facecolor"]))
        for r, colors in enumerate(rows):
            for k, c in enumerate(colors):
                ax.add_patch(plt.Rectangle((k + 0.05, 2 - r + 0.1), 0.9, 0.8, color=np.clip(simulate(c, v), 0, 1)))
        ax.text(0, 3.05, f"{name}: {v or 'normal vision'}", fontsize=9, va="bottom")
fig.tight_layout(); fig.savefig(f"{out}/fig1_cvd.png", dpi=140)
