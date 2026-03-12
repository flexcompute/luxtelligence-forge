from .utils import place_edge_couplers  # noqa: F401
from .technology import lnoi400
from . import component

__version__ = "1.4.0"

component_names = tuple(sorted(n for n in dir(component) if not n.startswith("_")))


def plot_cross_section(technology=None):
    import photonforge as pf

    if technology is None:
        technology = lnoi400(include_substrate=True, include_top_opening=True)

    c = pf.Component("Extrusion test", technology)
    c.add(
        "LN_RIDGE",
        pf.Rectangle(center=(0, 0), size=(60, 1)),
        "LN_SLAB",
        pf.Rectangle(center=(-15, 0), size=(30, 8)),
        "TL",
        pf.Rectangle(center=(0, 5), size=(60, 5)),
        pf.Rectangle(center=(0, -5), size=(60, 5)),
        "LN_SLAB",
        pf.stencil.linear_taper(30, (8, 1)),
        "SLAB_NEGATIVE",
        pf.Rectangle(center=(15, 0), size=(30, 8)),
    )

    ax = pf.tidy3d_plot(c, x=25)
    ax.set(title=c.technology.name)

    # Add annotations
    # kwargs = {"arrowprops": {"arrowstyle": "-", "color": "black", "linewidth": 1}}
    #
    # ax.text(0, 0.5, "E200", ha="center")
    # ax.text(10, 0.5, "E600", ha="center")
    # ax.text(20, 0.5, "E1700", ha="center")
    #
    # ax.text(-10, 1, "Met1", ha="center")
    # ax.text(-10, 2.5, "Met2", ha="center")
    # ax.annotate("Iso", (-6, 0.2), (-5, 0.5), **kwargs)

    return ax
