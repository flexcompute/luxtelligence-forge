import warnings

import photonforge as pf
import photonforge.typing as pft

from .utils import _core_and_clad_info


@pf.parametric_component
def s_bend_spline(
    *,
    port_spec: str | pf.PortSpec = "RWG1000",
    length: pft.PositiveDimension = 100.0,
    offset: pft.Coordinate = 25.0,
    straight_length: pft.Dimension = 5.0,
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
def u_bend(
    *,
    port_spec: str | pf.PortSpec = "RWG1000",
    offset: pft.Coordinate = 80.0,
    euler_fraction: pft.Fraction = 1.0,
    technology: pf.Technology | None = None,
    name: str = "",
    model: pf.Model | None = pf.Tidy3DModel(port_symmetries=[(1, 0)]),
) -> pf.Component:
    """180° bend.

    Args:
        port_spec: Port specification describing waveguide cross-section.
        offset: Vertical offset of the bend.
        euler_fraction: Fraction of the bend that is created using an Euler
          spiral (see :func:`photonforge.Path.arc`).
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component.

    Returns:
        Component with the bend, ports, and model.
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
    c.properties.__thumbnail__ = "u-bend"

    endpoint = (0, offset)
    radius = abs(offset) / 2
    a0, a1 = (-90, 90) if offset > 0 else (90, -90)
    for layer, path in port_spec.get_paths((0, 0)):
        path.arc(a0, a1, radius, euler_fraction=euler_fraction, endpoint=endpoint)
        c.add(layer, path)

    c.add_port(pf.Port((0, 0), 0, port_spec))
    c.add_port(pf.Port(endpoint, 0, port_spec, inverted=True))

    if model is not None:
        c.add_model(model)

    return c


@pf.parametric_component
def racetrack_u_bend(
    *,
    port_spec: str | pf.PortSpec = "RWG3000",
    offset: pft.Coordinate = 90.0,
    euler_fraction: pft.Fraction = 1.0,
    technology: pf.Technology | None = None,
    name: str = "",
    model: pf.Model | None = pf.Tidy3DModel(port_symmetries=[(1, 0)]),
) -> pf.Component:
    """180° bend with defaults suitable for low-loss racetrack resonator.

    Args:
        port_spec: Port specification describing waveguide cross-section.
        offset: Vertical offset of the bend.
        euler_fraction: Fraction of the bend that is created using an Euler
          spiral (see :func:`photonforge.Path.arc`).
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component.

    Returns:
        Component with the bend, ports, and model.
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
    c.properties.__thumbnail__ = "u-bend"

    endpoint = (0, offset)
    radius = abs(offset) / 2
    a0, a1 = (-90, 90) if offset > 0 else (90, -90)
    for layer, path in port_spec.get_paths((0, 0)):
        path.arc(a0, a1, radius, euler_fraction=euler_fraction, endpoint=endpoint)
        c.add(layer, path)

    c.add_port(pf.Port((0, 0), 0, port_spec))
    c.add_port(pf.Port(endpoint, 0, port_spec, inverted=True))

    if model is not None:
        c.add_model(model)

    return c


@pf.parametric_component
def l_bend(
    *,
    port_spec: str | pf.PortSpec = "RWG1000",
    effective_radius: pft.PositiveDimension = 80.0,
    euler_fraction: pft.Fraction = 1.0,
    technology: pf.Technology | None = None,
    name: str = "",
    model: pf.Model | None = pf.Tidy3DModel(port_symmetries=[(1, 0)]),
) -> pf.Component:
    """90° bend.

    Args:
        port_spec: Port specification describing waveguide cross-section.
        effective_radius: Effective radius of the bend (horizontal/vertical
          extent).
        euler_fraction: Fraction of the bend that is created using an Euler
          spiral (see :func:`photonforge.Path.arc`).
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component.

    Returns:
        Component with the bend, ports, and model.
    """
    if effective_radius <= 0:
        raise ValueError("'radius' must be positive.")

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
    c.properties.__thumbnail__ = "bend"

    endpoint = (effective_radius, effective_radius)
    for layer, path in port_spec.get_paths((0, 0)):
        path.arc(-90, 0, effective_radius, euler_fraction=euler_fraction, endpoint=endpoint)
        c.add(layer, path)

    c.add_port(pf.Port((0, 0), 0, port_spec))
    c.add_port(pf.Port(endpoint, -90, port_spec, inverted=True))

    if model is not None:
        c.add_model(model)

    return c


@pf.parametric_component
def s_bend_spline_varying_width(
    *,
    port_spec1: str | pf.PortSpec = "RWG1000",
    port_spec2: str | pf.PortSpec = "RWG3000",
    length: pft.PositiveDimension = 58.0,
    offset: pft.Coordinate = 14.5,
    technology: pf.Technology | None = None,
    name: str = "",
    model: pf.Model | None = pf.Tidy3DModel(),
) -> pf.Component:
    """S-bend waveguide section with varying profile width.

    Args:
        port_spec1: Port specification describing the starting waveguide
          cross-section.
        port_spec2: Port specification describing the ending waveguide
          cross-section.
        length: Horizontal extent of the bend.
        offset: Vertical offset of the bend.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component.

    Returns:
        Component with the S-bend, ports, and model.
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
    if isinstance(port_spec1, str):
        port_spec1 = technology.ports[port_spec1]
    if isinstance(port_spec2, str):
        port_spec2 = technology.ports[port_spec2]

    c = pf.Component(name, technology=technology)
    c.properties.__thumbnail__ = "s-bend"

    core_width1, core_layer1, clad_width1, clad_layer1 = _core_and_clad_info(port_spec1, technology)
    core_width2, core_layer2, clad_width2, clad_layer2 = _core_and_clad_info(port_spec2, technology)
    if core_layer1 != core_layer2 or clad_layer1 != clad_layer2:
        raise ValueError("Incompatible waveguide types (port specifications).")

    controls = [
        (0.2 * length, 0),
        (0.4 * length, 0),
        (0.6 * length, offset),
        (0.8 * length, offset),
        (length, offset),
    ]
    c.add(
        core_layer1,
        pf.Path((0, 0), core_width1).bezier(controls, width=core_width2),
        clad_layer1,
        pf.Path((0, 0), clad_width1).bezier(controls, width=clad_width2),
    )

    c.add_port(pf.Port((0, 0), 0, port_spec1))
    c.add_port(pf.Port((length, offset), 180, port_spec2, inverted=True))

    if model is not None:
        c.add_model(model)

    return c


@pf.parametric_component
def directional_coupler_balanced(
    *,
    port_spec: str | pf.PortSpec = "RWG1000",
    io_wg_sep: pft.PositiveDimension = 30.6,
    s_bend_length: pft.PositiveDimension = 58.0,
    central_straight_length: pft.Dimension = 16.92,
    central_wg_width: pft.PositiveDimension = 0.8,
    coupler_wg_sep: pft.Dimension = 0.8,
    technology: pf.Technology | None = None,
    name: str = "",
    model: pf.Model | None = pf.Tidy3DModel(),
) -> pf.Component:
    """Directional coupler with S-bends.

    Args:
        port_spec: Port specification describing waveguide cross-section.
        io_wg_sep: Separation between the input/output waveguide centers.
        s_bend_length: Length of the S-bend sections.
        central_straight_length: Length of the coupling region.
        central_wg_width: Width of the waveguide in the coupling region.
        coupler_wg_sep: Distance between waveguides (edge-to-edge) in the
          coupling region.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component.

    Returns:
        Component with the directional coupler, ports, and model.
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

    core_width, core_layer, clad_width, clad_layer = _core_and_clad_info(port_spec, technology)
    port_spec1 = port_spec.copy()
    port_spec1.description = f"{port_spec.description}, custom core {central_wg_width}μm"
    port_spec1.path_profiles = [(central_wg_width, 0, core_layer), (clad_width, 0, clad_layer)]

    s_bend = s_bend_spline_varying_width(
        port_spec1=port_spec1,
        port_spec2=port_spec,
        length=s_bend_length,
        offset=0.5 * (io_wg_sep - coupler_wg_sep - central_wg_width),
        technology=technology,
    )
    straight = pf.parametric.straight(
        port_spec=s_bend.ports["P0"].spec,
        length=central_straight_length,
        technology=technology,
    )

    c = pf.Component(name, technology=technology)
    c.properties.__thumbnail__ = "dc"

    top = pf.Reference(
        straight, (-0.5 * central_straight_length, 0.5 * (central_wg_width + coupler_wg_sep))
    )
    bot = pf.Reference(
        straight, (-0.5 * central_straight_length, -0.5 * (central_wg_width + coupler_wg_sep))
    )
    if central_straight_length != 0:
        c.add(top, bot)

    ref = c.add_reference(s_bend).connect("P0", bot["P0"])
    c.add_port(ref["P1"])

    ref = c.add_reference(s_bend).mirror().connect("P0", top["P0"])
    c.add_port(ref["P1"])

    ref = c.add_reference(s_bend).mirror().connect("P0", bot["P1"])
    c.add_port(ref["P1"])

    ref = c.add_reference(s_bend).connect("P0", top["P1"])
    c.add_port(ref["P1"])

    if model is not None:
        c.add_model(model)

    return c
