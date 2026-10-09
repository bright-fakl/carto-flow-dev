# Produces before/after PNGs of the two documentation examples that use the "Hispanic or Latino"
# column (proportional partitions of the states; partitions on a flow cartogram), plus
# table_hispanic.md with the national totals and top/bottom five states by share.
# "Before" substitutes the old White-alone column (old_hispanic_white_alone.csv, next to this
# script) for the bundled column; "after" uses the bundled data as is.
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import carto_flow.data as examples
import carto_flow.flow_cartogram as flow
import carto_flow.proportional_cartogram as pc
from carto_flow.proportional_cartogram.visualization import plot_partitions

HERE = Path(__file__).resolve().parent
COL = "Hispanic or Latino"
OLD = pd.read_csv(HERE / "old_hispanic_white_alone.csv", dtype={"STATE": str}).set_index("STATE")[
    "Hispanic or Latino (White alone)"
]
PALETTE = {"Black or African American": "indigo", "Asian": "darkorchid", COL: "plum"}


def load(version, **kw):
    gdf = examples.load_us_census(population=True, race=True, **kw)
    if version == "before":
        gdf[COL] = gdf["STATE"].map(OLD)
        gdf[f"{COL} %"] = gdf[COL] / gdf["Total Race"]
    return gdf


def proportional_example(version):
    gdf = load(version, simplify=1000)
    part = pc.partition_geometries(
        gdf,
        columns=["Black or African American", "Asian", COL],
        method="split",
        direction="horizontal",
        alternate=True,
        normalization="row",
    )
    res = pc.plot_partitions(part, color_by="category", edgecolor="white", palette=PALETTE)
    res.ax.axis("off")
    for _, row in gdf.iterrows():
        res.ax.text(
            row.geometry.centroid.x,
            row.geometry.centroid.y,
            row["State Abbreviation"],
            va="center",
            ha="center",
            color="white",
            fontweight="bold",
            fontsize=7,
        )
    return res.ax.figure


def partitions_on_flow(version):
    gdf = load(version)
    gdf["Minorities"] = gdf["Black or African American"] + gdf["Asian"] + gdf[COL]
    carto = flow.morph_gdf(gdf, "Minorities", options=flow.MorphOptions(grid_size=512, show_progress=False))
    part = pc.partition_geometries(
        carto.to_geodataframe(),
        columns=["Black or African American", COL, "Asian"],
        method="split",
        direction="horizontal",
        strategy="treemap",
        normalization="row",
        treemap_reference="mean",
    )
    fig, ax = plt.subplots(figsize=(12, 7))
    plot_partitions(part, color_by="category", edgecolor="white", palette=PALETTE, ax=ax)
    ax.axis("off")
    return fig


def side_by_side(fn, name, title):
    fig, axes = plt.subplots(1, 2, figsize=(20, 7))
    for ax, version in zip(axes, ("before", "after")):
        f = fn(version)
        f.canvas.draw()
        ax.imshow(f.canvas.buffer_rgba())
        ax.axis("off")
        ax.set_title(f"{version}: {'White alone' if version == 'before' else 'all races'}")
        plt.close(f)
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(HERE / name, dpi=110)
    plt.close(fig)


def tables():
    lines = []
    old = load("before", contiguous_only=False)
    new = load("after", contiguous_only=False)
    for label, g in (("old (White alone)", old), ("new (all races)", new)):
        g50 = g[g["State Name"] != "Puerto Rico"]
        lines.append(
            f"- {label}: {int(g[COL].sum()):,} incl. Puerto Rico ({g[COL].sum() / g['Total Race'].sum():.1%}); "
            f"{int(g50[COL].sum()):,} for the 50 states and DC ({g50[COL].sum() / g50['Total Race'].sum():.1%})"
        )
    lines.append("")
    for label, g in (("old", old), ("new", new)):
        s = g.set_index("State Name")[f"{COL} %"].sort_values(ascending=False)
        top = ", ".join(f"{n} {v:.1%}" for n, v in s.head(5).items())
        bot = ", ".join(f"{n} {v:.1%}" for n, v in s.tail(5)[::-1].items())
        lines.append(f"- {label} top five: {top}")
        lines.append(f"- {label} bottom five: {bot}")
    (HERE / "table_hispanic.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    tables()
    side_by_side(proportional_example, "proportional_partitions.png", "Distribution of minority groups (gallery example)")
    side_by_side(partitions_on_flow, "partitions_on_flow.png", "Partitions on a flow cartogram (how-to)")
