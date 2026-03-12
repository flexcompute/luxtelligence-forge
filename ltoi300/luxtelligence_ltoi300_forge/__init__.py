from .technology import ltoi300
from . import component

__version__ = "1.0.0.dev1"

component_names = tuple(sorted(n for n in dir(component) if not n.startswith("_")))


def plot_cross_section(technology=None):
    import photonforge as pf

    if technology is None:
        technology = ltoi300(include_substrate=True, include_beol=True)

    c = pf.Component("Extrusion test", technology)
    c.add(
        "LT_RIDGE",
        pf.Rectangle(center=(-22.5, 0), size=(0.8, 100)),
        "LT_SLAB",
        pf.Rectangle(center=(-22.5, 0), size=(3, 100)),
        "M1",
        pf.Rectangle((-20, -12), (0, 12)),
        pf.Rectangle((-40, -12), (-25, 12)),
        "M2",
        pf.Rectangle((-20, -10), (15, 10)),
        "HRL",
        pf.Rectangle((2.5, -10), (15, 10)),
        "VIA_M1_M2",
        pf.Rectangle((-17.5, -10), (-2.5, 10)),
        "VIA_M2_HRL",
        pf.Rectangle((5, -10), (12.5, 10)),
    )

    ax = pf.tidy3d_plot(c, y=0)
    ax.set(title=c.technology.name)

    # Add annotations
    # kwargs = {"arrowprops": {"arrowstyle": "-", "color": "black", "linewidth": 1}}
    #
    # ax.text(0, 0.5, "", ha="center")
    # ax.text(10, 0.5, "E600", ha="center")
    # ax.text(20, 0.5, "E1700", ha="center")
    #
    # ax.text(-10, 1, "Met1", ha="center")
    # ax.text(-10, 2.5, "Met2", ha="center")
    # ax.annotate("Iso", (-6, 0.2), (-5, 0.5), **kwargs)

    return ax
