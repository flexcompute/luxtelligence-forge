import warnings

import photonforge as pf
import photonforge.typing as pft


@pf.parametric_component
def heater_pad(
    *,
    pad_size: pft.PositiveDimension2D = (100.0, 100.0),
    taper_length: pft.PositiveDimension = 10.0,
    contact_width: pft.PositiveDimension = 2.7,
    technology: pf.Technology | None = None,
    name: str = "",
) -> pf.Component:
    """Bonding pad for a heater.

    Args:
        pad_size: Size of the bonding pad.
        taper_length: Length of the wedge connecting the pad to the heater.
        contact_width: Width of the connection to the heater.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.

    Returns:
        Component with the bonding pad centered at the origin.
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

    c = pf.Component(name, technology=technology)
    c.properties.__thumbnail__ = "bondpad"

    x0 = 0.5 * pad_size[0]
    y0 = 0.5 * pad_size[1]
    y1 = 0.5 * (
        contact_width
        + (pad_size[1] - contact_width) * taper_length / (0.5 * pad_size[0] + taper_length)
    )
    x2 = x0 + taper_length
    y2 = 0.5 * contact_width
    polygon = pf.Polygon(
        [(x0, y0), (-x0, y0), (-x0, -y0), (x0, -y0), (x0, -y1), (x2, -y2), (x2, y2), (x0, y1)]
    )
    layer = technology.layers["HT"].layer
    c.add(layer, polygon)
    c.add_terminal(
        [
            pf.Terminal(layer, pf.Rectangle(size=pad_size)),
            pf.Terminal(layer, pf.Rectangle(center=(x2, 0), size=(0, contact_width))),
        ]
    )

    return c


@pf.parametric_component
def straight_heater(
    *,
    length: pft.PositiveDimension = 150.0,
    width: pft.PositiveDimension = 0.9,
    pad_size: pft.PositiveDimension2D = (100.0, 100.0),
    pad_pitch: pft.PositiveDimension | None = None,
    pad_offset: pft.PositiveDimension = 10.0,
    contact_width_factor: pft.PositiveFloat = 3.0,
    technology: pf.Technology | None = None,
    name: str = "",
) -> pf.Component:
    """Straight resistive wire with pads.

    Args:
        port_spec: Port specification describing waveguide cross-section.
        length: Heater wire length.
        width: Heater wire width.
        pad_size: Size of the bonding pad.
        pad_pitch: Distance between pad centers.
        pad_offset: Distance between the heater and the pads.
        contact_width_factor: Ratio between the contact and heater widths.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.

    Returns:
        Heater component.
    """
    c = pf.Component(name, technology)
    # c.properties.__thumbnail__ =

    routing_width = contact_width_factor * width
    if pad_pitch is None:
        pad_pitch = max(pad_size[0] + pad_offset, length)

    y_pad = 0.5 * width + pad_offset + 0.5 * pad_size[1]
    pad0 = pf.Rectangle(center=(0, y_pad), size=pad_size)
    pad1 = pad0.copy().translate((pad_pitch, 0))

    wire = pf.Rectangle((0, -0.5 * width), size=(length, width))

    contact0 = pf.Polygon(
        [
            (0, 0.5 * width),
            (routing_width, 0.5 * width),
            (pad0.x_max, pad0.center[1]),
            (pad0.x_min, pad0.center[1]),
        ]
    )

    shapes = [pad0, pad1, wire, contact0]

    if pad1.x_max < length:
        y_route = pad0.y_min
        route = pf.Rectangle((pad1.x_max, y_route), (length, y_route + routing_width))
        contact1 = pf.Rectangle((length - routing_width, 0), (length, y_route + routing_width))
        shapes.extend([contact1, route])
    elif pad1.x_min > length - routing_width:
        y_route = pad0.y_min
        route = pf.Rectangle((length - routing_width, y_pad), (pad1.x_min, y_pad + routing_width))
        contact1 = pf.Rectangle((length - routing_width, 0), (length, y_route + routing_width))
        shapes.extend([contact1, route])
    else:
        contact1 = pf.Polygon(
            [
                (pad1.x_max, pad1.center[1]),
                (pad1.x_min, pad1.center[1]),
                (length - routing_width, 0.5 * width),
                (length, 0.5 * width),
            ]
        )
        shapes.append(contact1)

    ht = c.technology.layers["HT"].layer
    c.add(ht, pf.boolean(shapes, [], "+")[0])

    c.add_terminal(pf.Terminal(ht, pad0), "htr_l")
    c.add_terminal(pf.Terminal(ht, pad1), "htr_r")
    return c


@pf.parametric_component
def heated_straight(
    *,
    port_spec: str | pf.PortSpec = "RWG1000",
    length: pft.PositiveDimension = 700.0,
    heater_width: pft.PositiveDimension = 1.0,
    heater_offset: pft.Coordinate = 1.22,
    pad_size: pft.PositiveDimension2D = (100.0, 100.0),
    pad_offset: pft.PositiveDimension = 10.0,
    contact_width_factor: pft.PositiveFloat = 3.0,
    draw_heater: bool = True,
    technology: pf.Technology | None = None,
    name: str = "",
    model: pf.Model | None = pf.Tidy3DModel(port_symmetries=[(1, 0)]),
) -> pf.Component:
    """Straight heated waveguide section.

    Args:
        port_spec: Port specification describing waveguide cross-section.
        length: Waveguide length.
        heater_width: Heater wire width.
        heater_offset: Offset between the heater wire and waveguide centers.
        pad_size: Size of the heater bonding pad.
        pad_offset: Distance between the heater and the pads.
        contact_width_factor: Ratio between the contact and heater widths.
        draw_heater: Flag indicating whether to include the heater.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component.

    Returns:
        Component with the waveguide, heater, ports, and model.
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
    if isinstance(port_spec, str):
        port_spec = technology.ports[port_spec]

    c = pf.Component(name, technology=technology)
    c.properties.__thumbnail__ = "to_ps"

    straight = c.add_reference(
        pf.parametric.straight(port_spec=port_spec, length=length, technology=technology)
    )

    if draw_heater:
        heater = straight_heater(
            length=length,
            width=heater_width,
            pad_size=pad_size,
            pad_offset=pad_offset,
            contact_width_factor=contact_width_factor,
            technology=technology,
        )
        heater_ref = pf.Reference(heater, (0, heater_offset))
        c.add(heater_ref)
        c.add_terminal(heater_ref["htr_l"], "htr_l")
        c.add_terminal(heater_ref["htr_r"], "htr_r")

    c.add_port(straight["P0"], "P0")
    c.add_port(straight["P1"], "P1")

    if model is not None:
        c.add_model(model)

    return c
