from warnings import warn

import photonforge as pf
import photonforge.typing as pft

from .utils import _core_and_clad_info


def mmi1x2(
    port_spec,
    width,
    length,
    taper_width,
    taper_length,
    port_separation,
    technology,
    name,
    model,
) -> pf.Component:
    if port_separation + taper_width > width:
        raise ValueError("Condition 'port_separation + taper_width ≤ width' is not satisfied.")
    if port_separation < taper_width:
        warn("Waveguide tapers will overlap.", RuntimeWarning, 3)

    if technology is None:
        technology = pf.config.default_technology
        if "LTOI300" not in technology.name:
            warn(
                f"Current default technology {technology.name} does not seem supported by the "
                "Luxtelligence LTOI300 component library.",
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
def mmi1x2_oband(
    *,
    port_spec: str | pf.PortSpec = "RWG700",
    width: pft.PositiveDimension = 4.5,
    length: pft.PositiveDimension = 15.8,
    taper_width: pft.PositiveDimension = 1.7,
    taper_length: pft.PositiveDimension = 25.0,
    port_separation: pft.Dimension = 2.45,
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
    return mmi1x2(
        port_spec,
        width,
        length,
        taper_width,
        taper_length,
        port_separation,
        technology,
        name,
        model,
    )


@pf.parametric_component
def mmi1x2_cband(
    *,
    port_spec: str | pf.PortSpec = "RWG900",
    width: pft.PositiveDimension = 4.5,
    length: pft.PositiveDimension = 13.5,
    taper_width: pft.PositiveDimension = 1.95,
    taper_length: pft.PositiveDimension = 25.0,
    port_separation: pft.Dimension = 2.55,
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
    return mmi1x2(
        port_spec,
        width,
        length,
        taper_width,
        taper_length,
        port_separation,
        technology,
        name,
        model,
    )


def mmi2x2(
    port_spec,
    width,
    length,
    taper_width,
    taper_length,
    port_separation,
    technology,
    name,
    model,
) -> pf.Component:
    if port_separation + taper_width > width:
        raise ValueError("Condition 'port_separation + taper_width ≤ width' is not satisfied.")
    if port_separation < taper_width:
        warn("Waveguide tapers will overlap.", RuntimeWarning, 3)

    if technology is None:
        technology = pf.config.default_technology
        if "LTOI300" not in technology.name:
            warn(
                f"Current default technology {technology.name} does not seem supported by the "
                "Luxtelligence LTOI300 component library.",
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


@pf.parametric_component
def mmi2x2_oband(
    *,
    port_spec: str | pf.PortSpec = "RWG700",
    width: pft.PositiveDimension = 5.65,
    length: pft.PositiveDimension = 97.5,
    taper_width: pft.PositiveDimension = 1.75,
    taper_length: pft.PositiveDimension = 25.0,
    port_separation: pft.Dimension = 3.9,
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
    return mmi2x2(
        port_spec,
        width,
        length,
        taper_width,
        taper_length,
        port_separation,
        technology,
        name,
        model,
    )


@pf.parametric_component
def mmi2x2_cband(
    *,
    port_spec: str | pf.PortSpec = "RWG900",
    width: pft.PositiveDimension = 5.15,
    length: pft.PositiveDimension = 67.5,
    taper_width: pft.PositiveDimension = 1.5,
    taper_length: pft.PositiveDimension = 25.0,
    port_separation: pft.Dimension = 3.65,
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
    return mmi2x2(
        port_spec=port_spec,
        width=width,
        length=length,
        taper_width=taper_width,
        taper_length=taper_length,
        port_separation=port_separation,
        technology=technology,
        name=name,
        model=model,
    )
