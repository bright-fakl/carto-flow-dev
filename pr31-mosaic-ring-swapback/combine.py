"""Combine before/after PNGs side by side."""

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt

outdir = sys.argv[1]
for case in ("swapback", "greatlakes", "states", "districts_group_by", "fixture"):
    fig, axes = plt.subplots(1, 2, figsize=(18, 6))
    for ax, label in zip(axes, ("before", "after")):
        ax.imshow(mpimg.imread(f"{outdir}/{case}_{label}.png"))
        ax.set_axis_off()
    fig.suptitle(f"{case}: before (main @ 6a5de8b) vs after (fix/mosaic-ring-swapback)", fontsize=12)
    fig.tight_layout()
    fig.savefig(f"{outdir}/{case}_before_after.png", dpi=110)
    plt.close(fig)
    print("wrote", f"{outdir}/{case}_before_after.png")
