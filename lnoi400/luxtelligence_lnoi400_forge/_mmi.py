from warnings import warn

import photonforge as pf
import photonforge.typing as pft

from .utils import _core_and_clad_info


@pf.parametric_component
def mmi1x2_optimized1550(
    *,
    port_spec: str | pf.PortSpec = "RWG1000",
    width: pft.PositiveDimension = 6.0,
    length: pft.PositiveDimension = 26.75,
    taper_width: pft.PositiveDimension = 1.5,
    taper_length: pft.PositiveDimension = 25.0,
    port_separation: pft.Dimension = 3.3,
    technology: pf.Technology | None = None,
    name: str = "",
    model: pf.Model = pf.Tidy3DModel(),
) -> pf.Component:
    """MMI with 1 port on one side and 2 ports on the other.

    Args:
        port_spec: Port specification describing waveguide cross-section.
        width: Width of the MMI section.
        length: Length of the MMI section.
        taper_width: Width of the taper.
        taper_length: Length of the taper.
        port_separation: Distance between ports.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component.

    Returns:
        MMI Component with layout, ports and model.
    """
    if port_separation + taper_width > width:
        raise ValueError("Condition 'port_separation + taper_width ≤ width' is not satisfied.")
    if port_separation < taper_width:
        warn("Waveguide tapers will overlap.", RuntimeWarning, 3)

    if technology is None:
        technology = pf.config.default_technology
        if "LNOI400" not in technology.name:
            warn(
                f"Current default technology {technology.name} does not seem supported by the "
                "Luxtelligence LNOI400 component library.",
                RuntimeWarning,
                3,
            )
    if isinstance(port_spec, str):
        port_spec = technology.ports[port_spec]

    c = pf.Component(name, technology=technology)
    c.properties.__thumbnail__ = "mmi1x2"

    core_width, core_layer, clad_width, clad_layer = _core_and_clad_info(port_spec, technology)
    margin = 0.5 * (clad_width - core_width)
    clad_taper_width = clad_width + taper_width - core_width

    c.add(
        core_layer,
        pf.Rectangle((0, -0.5 * width), (length, 0.5 * width)),
        clad_layer,
        pf.Rectangle((0, -0.5 * width - margin), (length, 0.5 * width + margin)),
    )

    for layer, path in port_spec.get_paths((-taper_length, 0)):
        if layer == core_layer:
            c.add(layer, path.segment((0, 0), taper_width))
        else:
            c.add(layer, path.segment((0, 0), clad_taper_width))

    x = length + taper_length
    offset = port_separation * 0.5
    for y in (-offset, offset):
        for layer, path in port_spec.get_paths((x, y)):
            if layer == core_layer:
                c.add(layer, path.segment((length, y), taper_width))
            else:
                c.add(layer, path.segment((length, y), clad_taper_width))

    c.add_port(pf.Port((-taper_length, 0), 0, port_spec))
    c.add_port(pf.Port((x, offset), 180, port_spec, inverted=True))
    c.add_port(pf.Port((x, -offset), 180, port_spec, inverted=True))

    c.add_model(model)
    return c


@pf.parametric_component
def mmi2x2_optimized1550(
    *,
    port_spec: str | pf.PortSpec = "RWG1000",
    width: pft.PositiveDimension = 5.0,
    length: pft.PositiveDimension = 76.5,
    taper_width: pft.PositiveDimension = 1.5,
    taper_length: pft.PositiveDimension = 25.0,
    port_separation: pft.Dimension = 3.5,
    technology: pf.Technology | None = None,
    name: str = "",
    model: pf.Model = pf.Tidy3DModel(),
) -> pf.Component:
    """MMI with 2 ports on each side.

    Args:
        port_spec: Port specification describing waveguide cross-section.
        width: Width of the MMI section.
        length: Length of the MMI section.
        taper_width: Width of the taper.
        taper_length: Length of the taper.
        port_separation: Distance between ports.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component.

    Returns:
        MMI Component with layout, ports and model.
    """
    if port_separation + taper_width > width:
        raise ValueError("Condition 'port_separation + taper_width ≤ width' is not satisfied.")
    if port_separation < taper_width:
        warn("Waveguide tapers will overlap.", RuntimeWarning, 3)

    if technology is None:
        technology = pf.config.default_technology
        if "LNOI400" not in technology.name:
            warn(
                f"Current default technology {technology.name} does not seem supported by the "
                "Luxtelligence LNOI400 component library.",
                RuntimeWarning,
                3,
            )
    if isinstance(port_spec, str):
        port_spec = technology.ports[port_spec]

    c = pf.Component(name, technology=technology)
    c.properties.__thumbnail__ = "mmi2x2"

    core_width, core_layer, clad_width, clad_layer = _core_and_clad_info(port_spec, technology)
    margin = 0.5 * (clad_width - core_width)
    clad_taper_width = clad_width + taper_width - core_width

    c.add(
        core_layer,
        pf.Rectangle((0, -0.5 * width), (length, 0.5 * width)),
        clad_layer,
        pf.Rectangle((0, -0.5 * width - margin), (length, 0.5 * width + margin)),
    )

    offset = port_separation * 0.5
    for y in (-offset, offset):
        for layer, path in port_spec.get_paths((-taper_length, y)):
            if layer == core_layer:
                c.add(layer, path.segment((0, y), taper_width))
            else:
                c.add(layer, path.segment((0, y), clad_taper_width))

    x = length + taper_length
    for y in (-offset, offset):
        for layer, path in port_spec.get_paths((x, y)):
            if layer == core_layer:
                c.add(layer, path.segment((length, y), taper_width))
            else:
                c.add(layer, path.segment((length, y), clad_taper_width))

    c.add_port(pf.Port((-taper_length, offset), 0, port_spec))
    c.add_port(pf.Port((-taper_length, -offset), 0, port_spec))
    c.add_port(pf.Port((x, offset), 180, port_spec, inverted=True))
    c.add_port(pf.Port((x, -offset), 180, port_spec, inverted=True))

    c.add_model(model)
    return c
