from .utils import place_edge_couplers  # noqa: F401
from .technology import lnoi400
from . import component

__version__ = "2.1.0"

component_names = tuple(sorted(n for n in dir(component) if not n.startswith("_")))


def plot_cross_section(technology=None):
    import photonforge as pf

    if technology is None:
        technology = lnoi400()

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

    return ax
