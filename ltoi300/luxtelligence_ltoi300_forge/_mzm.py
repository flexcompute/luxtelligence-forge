from collections.abc import Sequence as Sequence
from warnings import warn

import photonforge as pf
import photonforge.typing as pft

from ._cpw import TRailSpec, straight_cpw, cpw_pad, cpw_termination
from ._mmi import mmi1x2_cband, mmi1x2_oband, mmi2x2_cband, mmi2x2_oband


@pf.parametric_component
def s_bend_spline(
    *,
    port_spec: str | pf.PortSpec,
    length: pft.PositiveDimension,
    offset: pft.Coordinate,
    straight_length: pft.Dimension,
    technology: pf.Technology | None = None,
    name: str = "",
    model: pf.Model | None = pf.Tidy3DModel(),
) -> pf.Component:
    """S-bend waveguide section.

    Args:
        port_spec: Port specification describing waveguide cross-section.
        length: Horizontal extent of the bend.
        offset: Vertical offset of the bend.
        straight_length: Horizontal extent of straight segments at bend
          input and output.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component.

    Returns:
        Component with the S-bend, ports, and model.
    """
    if technology is None:
        technology = pf.config.default_technology
        if "LTOI300" not in technology.name:
            warn(
                f"Current default technology {technology.name} does not seem supported by the "
                "Luxtelligence LTOI300 component library.",
                RuntimeWarning,
                1,
            )
    if isinstance(port_spec, str):
        port_spec = technology.ports[port_spec]

    c = pf.Component(name, technology=technology)
    c.properties.__thumbnail__ = "s-bend"

    length = abs(length)
    straight_length = abs(straight_length)
    endpoint = pf.snap_to_grid((length + 2 * straight_length, offset))

    for layer, path in port_spec.get_paths((0, 0)):
        if straight_length > 0:
            path.segment((straight_length, 0))
        path.bezier([(length / 3, 0), (length * 2 / 3, offset), (length, offset)], relative=True)
        if straight_length > 0:
            path.segment(endpoint)
        c.add(layer, path)

    c.add_port(pf.Port((0, 0), 0, port_spec))
    c.add_port(pf.Port(endpoint, 180, port_spec, inverted=True))

    if model is not None:
        c.add_model(model)

    return c


@pf.parametric_component
def heated_straight(
    *,
    port_spec: pf.PortSpec,
    length: pft.PositiveDimension,
    heater_offset: pft.Coordinate,
    heater_width: pft.PositiveDimension,
    routing_width: pft.PositiveDimension,
    pad_size: pft.PositiveDimension2D,
    pad_pitch: pft.PositiveDimension | None,
    pad_offset: pft.PositiveDimension,
    via_margin: pft.Dimension,
    via_fillet_radius: pft.Dimension,
    contact_width_factor: pft.PositiveFloat,
    technology: pf.Technology | None,
    name: str = "",
) -> pf.Component:
    c = pf.parametric.straight(
        port_spec=port_spec, length=length, technology=technology, use_parametric_cache=False
    )
    c.parametric_function = None
    c.parametric_kwargs = None
    c.random_variables = None
    c.name = name

    if pad_pitch is None:
        pad_pitch = max(pad_size[0] + pad_offset, length - pad_size[0])

    y_pad = 0.5 * heater_width + pad_offset + heater_offset
    pad0 = pf.Rectangle((0, y_pad), size=pad_size)
    pad1 = pad0.copy().translate((pad_pitch, 0))

    via0 = pf.Rectangle(
        (via_margin, y_pad + via_margin),
        size=(pad_size[0] - 2 * via_margin, pad_size[1] - 2 * via_margin),
    )
    if via_fillet_radius > 0:
        via0 = via0.to_polygon().fillet(via_fillet_radius)
    via1 = via0.copy().translate((pad_pitch, 0))

    wire = pf.Rectangle((0, heater_offset - 0.5 * heater_width), size=(length, heater_width))

    x_wire = contact_width_factor * heater_width
    contact0 = pf.Polygon(
        [
            (0, heater_offset),
            (x_wire, heater_offset),
            (pad0.x_max, pad0.center[1]),
            (0, pad0.center[1]),
        ]
    )

    shapes = [pad0, pad1, wire, contact0]
    if pad1.x_max < length:
        x_wire = length - x_wire
        y_route = y_pad + 0.5 * routing_width
        contact1 = pf.Polygon(
            [
                (x_wire, heater_offset),
                (length, heater_offset),
                (length, y_route),
                (length - routing_width, y_route),
            ]
        )
        route = pf.Rectangle((pad1.x_max, y_pad), (length, y_pad + routing_width))
        shapes.extend([contact1, route])
    else:
        contact1 = pf.Polygon(
            [
                (length, pad1.center[1]),
                (pad1.x_min, pad1.center[1]),
                (length - x_wire, heater_offset),
                (length, heater_offset),
            ]
        )
        shapes.append(contact1)

    hrl_polygon = pf.boolean(shapes, [], "+")[0]

    dx = (-0.5 * contact_width_factor * heater_width, 0)
    pad0.translate(dx)
    pad1.translate(dx)
    via0.translate(dx)
    via1.translate(dx)
    hrl_polygon.translate(dx)
    c.add("M2", pad0, pad1, "VIA_M2_HRL", via0, via1, "HRL", hrl_polygon)

    m2 = c.technology.layers["M2"].layer
    c.add_terminal(pf.Terminal(m2, pad0), "htr_l")
    c.add_terminal(pf.Terminal(m2, pad1), "htr_r")
    return c


@pf.parametric_component
def optical_combiner(
    *,
    mmi: pf.Component,
    heater: pf.Component | None,
    separation: pft.PositiveDimension,
    imbalance_length: pft.Coordinate,
    mmi_connection_length: pft.Dimension,
    cpw_connection_length: pft.Dimension,
    radius: pft.PositiveDimension,
    s_bend_factor: pft.PositiveFloat,
    technology: pf.Technology | None,
    name: str = "",
):
    c = pf.Component(name, technology)
    c.properties.__thumbnail__ = "black_box"

    mmi_ref = c.add_reference(mmi)
    c.add_port(mmi_ref["P0"])
    opt_spec = c["P0"].spec

    if len(mmi.select_ports("optical")) > 3:
        top_port = mmi_ref["P2"]
        bot_port = mmi_ref["P3"]
        c.add_port(mmi_ref["P1"])
    else:
        top_port = mmi_ref["P1"]
        bot_port = mmi_ref["P2"]

    mmi_connection = pf.parametric.straight(
        port_spec=opt_spec, length=mmi_connection_length, technology=technology
    )
    top_arm = c.add_reference(mmi_connection).connect("P0", top_port)
    bot_arm = c.add_reference(mmi_connection).connect("P0", bot_port)

    s_bend_offset = 0.5 * (separation - abs(top_port.center[1] - bot_port.center[1]))
    s_bend_length = s_bend_factor * s_bend_offset
    s_bend = s_bend_spline(
        port_spec=opt_spec,
        length=s_bend_length,
        offset=s_bend_offset,
        straight_length=0,
        technology=technology,
    )
    top_arm = c.add_reference(s_bend).connect("P0", top_arm["P1"])
    bot_arm = c.add_reference(s_bend).mirror().connect("P0", bot_arm["P1"])

    if imbalance_length != 0:
        bend = pf.parametric.bend(
            port_spec=opt_spec, radius=radius, euler_fraction=1.0, technology=technology
        )
        top_arm = c.add_reference(bend).connect("P0", top_arm["P1"])
        bot_arm = c.add_reference(bend).mirror().connect("P0", bot_arm["P1"])

        imbalance = pf.parametric.straight(
            port_spec=opt_spec, length=abs(imbalance_length) / 2, technology=technology
        )
        if imbalance_length > 0:
            top_arm = c.add_reference(imbalance).connect("P0", top_arm["P1"])
        else:
            bot_arm = c.add_reference(imbalance).connect("P0", bot_arm["P1"])

        top_arm = c.add_reference(bend).mirror().connect("P0", top_arm["P1"])
        bot_arm = c.add_reference(bend).connect("P0", bot_arm["P1"])

    if heater is not None:
        top_arm = c.add_reference(heater).connect("P0", top_arm["P1"])
        bot_arm = c.add_reference(heater).mirror().connect("P0", bot_arm["P1"])
        c.add_terminal(top_arm["htr_l"], "htr_tl")
        c.add_terminal(top_arm["htr_r"], "htr_tr")
        c.add_terminal(bot_arm["htr_l"], "htr_bl")
        c.add_terminal(bot_arm["htr_r"], "htr_br")

    if imbalance_length != 0:
        top_arm = c.add_reference(bend).mirror().connect("P0", top_arm["P1"])
        bot_arm = c.add_reference(bend).connect("P0", bot_arm["P1"])

        if imbalance_length > 0:
            top_arm = c.add_reference(imbalance).connect("P0", top_arm["P1"])
        else:
            bot_arm = c.add_reference(imbalance).connect("P0", bot_arm["P1"])

        top_arm = c.add_reference(bend).connect("P0", top_arm["P1"])
        bot_arm = c.add_reference(bend).mirror().connect("P0", bot_arm["P1"])

    if cpw_connection_length > 0:
        cpw_connection = pf.parametric.straight(
            port_spec=opt_spec, length=cpw_connection_length, technology=technology
        )
        top_arm = c.add_reference(cpw_connection).connect("P0", top_arm["P1"])
        bot_arm = c.add_reference(cpw_connection).connect("P0", bot_arm["P1"])

    c.add_port((top_arm["P1"], bot_arm["P1"]))
    return c


def base_mzm(
    mmi: pf.Component,
    modulation_length: pft.PositiveDimension,
    modulation_bulge: pft.Coordinate,
    modulation_bulge_taper: pft.Dimension,
    heater_length: pft.Dimension,
    heater_width: pft.PositiveDimension,
    heater_offset: pft.Coordinate,
    heater_route_width: pft.PositiveDimension,
    heater_pad_size: pft.PositiveDimension2D,
    heater_pad_pitch: pft.PositiveDimension | None,
    heater_pad_offset: pft.PositiveDimension,
    heater_contact_factor: pft.PositiveFloat,
    imbalance_length: pft.Coordinate,
    mmi_connection_length: pft.Dimension,
    cpw_connection_length: pft.Dimension,
    radius: pft.PositiveDimension,
    s_bend_factor: pft.PositiveFloat,
    cpw_spec: str | pf.PortSpec,
    t_rail_base: pft.Dimension2D,
    t_rail_top: pft.Dimension2D,
    t_rail_gap: pft.Dimension,
    t_rail_fillet: pft.Dimension,
    cpw_pad_straight: pft.PositiveDimension,
    cpw_pad_taper: pft.PositiveDimension,
    cpw_pad_width: pft.PositiveDimension,
    cpw_pad_pitch: pft.PositiveDimension,
    cpw_pad_overlap: pft.PositiveDimension,
    cpw_pad_m2_length: pft.PositiveDimension,
    termination_resistor_length: pft.Dimension,
    termination_resistor_width: pft.PositiveDimension,
    termination_m1_length: pft.PositiveDimension,
    termination_m2_separation: pft.PositiveDimension,
    termination_m2_hrl_length: pft.PositiveDimension,
    termination_hrl_separation: pft.PositiveDimension,
    via_size: pft.PositiveDimension,
    via_gap: pft.PositiveDimension,
    via_margin: pft.Dimension,
    via_fillet: pft.Dimension,
    technology: pf.Technology | None,
    name: str,
) -> pf.Component:
    if technology is None:
        technology = pf.config.default_technology
        if "LTOI300" not in technology.name:
            warn(
                f"Current default technology {technology.name} does not seem supported by the "
                "Luxtelligence LTOI300 component library.",
                RuntimeWarning,
                3,
            )

    if isinstance(cpw_spec, str):
        cpw_spec = technology.ports[cpw_spec]

    mmi_ports = mmi.select_ports("optical")
    opt_spec = next(iter(mmi_ports.values())).spec

    t_rail = TRailSpec(
        base_width=t_rail_base[0],
        base_height=t_rail_base[1],
        top_width=t_rail_top[0],
        top_height=t_rail_top[1],
        gap=t_rail_gap,
        fillet_radius=t_rail_fillet,
    )

    cpw = straight_cpw(
        cpw_spec=cpw_spec,
        opt_spec=opt_spec,
        length=modulation_length,
        bulge_width=modulation_bulge,
        bulge_taper_length=modulation_bulge_taper,
        t_rail=t_rail,
        waveguide_position="both",
        technology=technology,
    )

    heater = None
    if heater_length > 0:
        heater = heated_straight(
            port_spec=opt_spec,
            length=heater_length,
            heater_width=heater_width,
            heater_offset=heater_offset,
            routing_width=heater_route_width,
            pad_size=heater_pad_size,
            pad_pitch=heater_pad_pitch,
            pad_offset=heater_pad_offset,
            via_margin=via_margin,
            via_fillet_radius=via_fillet,
            contact_width_factor=heater_contact_factor,
            technology=technology,
        )

    pad = cpw_pad(
        cpw_spec=cpw_spec,
        opt_spec=opt_spec,
        straight_length=cpw_pad_straight,
        taper_length=cpw_pad_taper,
        ground_pad_width=cpw_pad_width,
        pitch=cpw_pad_pitch,
        overlap_length=cpw_pad_overlap,
        m2_length=cpw_pad_m2_length,
        via_size=via_size,
        via_gap=via_gap,
        via_margin=via_margin,
        via_fillet_radius=via_fillet,
        waveguide_position="both",
        technology=technology,
    )

    termination = None
    if termination_resistor_length > 0:
        termination = cpw_termination(
            cpw_spec=cpw_spec,
            resistor_length=termination_resistor_length,
            resistor_width=termination_resistor_width,
            m1_length=termination_m1_length,
            m2_separation=termination_m2_separation,
            m2_hrl_length=termination_m2_hrl_length,
            hrl_separation=termination_hrl_separation,
            via_size=via_size,
            via_gap=via_gap,
            via_margin=via_margin,
            fillet_radius=via_fillet,
            technology=technology,
        )

    separation = abs(pad["P3"].center[1] - pad["P2"].center[1])

    comb = optical_combiner(
        mmi=mmi,
        heater=heater,
        separation=separation,
        imbalance_length=imbalance_length,
        mmi_connection_length=mmi_connection_length,
        cpw_connection_length=cpw_connection_length,
        radius=radius,
        s_bend_factor=s_bend_factor,
        technology=technology,
    )
    comb_port = "P3" if len(mmi_ports) > 3 else "P2"

    c = pf.Component(name, technology)
    c.properties.__thumbnail__ = "mzm"

    cpw_ref = c.add_reference(cpw)
    pad0 = c.add_reference(pad).connect("E0", cpw_ref["E0"])
    comb1 = c.add_reference(comb).connect(comb_port, pad0["P3"])

    c.add_terminal(pad0["signal"], "signal_l")
    c.add_terminal(pad0["gnd_b"], "gnd_tl")
    c.add_terminal(pad0["gnd_t"], "gnd1_bl")

    if termination is not None:
        c.add_reference(termination).connect("E0", cpw_ref["E1"])
        comb = optical_combiner(
            mmi=mmi,
            heater=None,
            separation=abs(cpw["P0"].center[1] - cpw["P2"].center[1]),
            imbalance_length=0,
            mmi_connection_length=mmi_connection_length,
            cpw_connection_length=cpw_connection_length,
            radius=radius,
            s_bend_factor=s_bend_factor,
            technology=technology,
        )
        comb2 = c.add_reference(comb).connect(comb_port, cpw_ref["P1"])
    else:
        pad1 = c.add_reference(pad).connect("E0", cpw_ref["E1"])
        c.add_terminal(pad1["signal"], "signal_r")
        c.add_terminal(pad1["gnd_b"], "gnd0_br")
        c.add_terminal(pad1["gnd_t"], "gnd1_tr")
        comb = optical_combiner(
            mmi=mmi,
            heater=None,
            separation=separation,
            imbalance_length=0,
            mmi_connection_length=mmi_connection_length,
            cpw_connection_length=cpw_connection_length,
            radius=radius,
            s_bend_factor=s_bend_factor,
            technology=technology,
        )
        comb2 = c.add_reference(comb).connect(comb_port, pad1["P3"])

    c.add_port(comb1["P0"])
    if len(mmi_ports) > 3:
        c.add_port(comb1["P1"])

    c.add_port(comb2["P0"])
    if len(mmi_ports) > 3:
        c.add_port(comb2["P1"])

    if heater is not None:
        for t in ("htr_bl", "htr_br", "htr_tl", "htr_tr"):
            c.add_terminal(comb1[t], t)

    return c


@pf.parametric_component
def terminated_mzm_1x2mmi_oband(
    *,
    mmi: pf.Component | None = None,
    modulation_length: pft.PositiveDimension = 5000,
    modulation_bulge: pft.Coordinate = 1.8,
    modulation_bulge_taper: pft.Dimension = 100,
    heater_length: pft.Dimension = 700,
    heater_width: pft.PositiveDimension = 2.5,
    heater_offset: pft.Coordinate = 0,
    heater_route_width: pft.PositiveDimension = 6,
    heater_pad_size: pft.PositiveDimension2D = (150, 150),
    heater_pad_pitch: pft.PositiveDimension | None = None,
    heater_pad_offset: pft.PositiveDimension = 10,
    heater_contact_factor: pft.PositiveFloat = 3,
    imbalance_length: pft.Coordinate = 100,
    mmi_connection_length: pft.Dimension = 10,
    cpw_connection_length: pft.Dimension = 75,
    radius: pft.PositiveDimension = 60,
    s_bend_factor: pft.PositiveFloat = 3.5,
    cpw_spec: str | pf.PortSpec = "UniCPW-EO-oband",
    t_rail_base: pft.Dimension2D = (53, 2.5),
    t_rail_top: pft.Dimension2D = (53, 2.5),
    t_rail_gap: pft.Dimension = 5,
    t_rail_fillet: pft.Dimension = 0.45,
    cpw_pad_straight: pft.PositiveDimension = 25,
    cpw_pad_taper: pft.PositiveDimension = 150,
    cpw_pad_width: pft.PositiveDimension = 150,
    cpw_pad_pitch: pft.PositiveDimension = 100,
    cpw_pad_overlap: pft.PositiveDimension = 45,
    cpw_pad_m2_length: pft.PositiveDimension = 80,
    termination_resistor_length: pft.Dimension = 48.5,
    termination_resistor_width: pft.PositiveDimension = 1.5,
    termination_m1_length: pft.PositiveDimension = 45,
    termination_m2_separation: pft.PositiveDimension = 10,
    termination_m2_hrl_length: pft.PositiveDimension = 20,
    termination_hrl_separation: pft.PositiveDimension = 2.5,
    via_size: pft.PositiveDimension = 12,
    via_gap: pft.PositiveDimension = 12,
    via_margin: pft.Dimension = 2.5,
    via_fillet: pft.Dimension = 1,
    technology: pf.Technology | None = None,
    name: str = "",
) -> pf.Component:
    """Terminated MZM modulator for O band using 1x2 MMI splitters.

    Args:
        mmi: MMI component used as optical splitter and combiner.
          If ``None``The PDK default is used.
        modulation_length: Length of the modulation section.
        modulation_bulge: Width added to the waveguide in the modulation
          region.
        modulation_bulge_taper: Length of the bulge transition taper.
        heater_length: Length of the heated waveguide used for bias control.
        heater_width: Width of the heater wire.
        heater_offset: Offset between the heater wire and the optical
          waveguide centers.
        heater_route_width: Width of the routing path for the heater.
        heater_pad_size: Heater pad size.
        heater_pad_pitch: Heater pad pitch.
        heater_pad_offset: Offset between the heater wire and pad edges.
        heater_contact_factor: Factor controlling the routing width at the
          wire (multiplies the wire width).
        imbalance_length: Length of an optional optical segment added to a
          single MZI arm (top, if positive, or bottom, if negative).
        mmi_connection_length: Length of the connection close to the MMIs.
        cpw_connection_length: Length of the connection close to the CPW.
        radius: Bend radius for optical waveguides.
        s_bend_factor: Ratio between length and offset for S bends.
        cpw_spec: Port specification for the CPW.
        t_rail_base: Dimensions for an optional T-rail base for the CPW.
        t_rail_top: Dimensions for an optional T-rail top for the CPW.
        t_rail_gap: Gap between adjacent T-rail insertions in the CPW.
        t_rail_fillet: Fillet radius for T-rail shapes.
        cpw_pad_straight: Length of the straight section of the CPW pad.
        cpw_pad_taper: Length of the taper section of the CPW pad.
        cpw_pad_width: Width of the ground CPW pads.
        cpw_pad_pitch: CPW pad pitch.
        cpw_pad_overlap: Length of the via section of the CPW pad.
        cpw_pad_m2_length: Length of the CPW pad in M2.
        termination_resistor_length: Effective length of the CPW termination
          resistor.
        termination_resistor_width: Width of the CPW termination resistor.
        termination_m1_length: Length of the termination in M1.
        termination_m2_separation: Length of the termination in M2.
        termination_m2_hrl_length: Length of the termination in the M2/HRL
          via region.
        termination_hrl_separation: Added length for the termination in HRL.
        via_size: Dimensions of an individual via.
        via_gap: Separation between adjacent via edges.
        via_margin: Margin between vias and the surrounding region.
        via_fillet: Fillet radius for vias.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.

    Returns:
        MZM component.
    """
    if mmi is None:
        mmi = mmi1x2_oband(technology=technology)

    return base_mzm(
        mmi,
        modulation_length,
        modulation_bulge,
        modulation_bulge_taper,
        heater_length,
        heater_width,
        heater_offset,
        heater_route_width,
        heater_pad_size,
        heater_pad_pitch,
        heater_pad_offset,
        heater_contact_factor,
        imbalance_length,
        mmi_connection_length,
        cpw_connection_length,
        radius,
        s_bend_factor,
        cpw_spec,
        t_rail_base,
        t_rail_top,
        t_rail_gap,
        t_rail_fillet,
        cpw_pad_straight,
        cpw_pad_taper,
        cpw_pad_width,
        cpw_pad_pitch,
        cpw_pad_overlap,
        cpw_pad_m2_length,
        termination_resistor_length,
        termination_resistor_width,
        termination_m1_length,
        termination_m2_separation,
        termination_m2_hrl_length,
        termination_hrl_separation,
        via_size,
        via_gap,
        via_margin,
        via_fillet,
        technology,
        name,
    )


@pf.parametric_component
def unterminated_mzm_1x2mmi_oband(
    *,
    mmi: pf.Component | None = None,
    modulation_length: pft.PositiveDimension = 5000,
    modulation_bulge: pft.Coordinate = 1.8,
    modulation_bulge_taper: pft.Dimension = 100,
    heater_length: pft.Dimension = 700,
    heater_width: pft.PositiveDimension = 2.5,
    heater_offset: pft.Coordinate = 0,
    heater_route_width: pft.PositiveDimension = 6,
    heater_pad_size: pft.PositiveDimension2D = (150, 150),
    heater_pad_pitch: pft.PositiveDimension | None = None,
    heater_pad_offset: pft.PositiveDimension = 10,
    heater_contact_factor: pft.PositiveFloat = 3,
    imbalance_length: pft.Coordinate = 100,
    mmi_connection_length: pft.Dimension = 10,
    cpw_connection_length: pft.Dimension = 75,
    radius: pft.PositiveDimension = 60,
    s_bend_factor: pft.PositiveFloat = 3.5,
    cpw_spec: str | pf.PortSpec = "UniCPW-EO-oband",
    t_rail_base: pft.Dimension2D = (53, 2.5),
    t_rail_top: pft.Dimension2D = (53, 2.5),
    t_rail_gap: pft.Dimension = 5,
    t_rail_fillet: pft.Dimension = 0.45,
    cpw_pad_straight: pft.PositiveDimension = 25,
    cpw_pad_taper: pft.PositiveDimension = 150,
    cpw_pad_width: pft.PositiveDimension = 150,
    cpw_pad_pitch: pft.PositiveDimension = 100,
    cpw_pad_overlap: pft.PositiveDimension = 45,
    cpw_pad_m2_length: pft.PositiveDimension = 80,
    via_size: pft.PositiveDimension = 12,
    via_gap: pft.PositiveDimension = 12,
    via_margin: pft.Dimension = 2.5,
    via_fillet: pft.Dimension = 1,
    technology: pf.Technology | None = None,
    name: str = "",
) -> pf.Component:
    """Unterminated MZM modulator for O band using 1x2 MMI splitters.

    Args:
        mmi: MMI component used as optical splitter and combiner.
          If ``None``The PDK default is used.
        modulation_length: Length of the modulation section.
        modulation_bulge: Width added to the waveguide in the modulation
          region.
        modulation_bulge_taper: Length of the bulge transition taper.
        heater_length: Length of the heated waveguide used for bias control.
        heater_width: Width of the heater wire.
        heater_offset: Offset between the heater wire and the optical
          waveguide centers.
        heater_route_width: Width of the routing path for the heater.
        heater_pad_size: Heater pad size.
        heater_pad_pitch: Heater pad pitch.
        heater_pad_offset: Offset between the heater wire and pad edges.
        heater_contact_factor: Factor controlling the routing width at the
          wire (multiplies the wire width).
        imbalance_length: Length of an optional optical segment added to a
          single MZI arm (top, if positive, or bottom, if negative).
        mmi_connection_length: Length of the connection close to the MMIs.
        cpw_connection_length: Length of the connection close to the CPW.
        radius: Bend radius for optical waveguides.
        s_bend_factor: Ratio between length and offset for S bends.
        cpw_spec: Port specification for the CPW.
        t_rail_base: Dimensions for an optional T-rail base for the CPW.
        t_rail_top: Dimensions for an optional T-rail top for the CPW.
        t_rail_gap: Gap between adjacent T-rail insertions in the CPW.
        t_rail_fillet: Fillet radius for T-rail shapes.
        cpw_pad_straight: Length of the straight section of the CPW pad.
        cpw_pad_taper: Length of the taper section of the CPW pad.
        cpw_pad_width: Width of the ground CPW pads.
        cpw_pad_pitch: CPW pad pitch.
        cpw_pad_overlap: Length of the via section of the CPW pad.
        cpw_pad_m2_length: Length of the CPW pad in M2.
        via_size: Dimensions of an individual via.
        via_gap: Separation between adjacent via edges.
        via_margin: Margin between vias and the surrounding region.
        via_fillet: Fillet radius for vias.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.

    Returns:
        MZM component.
    """
    if mmi is None:
        mmi = mmi1x2_oband(technology=technology)

    return base_mzm(
        mmi,
        modulation_length,
        modulation_bulge,
        modulation_bulge_taper,
        heater_length,
        heater_width,
        heater_offset,
        heater_route_width,
        heater_pad_size,
        heater_pad_pitch,
        heater_pad_offset,
        heater_contact_factor,
        imbalance_length,
        mmi_connection_length,
        cpw_connection_length,
        radius,
        s_bend_factor,
        cpw_spec,
        t_rail_base,
        t_rail_top,
        t_rail_gap,
        t_rail_fillet,
        cpw_pad_straight,
        cpw_pad_taper,
        cpw_pad_width,
        cpw_pad_pitch,
        cpw_pad_overlap,
        cpw_pad_m2_length,
        0,
        0,
        0,
        0,
        0,
        0,
        via_size,
        via_gap,
        via_margin,
        via_fillet,
        technology,
        name,
    )


@pf.parametric_component
def terminated_mzm_1x2mmi_cband(
    *,
    mmi: pf.Component | None = None,
    modulation_length: pft.PositiveDimension = 5000,
    modulation_bulge: pft.Coordinate = 1.6,
    modulation_bulge_taper: pft.Dimension = 100,
    heater_length: pft.Dimension = 700,
    heater_width: pft.PositiveDimension = 2.5,
    heater_offset: pft.Coordinate = 0,
    heater_route_width: pft.PositiveDimension = 6,
    heater_pad_size: pft.PositiveDimension2D = (150, 150),
    heater_pad_pitch: pft.PositiveDimension | None = None,
    heater_pad_offset: pft.PositiveDimension = 10,
    heater_contact_factor: pft.PositiveFloat = 3,
    imbalance_length: pft.Coordinate = 100,
    mmi_connection_length: pft.Dimension = 10,
    cpw_connection_length: pft.Dimension = 75,
    radius: pft.PositiveDimension = 60,
    s_bend_factor: pft.PositiveFloat = 3.5,
    cpw_spec: str | pf.PortSpec = "UniCPW-EO-cband",
    t_rail_base: pft.Dimension2D = (53, 1.5),
    t_rail_top: pft.Dimension2D = (53, 1.5),
    t_rail_gap: pft.Dimension = 5,
    t_rail_fillet: pft.Dimension = 0.45,
    cpw_pad_straight: pft.PositiveDimension = 25,
    cpw_pad_taper: pft.PositiveDimension = 150,
    cpw_pad_width: pft.PositiveDimension = 150,
    cpw_pad_pitch: pft.PositiveDimension = 100,
    cpw_pad_overlap: pft.PositiveDimension = 45,
    cpw_pad_m2_length: pft.PositiveDimension = 80,
    termination_resistor_length: pft.Dimension = 48.5,
    termination_resistor_width: pft.PositiveDimension = 1.5,
    termination_m1_length: pft.PositiveDimension = 45,
    termination_m2_separation: pft.PositiveDimension = 10,
    termination_m2_hrl_length: pft.PositiveDimension = 20,
    termination_hrl_separation: pft.PositiveDimension = 2.5,
    via_size: pft.PositiveDimension = 12,
    via_gap: pft.PositiveDimension = 12,
    via_margin: pft.Dimension = 2.5,
    via_fillet: pft.Dimension = 1,
    technology: pf.Technology | None = None,
    name: str = "",
) -> pf.Component:
    """Terminated MZM modulator for C band using 1x2 MMI splitters.

    Args:
        mmi: MMI component used as optical splitter and combiner.
          If ``None``The PDK default is used.
        modulation_length: Length of the modulation section.
        modulation_bulge: Width added to the waveguide in the modulation
          region.
        modulation_bulge_taper: Length of the bulge transition taper.
        heater_length: Length of the heated waveguide used for bias control.
        heater_width: Width of the heater wire.
        heater_offset: Offset between the heater wire and the optical
          waveguide centers.
        heater_route_width: Width of the routing path for the heater.
        heater_pad_size: Heater pad size.
        heater_pad_pitch: Heater pad pitch.
        heater_pad_offset: Offset between the heater wire and pad edges.
        heater_contact_factor: Factor controlling the routing width at the
          wire (multiplies the wire width).
        imbalance_length: Length of an optional optical segment added to a
          single MZI arm (top, if positive, or bottom, if negative).
        mmi_connection_length: Length of the connection close to the MMIs.
        cpw_connection_length: Length of the connection close to the CPW.
        radius: Bend radius for optical waveguides.
        s_bend_factor: Ratio between length and offset for S bends.
        cpw_spec: Port specification for the CPW.
        t_rail_base: Dimensions for an optional T-rail base for the CPW.
        t_rail_top: Dimensions for an optional T-rail top for the CPW.
        t_rail_gap: Gap between adjacent T-rail insertions in the CPW.
        t_rail_fillet: Fillet radius for T-rail shapes.
        cpw_pad_straight: Length of the straight section of the CPW pad.
        cpw_pad_taper: Length of the taper section of the CPW pad.
        cpw_pad_width: Width of the ground CPW pads.
        cpw_pad_pitch: CPW pad pitch.
        cpw_pad_overlap: Length of the via section of the CPW pad.
        cpw_pad_m2_length: Length of the CPW pad in M2.
        termination_resistor_length: Effective length of the CPW termination
          resistor.
        termination_resistor_width: Width of the CPW termination resistor.
        termination_m1_length: Length of the termination in M1.
        termination_m2_separation: Length of the termination in M2.
        termination_m2_hrl_length: Length of the termination in the M2/HRL
          via region.
        termination_hrl_separation: Added length for the termination in HRL.
        via_size: Dimensions of an individual via.
        via_gap: Separation between adjacent via edges.
        via_margin: Margin between vias and the surrounding region.
        via_fillet: Fillet radius for vias.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.

    Returns:
        MZM component.
    """
    if mmi is None:
        mmi = mmi1x2_cband(technology=technology)

    return base_mzm(
        mmi,
        modulation_length,
        modulation_bulge,
        modulation_bulge_taper,
        heater_length,
        heater_width,
        heater_offset,
        heater_route_width,
        heater_pad_size,
        heater_pad_pitch,
        heater_pad_offset,
        heater_contact_factor,
        imbalance_length,
        mmi_connection_length,
        cpw_connection_length,
        radius,
        s_bend_factor,
        cpw_spec,
        t_rail_base,
        t_rail_top,
        t_rail_gap,
        t_rail_fillet,
        cpw_pad_straight,
        cpw_pad_taper,
        cpw_pad_width,
        cpw_pad_pitch,
        cpw_pad_overlap,
        cpw_pad_m2_length,
        termination_resistor_length,
        termination_resistor_width,
        termination_m1_length,
        termination_m2_separation,
        termination_m2_hrl_length,
        termination_hrl_separation,
        via_size,
        via_gap,
        via_margin,
        via_fillet,
        technology,
        name,
    )


@pf.parametric_component
def unterminated_mzm_1x2mmi_cband(
    *,
    mmi: pf.Component | None = None,
    modulation_length: pft.PositiveDimension = 5000,
    modulation_bulge: pft.Coordinate = 1.6,
    modulation_bulge_taper: pft.Dimension = 100,
    heater_length: pft.Dimension = 700,
    heater_width: pft.PositiveDimension = 2.5,
    heater_offset: pft.Coordinate = 0,
    heater_route_width: pft.PositiveDimension = 6,
    heater_pad_size: pft.PositiveDimension2D = (150, 150),
    heater_pad_pitch: pft.PositiveDimension | None = None,
    heater_pad_offset: pft.PositiveDimension = 10,
    heater_contact_factor: pft.PositiveFloat = 3,
    imbalance_length: pft.Coordinate = 100,
    mmi_connection_length: pft.Dimension = 10,
    cpw_connection_length: pft.Dimension = 75,
    radius: pft.PositiveDimension = 60,
    s_bend_factor: pft.PositiveFloat = 3.5,
    cpw_spec: str | pf.PortSpec = "UniCPW-EO-cband",
    t_rail_base: pft.Dimension2D = (53, 1.5),
    t_rail_top: pft.Dimension2D = (53, 1.5),
    t_rail_gap: pft.Dimension = 5,
    t_rail_fillet: pft.Dimension = 0.45,
    cpw_pad_straight: pft.PositiveDimension = 25,
    cpw_pad_taper: pft.PositiveDimension = 150,
    cpw_pad_width: pft.PositiveDimension = 150,
    cpw_pad_pitch: pft.PositiveDimension = 100,
    cpw_pad_overlap: pft.PositiveDimension = 45,
    cpw_pad_m2_length: pft.PositiveDimension = 80,
    via_size: pft.PositiveDimension = 12,
    via_gap: pft.PositiveDimension = 12,
    via_margin: pft.Dimension = 2.5,
    via_fillet: pft.Dimension = 1,
    technology: pf.Technology | None = None,
    name: str = "",
) -> pf.Component:
    """Unterminated MZM modulator for C band using 1x2 MMI splitters.

    Args:
        mmi: MMI component used as optical splitter and combiner.
          If ``None``The PDK default is used.
        modulation_length: Length of the modulation section.
        modulation_bulge: Width added to the waveguide in the modulation
          region.
        modulation_bulge_taper: Length of the bulge transition taper.
        heater_length: Length of the heated waveguide used for bias control.
        heater_width: Width of the heater wire.
        heater_offset: Offset between the heater wire and the optical
          waveguide centers.
        heater_route_width: Width of the routing path for the heater.
        heater_pad_size: Heater pad size.
        heater_pad_pitch: Heater pad pitch.
        heater_pad_offset: Offset between the heater wire and pad edges.
        heater_contact_factor: Factor controlling the routing width at the
          wire (multiplies the wire width).
        imbalance_length: Length of an optional optical segment added to a
          single MZI arm (top, if positive, or bottom, if negative).
        mmi_connection_length: Length of the connection close to the MMIs.
        cpw_connection_length: Length of the connection close to the CPW.
        radius: Bend radius for optical waveguides.
        s_bend_factor: Ratio between length and offset for S bends.
        cpw_spec: Port specification for the CPW.
        t_rail_base: Dimensions for an optional T-rail base for the CPW.
        t_rail_top: Dimensions for an optional T-rail top for the CPW.
        t_rail_gap: Gap between adjacent T-rail insertions in the CPW.
        t_rail_fillet: Fillet radius for T-rail shapes.
        cpw_pad_straight: Length of the straight section of the CPW pad.
        cpw_pad_taper: Length of the taper section of the CPW pad.
        cpw_pad_width: Width of the ground CPW pads.
        cpw_pad_pitch: CPW pad pitch.
        cpw_pad_overlap: Length of the via section of the CPW pad.
        cpw_pad_m2_length: Length of the CPW pad in M2.
        via_size: Dimensions of an individual via.
        via_gap: Separation between adjacent via edges.
        via_margin: Margin between vias and the surrounding region.
        via_fillet: Fillet radius for vias.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.

    Returns:
        MZM component.
    """
    if mmi is None:
        mmi = mmi1x2_cband(technology=technology)

    return base_mzm(
        mmi,
        modulation_length,
        modulation_bulge,
        modulation_bulge_taper,
        heater_length,
        heater_width,
        heater_offset,
        heater_route_width,
        heater_pad_size,
        heater_pad_pitch,
        heater_pad_offset,
        heater_contact_factor,
        imbalance_length,
        mmi_connection_length,
        cpw_connection_length,
        radius,
        s_bend_factor,
        cpw_spec,
        t_rail_base,
        t_rail_top,
        t_rail_gap,
        t_rail_fillet,
        cpw_pad_straight,
        cpw_pad_taper,
        cpw_pad_width,
        cpw_pad_pitch,
        cpw_pad_overlap,
        cpw_pad_m2_length,
        0,
        0,
        0,
        0,
        0,
        0,
        via_size,
        via_gap,
        via_margin,
        via_fillet,
        technology,
        name,
    )


@pf.parametric_component
def terminated_mzm_2x2mmi_oband(
    *,
    mmi: pf.Component | None = None,
    modulation_length: pft.PositiveDimension = 5000,
    modulation_bulge: pft.Coordinate = 1.8,
    modulation_bulge_taper: pft.Dimension = 100,
    heater_length: pft.Dimension = 700,
    heater_width: pft.PositiveDimension = 2.5,
    heater_offset: pft.Coordinate = 0,
    heater_route_width: pft.PositiveDimension = 6,
    heater_pad_size: pft.PositiveDimension2D = (150, 150),
    heater_pad_pitch: pft.PositiveDimension | None = None,
    heater_pad_offset: pft.PositiveDimension = 10,
    heater_contact_factor: pft.PositiveFloat = 3,
    imbalance_length: pft.Coordinate = 100,
    mmi_connection_length: pft.Dimension = 10,
    cpw_connection_length: pft.Dimension = 75,
    radius: pft.PositiveDimension = 60,
    s_bend_factor: pft.PositiveFloat = 3.5,
    cpw_spec: str | pf.PortSpec = "UniCPW-EO-oband",
    t_rail_base: pft.Dimension2D = (53, 2.5),
    t_rail_top: pft.Dimension2D = (53, 2.5),
    t_rail_gap: pft.Dimension = 5,
    t_rail_fillet: pft.Dimension = 0.45,
    cpw_pad_straight: pft.PositiveDimension = 25,
    cpw_pad_taper: pft.PositiveDimension = 150,
    cpw_pad_width: pft.PositiveDimension = 150,
    cpw_pad_pitch: pft.PositiveDimension = 100,
    cpw_pad_overlap: pft.PositiveDimension = 45,
    cpw_pad_m2_length: pft.PositiveDimension = 80,
    termination_resistor_length: pft.Dimension = 48.5,
    termination_resistor_width: pft.PositiveDimension = 1.5,
    termination_m1_length: pft.PositiveDimension = 45,
    termination_m2_separation: pft.PositiveDimension = 10,
    termination_m2_hrl_length: pft.PositiveDimension = 20,
    termination_hrl_separation: pft.PositiveDimension = 2.5,
    via_size: pft.PositiveDimension = 12,
    via_gap: pft.PositiveDimension = 12,
    via_margin: pft.Dimension = 2.5,
    via_fillet: pft.Dimension = 1,
    technology: pf.Technology | None = None,
    name: str = "",
) -> pf.Component:
    """Terminated MZM modulator for O band using 2x2 MMI splitters.

    Args:
        mmi: MMI component used as optical splitter and combiner.
          If ``None``The PDK default is used.
        modulation_length: Length of the modulation section.
        modulation_bulge: Width added to the waveguide in the modulation
          region.
        modulation_bulge_taper: Length of the bulge transition taper.
        heater_length: Length of the heated waveguide used for bias control.
        heater_width: Width of the heater wire.
        heater_offset: Offset between the heater wire and the optical
          waveguide centers.
        heater_route_width: Width of the routing path for the heater.
        heater_pad_size: Heater pad size.
        heater_pad_pitch: Heater pad pitch.
        heater_pad_offset: Offset between the heater wire and pad edges.
        heater_contact_factor: Factor controlling the routing width at the
          wire (multiplies the wire width).
        imbalance_length: Length of an optional optical segment added to a
          single MZI arm (top, if positive, or bottom, if negative).
        mmi_connection_length: Length of the connection close to the MMIs.
        cpw_connection_length: Length of the connection close to the CPW.
        radius: Bend radius for optical waveguides.
        s_bend_factor: Ratio between length and offset for S bends.
        cpw_spec: Port specification for the CPW.
        t_rail_base: Dimensions for an optional T-rail base for the CPW.
        t_rail_top: Dimensions for an optional T-rail top for the CPW.
        t_rail_gap: Gap between adjacent T-rail insertions in the CPW.
        t_rail_fillet: Fillet radius for T-rail shapes.
        cpw_pad_straight: Length of the straight section of the CPW pad.
        cpw_pad_taper: Length of the taper section of the CPW pad.
        cpw_pad_width: Width of the ground CPW pads.
        cpw_pad_pitch: CPW pad pitch.
        cpw_pad_overlap: Length of the via section of the CPW pad.
        cpw_pad_m2_length: Length of the CPW pad in M2.
        termination_resistor_length: Effective length of the CPW termination
          resistor.
        termination_resistor_width: Width of the CPW termination resistor.
        termination_m1_length: Length of the termination in M1.
        termination_m2_separation: Length of the termination in M2.
        termination_m2_hrl_length: Length of the termination in the M2/HRL
          via region.
        termination_hrl_separation: Added length for the termination in HRL.
        via_size: Dimensions of an individual via.
        via_gap: Separation between adjacent via edges.
        via_margin: Margin between vias and the surrounding region.
        via_fillet: Fillet radius for vias.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.

    Returns:
        MZM component.
    """
    if mmi is None:
        mmi = mmi2x2_oband(technology=technology)

    return base_mzm(
        mmi,
        modulation_length,
        modulation_bulge,
        modulation_bulge_taper,
        heater_length,
        heater_width,
        heater_offset,
        heater_route_width,
        heater_pad_size,
        heater_pad_pitch,
        heater_pad_offset,
        heater_contact_factor,
        imbalance_length,
        mmi_connection_length,
        cpw_connection_length,
        radius,
        s_bend_factor,
        cpw_spec,
        t_rail_base,
        t_rail_top,
        t_rail_gap,
        t_rail_fillet,
        cpw_pad_straight,
        cpw_pad_taper,
        cpw_pad_width,
        cpw_pad_pitch,
        cpw_pad_overlap,
        cpw_pad_m2_length,
        termination_resistor_length,
        termination_resistor_width,
        termination_m1_length,
        termination_m2_separation,
        termination_m2_hrl_length,
        termination_hrl_separation,
        via_size,
        via_gap,
        via_margin,
        via_fillet,
        technology,
        name,
    )


@pf.parametric_component
def unterminated_mzm_2x2mmi_oband(
    *,
    mmi: pf.Component | None = None,
    modulation_length: pft.PositiveDimension = 5000,
    modulation_bulge: pft.Coordinate = 1.8,
    modulation_bulge_taper: pft.Dimension = 100,
    heater_length: pft.Dimension = 700,
    heater_width: pft.PositiveDimension = 2.5,
    heater_offset: pft.Coordinate = 0,
    heater_route_width: pft.PositiveDimension = 6,
    heater_pad_size: pft.PositiveDimension2D = (150, 150),
    heater_pad_pitch: pft.PositiveDimension | None = None,
    heater_pad_offset: pft.PositiveDimension = 10,
    heater_contact_factor: pft.PositiveFloat = 3,
    imbalance_length: pft.Coordinate = 100,
    mmi_connection_length: pft.Dimension = 10,
    cpw_connection_length: pft.Dimension = 75,
    radius: pft.PositiveDimension = 60,
    s_bend_factor: pft.PositiveFloat = 3.5,
    cpw_spec: str | pf.PortSpec = "UniCPW-EO-oband",
    t_rail_base: pft.Dimension2D = (53, 2.5),
    t_rail_top: pft.Dimension2D = (53, 2.5),
    t_rail_gap: pft.Dimension = 5,
    t_rail_fillet: pft.Dimension = 0.45,
    cpw_pad_straight: pft.PositiveDimension = 25,
    cpw_pad_taper: pft.PositiveDimension = 150,
    cpw_pad_width: pft.PositiveDimension = 150,
    cpw_pad_pitch: pft.PositiveDimension = 100,
    cpw_pad_overlap: pft.PositiveDimension = 45,
    cpw_pad_m2_length: pft.PositiveDimension = 80,
    via_size: pft.PositiveDimension = 12,
    via_gap: pft.PositiveDimension = 12,
    via_margin: pft.Dimension = 2.5,
    via_fillet: pft.Dimension = 1,
    technology: pf.Technology | None = None,
    name: str = "",
) -> pf.Component:
    """Unterminated MZM modulator for O band using 2x2 MMI splitters.

    Args:
        mmi: MMI component used as optical splitter and combiner.
          If ``None``The PDK default is used.
        modulation_length: Length of the modulation section.
        modulation_bulge: Width added to the waveguide in the modulation
          region.
        modulation_bulge_taper: Length of the bulge transition taper.
        heater_length: Length of the heated waveguide used for bias control.
        heater_width: Width of the heater wire.
        heater_offset: Offset between the heater wire and the optical
          waveguide centers.
        heater_route_width: Width of the routing path for the heater.
        heater_pad_size: Heater pad size.
        heater_pad_pitch: Heater pad pitch.
        heater_pad_offset: Offset between the heater wire and pad edges.
        heater_contact_factor: Factor controlling the routing width at the
          wire (multiplies the wire width).
        imbalance_length: Length of an optional optical segment added to a
          single MZI arm (top, if positive, or bottom, if negative).
        mmi_connection_length: Length of the connection close to the MMIs.
        cpw_connection_length: Length of the connection close to the CPW.
        radius: Bend radius for optical waveguides.
        s_bend_factor: Ratio between length and offset for S bends.
        cpw_spec: Port specification for the CPW.
        t_rail_base: Dimensions for an optional T-rail base for the CPW.
        t_rail_top: Dimensions for an optional T-rail top for the CPW.
        t_rail_gap: Gap between adjacent T-rail insertions in the CPW.
        t_rail_fillet: Fillet radius for T-rail shapes.
        cpw_pad_straight: Length of the straight section of the CPW pad.
        cpw_pad_taper: Length of the taper section of the CPW pad.
        cpw_pad_width: Width of the ground CPW pads.
        cpw_pad_pitch: CPW pad pitch.
        cpw_pad_overlap: Length of the via section of the CPW pad.
        cpw_pad_m2_length: Length of the CPW pad in M2.
        via_size: Dimensions of an individual via.
        via_gap: Separation between adjacent via edges.
        via_margin: Margin between vias and the surrounding region.
        via_fillet: Fillet radius for vias.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.

    Returns:
        MZM component.
    """
    if mmi is None:
        mmi = mmi2x2_oband(technology=technology)

    return base_mzm(
        mmi,
        modulation_length,
        modulation_bulge,
        modulation_bulge_taper,
        heater_length,
        heater_width,
        heater_offset,
        heater_route_width,
        heater_pad_size,
        heater_pad_pitch,
        heater_pad_offset,
        heater_contact_factor,
        imbalance_length,
        mmi_connection_length,
        cpw_connection_length,
        radius,
        s_bend_factor,
        cpw_spec,
        t_rail_base,
        t_rail_top,
        t_rail_gap,
        t_rail_fillet,
        cpw_pad_straight,
        cpw_pad_taper,
        cpw_pad_width,
        cpw_pad_pitch,
        cpw_pad_overlap,
        cpw_pad_m2_length,
        0,
        0,
        0,
        0,
        0,
        0,
        via_size,
        via_gap,
        via_margin,
        via_fillet,
        technology,
        name,
    )


@pf.parametric_component
def terminated_mzm_2x2mmi_cband(
    *,
    mmi: pf.Component | None = None,
    modulation_length: pft.PositiveDimension = 5000,
    modulation_bulge: pft.Coordinate = 1.6,
    modulation_bulge_taper: pft.Dimension = 100,
    heater_length: pft.Dimension = 700,
    heater_width: pft.PositiveDimension = 2.5,
    heater_offset: pft.Coordinate = 0,
    heater_route_width: pft.PositiveDimension = 6,
    heater_pad_size: pft.PositiveDimension2D = (150, 150),
    heater_pad_pitch: pft.PositiveDimension | None = None,
    heater_pad_offset: pft.PositiveDimension = 10,
    heater_contact_factor: pft.PositiveFloat = 3,
    imbalance_length: pft.Coordinate = 100,
    mmi_connection_length: pft.Dimension = 10,
    cpw_connection_length: pft.Dimension = 75,
    radius: pft.PositiveDimension = 60,
    s_bend_factor: pft.PositiveFloat = 3.5,
    cpw_spec: str | pf.PortSpec = "UniCPW-EO-cband",
    t_rail_base: pft.Dimension2D = (53, 1.5),
    t_rail_top: pft.Dimension2D = (53, 1.5),
    t_rail_gap: pft.Dimension = 5,
    t_rail_fillet: pft.Dimension = 0.45,
    cpw_pad_straight: pft.PositiveDimension = 25,
    cpw_pad_taper: pft.PositiveDimension = 150,
    cpw_pad_width: pft.PositiveDimension = 150,
    cpw_pad_pitch: pft.PositiveDimension = 100,
    cpw_pad_overlap: pft.PositiveDimension = 45,
    cpw_pad_m2_length: pft.PositiveDimension = 80,
    termination_resistor_length: pft.Dimension = 48.5,
    termination_resistor_width: pft.PositiveDimension = 1.5,
    termination_m1_length: pft.PositiveDimension = 45,
    termination_m2_separation: pft.PositiveDimension = 10,
    termination_m2_hrl_length: pft.PositiveDimension = 20,
    termination_hrl_separation: pft.PositiveDimension = 2.5,
    via_size: pft.PositiveDimension = 12,
    via_gap: pft.PositiveDimension = 12,
    via_margin: pft.Dimension = 2.5,
    via_fillet: pft.Dimension = 1,
    technology: pf.Technology | None = None,
    name: str = "",
) -> pf.Component:
    """Terminated MZM modulator for C band using 2x2 MMI splitters.

    Args:
        mmi: MMI component used as optical splitter and combiner.
          If ``None``The PDK default is used.
        modulation_length: Length of the modulation section.
        modulation_bulge: Width added to the waveguide in the modulation
          region.
        modulation_bulge_taper: Length of the bulge transition taper.
        heater_length: Length of the heated waveguide used for bias control.
        heater_width: Width of the heater wire.
        heater_offset: Offset between the heater wire and the optical
          waveguide centers.
        heater_route_width: Width of the routing path for the heater.
        heater_pad_size: Heater pad size.
        heater_pad_pitch: Heater pad pitch.
        heater_pad_offset: Offset between the heater wire and pad edges.
        heater_contact_factor: Factor controlling the routing width at the
          wire (multiplies the wire width).
        imbalance_length: Length of an optional optical segment added to a
          single MZI arm (top, if positive, or bottom, if negative).
        mmi_connection_length: Length of the connection close to the MMIs.
        cpw_connection_length: Length of the connection close to the CPW.
        radius: Bend radius for optical waveguides.
        s_bend_factor: Ratio between length and offset for S bends.
        cpw_spec: Port specification for the CPW.
        t_rail_base: Dimensions for an optional T-rail base for the CPW.
        t_rail_top: Dimensions for an optional T-rail top for the CPW.
        t_rail_gap: Gap between adjacent T-rail insertions in the CPW.
        t_rail_fillet: Fillet radius for T-rail shapes.
        cpw_pad_straight: Length of the straight section of the CPW pad.
        cpw_pad_taper: Length of the taper section of the CPW pad.
        cpw_pad_width: Width of the ground CPW pads.
        cpw_pad_pitch: CPW pad pitch.
        cpw_pad_overlap: Length of the via section of the CPW pad.
        cpw_pad_m2_length: Length of the CPW pad in M2.
        termination_resistor_length: Effective length of the CPW termination
          resistor.
        termination_resistor_width: Width of the CPW termination resistor.
        termination_m1_length: Length of the termination in M1.
        termination_m2_separation: Length of the termination in M2.
        termination_m2_hrl_length: Length of the termination in the M2/HRL
          via region.
        termination_hrl_separation: Added length for the termination in HRL.
        via_size: Dimensions of an individual via.
        via_gap: Separation between adjacent via edges.
        via_margin: Margin between vias and the surrounding region.
        via_fillet: Fillet radius for vias.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.

    Returns:
        MZM component.
    """
    if mmi is None:
        mmi = mmi2x2_cband(technology=technology)

    return base_mzm(
        mmi,
        modulation_length,
        modulation_bulge,
        modulation_bulge_taper,
        heater_length,
        heater_width,
        heater_offset,
        heater_route_width,
        heater_pad_size,
        heater_pad_pitch,
        heater_pad_offset,
        heater_contact_factor,
        imbalance_length,
        mmi_connection_length,
        cpw_connection_length,
        radius,
        s_bend_factor,
        cpw_spec,
        t_rail_base,
        t_rail_top,
        t_rail_gap,
        t_rail_fillet,
        cpw_pad_straight,
        cpw_pad_taper,
        cpw_pad_width,
        cpw_pad_pitch,
        cpw_pad_overlap,
        cpw_pad_m2_length,
        termination_resistor_length,
        termination_resistor_width,
        termination_m1_length,
        termination_m2_separation,
        termination_m2_hrl_length,
        termination_hrl_separation,
        via_size,
        via_gap,
        via_margin,
        via_fillet,
        technology,
        name,
    )


@pf.parametric_component
def unterminated_mzm_2x2mmi_cband(
    *,
    mmi: pf.Component | None = None,
    modulation_length: pft.PositiveDimension = 5000,
    modulation_bulge: pft.Coordinate = 1.6,
    modulation_bulge_taper: pft.Dimension = 100,
    heater_length: pft.Dimension = 700,
    heater_width: pft.PositiveDimension = 2.5,
    heater_offset: pft.Coordinate = 0,
    heater_route_width: pft.PositiveDimension = 6,
    heater_pad_size: pft.PositiveDimension2D = (150, 150),
    heater_pad_pitch: pft.PositiveDimension | None = None,
    heater_pad_offset: pft.PositiveDimension = 10,
    heater_contact_factor: pft.PositiveFloat = 3,
    imbalance_length: pft.Coordinate = 100,
    mmi_connection_length: pft.Dimension = 10,
    cpw_connection_length: pft.Dimension = 75,
    radius: pft.PositiveDimension = 60,
    s_bend_factor: pft.PositiveFloat = 3.5,
    cpw_spec: str | pf.PortSpec = "UniCPW-EO-cband",
    t_rail_base: pft.Dimension2D = (53, 1.5),
    t_rail_top: pft.Dimension2D = (53, 1.5),
    t_rail_gap: pft.Dimension = 5,
    t_rail_fillet: pft.Dimension = 0.45,
    cpw_pad_straight: pft.PositiveDimension = 25,
    cpw_pad_taper: pft.PositiveDimension = 150,
    cpw_pad_width: pft.PositiveDimension = 150,
    cpw_pad_pitch: pft.PositiveDimension = 100,
    cpw_pad_overlap: pft.PositiveDimension = 45,
    cpw_pad_m2_length: pft.PositiveDimension = 80,
    via_size: pft.PositiveDimension = 12,
    via_gap: pft.PositiveDimension = 12,
    via_margin: pft.Dimension = 2.5,
    via_fillet: pft.Dimension = 1,
    technology: pf.Technology | None = None,
    name: str = "",
) -> pf.Component:
    """Unterminated MZM modulator for C band using 2x2 MMI splitters.

    Args:
        mmi: MMI component used as optical splitter and combiner.
          If ``None``The PDK default is used.
        modulation_length: Length of the modulation section.
        modulation_bulge: Width added to the waveguide in the modulation
          region.
        modulation_bulge_taper: Length of the bulge transition taper.
        heater_length: Length of the heated waveguide used for bias control.
        heater_width: Width of the heater wire.
        heater_offset: Offset between the heater wire and the optical
          waveguide centers.
        heater_route_width: Width of the routing path for the heater.
        heater_pad_size: Heater pad size.
        heater_pad_pitch: Heater pad pitch.
        heater_pad_offset: Offset between the heater wire and pad edges.
        heater_contact_factor: Factor controlling the routing width at the
          wire (multiplies the wire width).
        imbalance_length: Length of an optional optical segment added to a
          single MZI arm (top, if positive, or bottom, if negative).
        mmi_connection_length: Length of the connection close to the MMIs.
        cpw_connection_length: Length of the connection close to the CPW.
        radius: Bend radius for optical waveguides.
        s_bend_factor: Ratio between length and offset for S bends.
        cpw_spec: Port specification for the CPW.
        t_rail_base: Dimensions for an optional T-rail base for the CPW.
        t_rail_top: Dimensions for an optional T-rail top for the CPW.
        t_rail_gap: Gap between adjacent T-rail insertions in the CPW.
        t_rail_fillet: Fillet radius for T-rail shapes.
        cpw_pad_straight: Length of the straight section of the CPW pad.
        cpw_pad_taper: Length of the taper section of the CPW pad.
        cpw_pad_width: Width of the ground CPW pads.
        cpw_pad_pitch: CPW pad pitch.
        cpw_pad_overlap: Length of the via section of the CPW pad.
        cpw_pad_m2_length: Length of the CPW pad in M2.
        via_size: Dimensions of an individual via.
        via_gap: Separation between adjacent via edges.
        via_margin: Margin between vias and the surrounding region.
        via_fillet: Fillet radius for vias.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.

    Returns:
        MZM component.
    """
    if mmi is None:
        mmi = mmi2x2_cband(technology=technology)

    return base_mzm(
        mmi,
        modulation_length,
        modulation_bulge,
        modulation_bulge_taper,
        heater_length,
        heater_width,
        heater_offset,
        heater_route_width,
        heater_pad_size,
        heater_pad_pitch,
        heater_pad_offset,
        heater_contact_factor,
        imbalance_length,
        mmi_connection_length,
        cpw_connection_length,
        radius,
        s_bend_factor,
        cpw_spec,
        t_rail_base,
        t_rail_top,
        t_rail_gap,
        t_rail_fillet,
        cpw_pad_straight,
        cpw_pad_taper,
        cpw_pad_width,
        cpw_pad_pitch,
        cpw_pad_overlap,
        cpw_pad_m2_length,
        0,
        0,
        0,
        0,
        0,
        0,
        via_size,
        via_gap,
        via_margin,
        via_fillet,
        technology,
        name,
    )
