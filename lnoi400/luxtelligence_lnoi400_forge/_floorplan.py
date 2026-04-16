from typing import Literal
import warnings

import photonforge as pf
import photonforge.typing as pft


@pf.parametric_component
def chip_frame(
    *,
    x_size: pft.annotate(Literal[5000, 5050, 10000, 10100, 20000, 20200], units="μm") = 10100,
    y_size: pft.annotate(Literal[5000, 5050, 10000, 10100, 20000, 20200], units="μm") = 5050,
    center: pft.Coordinate2D = (0, 0),
    exclusion_zone_width: pft.Dimension = 50,
    technology: pf.Technology | None = None,
    name: str = "",
) -> pf.Component:
    """Chip extent and exclusion zone.

    Provide the chip extent and the exclusion zone around the chip frame.
    In the exclusion zone, only the edge-coupler routing to the chip facet
    should be placed. Allowed chip dimensions (in either direction) are
    5050 μm, 10100 μm, and 20200 μm.

    Args:
        x_size: Chip dimension in the horizontal direction.
        y_size: Chip dimension in the vertical direction.
        center: Center of the chip frame rectangle.
        exclusion_zone_width: Width of the exclusion zone close to the chip
          edges.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.

    Returns:
        Component with chip frame.
    """
    if technology is None:
        technology = pf.config.default_technology
        if "LNOI400" not in technology.name:
            warnings.warn(
                f"Current default technology {technology.name} does not seem supported by the "
                "Luxtelligence LNOI400 component library.",
                RuntimeWarning,
                1,
            )

    if x_size < 10000:
        x_size = 5050
    elif x_size < 20000:
        x_size = 10100
    else:
        x_size = 20200

    if y_size < 10000:
        y_size = 5050
    elif y_size < 20000:
        y_size = 10100
    else:
        y_size = 20200

    if x_size == 5050 and y_size == 5050:
        raise ValueError("The minimal die size is 5050 μm × 10100 μm.")

    ez = 2 * exclusion_zone_width

    return pf.Component(name, technology=technology).add(
        "CHIP_EXCLUSION_ZONE",
        pf.Rectangle(center=center, size=(x_size, y_size)),
        "CHIP_CONTOUR",
        pf.Rectangle(center=center, size=(x_size - ez, y_size - ez)),
    )
