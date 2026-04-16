import warnings

import numpy as np
import photonforge as pf
import photonforge.typing as pft

from .utils import _cpw_info


@pf.parametric_component
def cpw_pad_linear(
    *,
    cpw_spec: str | pf.PortSpec = "UniCPW",
    pad_width: pft.PositiveDimension = 80.0,
    straight_length: pft.PositiveDimension = 10.0,
    taper_length: pft.PositiveDimension = 190.0,
    technology: pf.Technology | None = None,
    name: str = "",
    model: pf.Model | None = pf.Tidy3DModel(),
) -> pf.Component:
    """RF access line for high-frequency GSG probes.

    The probe pad maintains a fixed gap/center-conductor ratio across its
    length to achieve impedance matching.

    Args:
        cpw_spec: Port specification describing the transmission line
          cross-section.
        pad_width: Width of the central conductor on the pad side.
        straight_length: Length of the straight section of the taper on the
          pad side.
        taper_length: Length of the tapered section.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Unused argument kept for API consistency.

    Returns:
        Component with the taper and port.
    """
    del model

    if technology is None:
        technology = pf.config.default_technology
        if "LNOI400" not in technology.name:
            warnings.warn(
                f"Current default technology {technology.name} does not seem supported by the "
                "Luxtelligence LNOI400 component library.",
                RuntimeWarning,
                1,
            )
    if isinstance(cpw_spec, str):
        cpw_spec = technology.ports[cpw_spec]

    c = pf.Component(name, technology=technology)
    c.properties.__thumbnail__ = "cpw-pad"

    central_width, gap, ground_width, offset, layer = _cpw_info(cpw_spec)

    scaling = pad_width / central_width
    y_max = offset + 0.5 * ground_width
    y_gnd = offset - 0.5 * ground_width
    y_sig = 0.5 * central_width
    length = straight_length + taper_length

    if scaling * y_gnd >= y_max:
        raise ValueError(
            f"'pad_width' must be less than {y_max / y_gnd * central_width} for the selected "
            f"port specification."
        )

    sig_vertices = [
        (0, -scaling * y_sig),
        (straight_length, -scaling * y_sig),
        (length, -y_sig),
        (length, y_sig),
        (straight_length, scaling * y_sig),
        (0, scaling * y_sig),
    ]

    gnd_vertices = [
        (0, scaling * y_gnd),
        (straight_length, scaling * y_gnd),
        (length, y_gnd),
        (length, y_max),
        (0, y_max),
    ]

    c.add(
        layer,
        pf.Polygon(sig_vertices),
        pf.Polygon(gnd_vertices),
        pf.Polygon([(x, -y) for x, y in gnd_vertices]),
    )

    c.add_port(pf.Port((length, 0), 180, cpw_spec, inverted=True))

    x_term = 0.5 * straight_length
    y_term = 0.5 * (scaling * y_gnd + y_max)
    sig_size = (straight_length, 2 * scaling * y_sig)
    gnd_size = (straight_length, y_max - scaling * y_gnd)
    c.add_terminal(
        {
            "G0": pf.Terminal(layer, pf.Rectangle(center=(x_term, -y_term), size=gnd_size)),
            "S": pf.Terminal(layer, pf.Rectangle(center=(x_term, 0), size=sig_size)),
            "G1": pf.Terminal(layer, pf.Rectangle(center=(x_term, y_term), size=gnd_size)),
        }
    )
    return c


def _t_rail(
    base_height: pft.PositiveDimension = 1.5,
    base_width: pft.PositiveDimension = 7.0,
    top_height: pft.PositiveDimension = 1.5,
    top_width: pft.PositiveDimension = 44.7,
    fillet_radius: pft.Dimension = 0.5,
) -> pf.Polygon:
    fillet_radius = 0.5 * min(
        2 * fillet_radius, base_height, top_height, (top_width - base_width) / 2
    )
    x0 = 0.5 * base_width
    x1 = 0.5 * top_width
    y1 = base_height + top_height
    if fillet_radius > 0:
        path = pf.Path((x0 + fillet_radius, 0), 0.1 * fillet_radius)
        if base_height > 2 * fillet_radius:
            path.arc(-90, -180, fillet_radius).segment((x0, base_height - fillet_radius)).arc(
                180, 90, fillet_radius
            )
        else:
            path.arc(-90, -270, fillet_radius)
        if x1 - x0 > 2 * fillet_radius:
            path.segment((x1 - fillet_radius, base_height))
        if top_height > 2 * fillet_radius:
            path.arc(-90, 0, fillet_radius).segment((x1, y1 - fillet_radius)).arc(
                0, 90, fillet_radius
            )
        else:
            path.arc(-90, 90, fillet_radius)
        vertices = path.spine()
        return pf.Polygon(np.vstack((vertices, vertices[::-1] * (-1, 1))))

    return pf.Polygon(
        [
            (x0, 0),
            (x0, base_height),
            (x1, base_height),
            (x1, y1),
            (-x1, y1),
            (-x1, base_height),
            (-x0, base_height),
            (-x0, 0),
        ]
    )


@pf.parametric_component
def trail_cpw(
    *,
    port_spec: str | pf.PortSpec = "UniCPW-HS",
    length: pft.PositiveDimension = 1000,
    base_height: pft.PositiveDimension = 1.5,
    base_width: pft.PositiveDimension = 7.0,
    top_height: pft.PositiveDimension = 1.5,
    top_width: pft.PositiveDimension = 44.7,
    gap: pft.PositiveDimension = 5.0,
    fillet_radius: pft.Dimension = 0.5,
    technology: pf.Technology | None = None,
    name: str = "",
    model: pf.Model | None = pf.CircuitModel(),
) -> pf.Component:
    """CPW transmission line with periodic T-rails.

    Args:
        port_spec: Port specification for the CPW transmission line.
        length: Length of the transmission line.
        base_height: T-rail base height.
        base_width: T-rail base width.
        top_height: T-rail top height.
        top_width: T-rail top width.
        gap: Gap between T-rail insertions.
        fillet_radius: pft.Dimension = 0.5,
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component.

    Returns:
        Component with the modulator, ports, and model.
    """
    c = pf.parametric.straight(port_spec=port_spec, length=length, technology=technology)
    c.parametric_function = None
    c.parametric_kwargs = None
    c.random_variables = None
    c.properties.__thumbnail__ = "tl"
    c.name = ""

    if isinstance(port_spec, str):
        port_spec = c.technology.ports[port_spec]

    central_width, tl_gap, _, _, _ = _cpw_info(port_spec)

    shape = _t_rail(base_height, base_width, top_height, top_width, fillet_radius)
    t_rail = pf.Component("T_RAIL", c.technology)
    t_rail.add((21, 0), shape, shape.copy().transform((0, tl_gap), x_reflection=True))

    period = max(base_width, top_width) + gap
    count = int(length / period)
    if count > 0:
        x = 0.5 * (length - (count - 1) * period)
        y = -0.5 * central_width - tl_gap
        spacing = (period, central_width + tl_gap)
        # TODO: Until PDA suports reference arrays, we need to dismember these
        c.add(*pf.Reference(t_rail, (x, y), columns=count, rows=2, spacing=spacing).get_repetition())

    return c
