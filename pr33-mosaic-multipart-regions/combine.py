"""Combine the three variants of each figure into one panel."""
import os
import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt

out = "/tmp/mp/out"
cases = [
    "world", "world_nomorph", "malaysia", "malaysia_nomorph", "indonesia", "indonesia_nomorph",
    "newzealand", "newzealand_nomorph", "states", "states_nomorph", "michigan", "michigan_nomorph",
    "rhodeisland", "fixture", "districts_group_by", "nomorph",
]
titles = {
    "before": "before: main @ 9c664f9",
    "mid": "mid: sub-regions only, reach 8",
    "after": "after (shipping): sub-regions + reach 16",
}
made = []
for case in cases:
    paths = [f"{out}/{case}_{lb}.png" for lb in ("before", "mid", "after")]
    if not all(os.path.exists(p) for p in paths):
        print("skip", case)
        continue
    fig, axes = plt.subplots(1, 3, figsize=(24, 6))
    for ax, lb, p in zip(axes, ("before", "mid", "after"), paths):
        ax.imshow(mpimg.imread(p))
        ax.set_axis_off()
        ax.set_title(titles[lb], fontsize=11)
    fig.suptitle(case, fontsize=13)
    fig.tight_layout()
    fig.savefig(f"{out}/{case}_3way.png", dpi=100)
    plt.close(fig)
    made.append(case)
print("made", len(made), made)
