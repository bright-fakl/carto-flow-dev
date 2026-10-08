"""Combine before/after PNGs side by side."""

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt

outdir = sys.argv[1]
for case in ("northeast", "districts_group_by", "nomorph", "states", "donut", "groups"):
    fig, axes = plt.subplots(1, 2, figsize=(18, 6))
    for ax, label in zip(axes, ("before", "after")):
        ax.imshow(mpimg.imread(f"{outdir}/{case}_{label}.png"))
        ax.set_axis_off()
    fig.suptitle(f"{case}: before (fix/mosaic-ring-swapback @ d93d7e9) vs after (fix/mosaic-enclosed-holes)", fontsize=12)
    fig.tight_layout()
    fig.savefig(f"{outdir}/{case}_before_after.png", dpi=110)
    plt.close(fig)
    print("wrote", f"{outdir}/{case}_before_after.png")
