from warnings import warn

import numpy as np
import photonforge as pf
import photonforge.typing as pft

from .utils import _core_and_clad_info


def double_layer_edge_coupler(
    start_port_spec,
    end_port_spec,
    lower_profile,
    upper_profile,
    upper_taper_length,
    total_taper_length,
    slab_removal_width,
    input_ext,
    technology,
    name,
    model,
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
    if isinstance(start_port_spec, str):
        start_port_spec = technology.ports[start_port_spec]
    if isinstance(end_port_spec, str):
        end_port_spec = technology.ports[end_port_spec]

    c = pf.Component(name, technology=technology)
    c.properties.__thumbnail__ = "taper"

    lower_width = lower_profile(0)[-2]
    width, lower_layer, *_ = _core_and_clad_info(start_port_spec, technology)
    if abs(width - lower_width) >= pf.config.tolerance / 2:
        warn("'lower_profile' starting width does not match 'start_port_spec'.", RuntimeWarning, 3)

    upper_width = upper_profile(1)[-2]
    width, upper_layer, *_ = _core_and_clad_info(end_port_spec, technology)
    if abs(width - upper_width) >= pf.config.tolerance / 2:
        warn("'upper_profile' starting width does not match 'end_port_spec'.", RuntimeWarning, 3)

    lower = pf.Path((0, 0), 0)
    lower.segment((total_taper_length, 0), lower_profile)

    upper = pf.Path((total_taper_length - upper_taper_length, 0), 0)
    upper.segment((total_taper_length, 0), upper_profile)

    c.add(upper_layer, upper, lower_layer, lower)

    if input_ext > 0:
        c.add(
            lower_layer,
            pf.Rectangle(corner1=(-input_ext, -0.5 * lower_width), corner2=(0, 0.5 * lower_width)),
        )

    if slab_removal_width > 0:
        c.add(
            "SLAB_NEGATIVE",
            pf.Rectangle(
                center=(0.5 * (total_taper_length - input_ext), 0),
                size=(total_taper_length + input_ext, slab_removal_width),
            ),
        )

    c.add_port(pf.Port((-input_ext if input_ext > 0 else 0, 0), 0, start_port_spec))
    c.add_port(pf.Port((total_taper_length, 0), 180, end_port_spec, inverted=True))

    c.add_model(model)
    return c


def lin_exp(y0, x1, y1, y2, rate, y_max):
    return pf.Expression(
        "u",
        [
            ("y0", y0),
            ("x1", x1),
            ("y1", y1),
            ("y2", y2),
            ("rate", rate),
            ("y_max", y_max),
            ("dy_lin", (y1 - y0) / x1),
            ("y_lin", "y0 + dy_lin * u"),
            ("scale", 1.0 / (1.0 - np.exp(rate))),
            ("v", "exp(rate * (u - x1) / (1 - x1))"),
            ("w", "scale * (1 - v)"),
            ("y_exp", "(1 - w) * y1 + w * y2"),
            ("dy_exp", "scale * rate / (1 - x1) * v * (y1 - y2)"),
            "if(u - x1, min(y_max, y_exp), y_lin)",
            "if(u - x1, if(y_exp - y_max, 0, dy_exp), dy_lin)",
        ],
    )


def exp(y0, y1, rate):
    return pf.Expression(
        "u",
        [
            ("y0", y0),
            ("y1", y1),
            ("rate", rate),
            ("scale", 1.0 / (1.0 - np.exp(-rate))),
            ("v", "exp(rate * (u - 1))"),
            ("w", "scale * (1 - v)"),
            ("y", "(1 - w) * y0 + w * y1"),
            ("dy", "scale * rate * v * (y0 - y1)"),
        ],
    )


_lower_o = lin_exp(0.35, 0.25, 0.5, 162.0, 7.5, 5.6)
_upper_o = exp(0.7, 0.25, 2.5)


@pf.parametric_component
def edge_coupler_oband(
    *,
    start_port_spec: str | pf.PortSpec = "SWG350",
    end_port_spec: str | pf.PortSpec = "RWG700",
    lower_profile: pf.Expression = _lower_o,
    upper_profile: pf.Expression = _upper_o,
    upper_taper_length: pft.PositiveDimension = 80.0,
    total_taper_length: pft.PositiveDimension = 160.0,
    slab_removal_width: pft.Dimension = 20.0,
    input_ext: pft.Dimension = 10.0,
    technology: pf.Technology | None = None,
    name: str = "",
    model: pf.Model = pf.Tidy3DModel(),
) -> pf.Component:
    """Dual layer inverse taper from a strip to a rib waveguide.

    Args:
        start_port_spec: Port specification describing the strip waveguide.
        end_port_spec: Port specification describing rib waveguide.
        lower_taper_end_width: Lower taper width at the start of the upper
          taper.
        upper_taper_start_width: The start width of the rib waveguide
          section.
        upper_taper_length: Length of the rib waveguide taper.
        total_taper_length: Total length of the taper.
        slab_removal_width: Width of the region where the slab is removed
          close to the coupler (for fabrication in positive tone).
        input_ext: Length of a straight segment extending beyond the lower
          taper.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component.

    Returns:
        Component with the taper, ports and model.
    """
    return double_layer_edge_coupler(
        start_port_spec,
        end_port_spec,
        lower_profile,
        upper_profile,
        upper_taper_length,
        total_taper_length,
        slab_removal_width,
        input_ext,
        technology,
        name,
        model,
    )


_lower_c = lin_exp(0.5, 0.5, 1.5, 14.7, 2.5, 5.6)
_upper_c = exp(0.9, 0.25, 2.5)


@pf.parametric_component
def edge_coupler_cband(
    *,
    start_port_spec: str | pf.PortSpec = "SWG500",
    end_port_spec: str | pf.PortSpec = "RWG900",
    lower_profile: pf.Expression = _lower_c,
    upper_profile: pf.Expression = _upper_c,
    upper_taper_length: pft.PositiveDimension = 80.0,
    total_taper_length: pft.PositiveDimension = 160.0,
    slab_removal_width: pft.Dimension = 20.0,
    input_ext: pft.Dimension = 10.0,
    technology: pf.Technology | None = None,
    name: str = "",
    model: pf.Model = pf.Tidy3DModel(),
) -> pf.Component:
    """Dual layer inverse taper from a strip to a rib waveguide.

    Args:
        start_port_spec: Port specification describing the strip waveguide.
        end_port_spec: Port specification describing rib waveguide.
        lower_taper_end_width: Lower taper width at the start of the upper
          taper.
        upper_taper_start_width: The start width of the rib waveguide
          section.
        upper_taper_length: Length of the rib waveguide taper.
        total_taper_length: Total length of the taper.
        slab_removal_width: Width of the region where the slab is removed
          close to the coupler (for fabrication in positive tone).
        input_ext: Length of a straight segment extending beyond the lower
          taper.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component.

    Returns:
        Component with the taper, ports and model.
    """
    return double_layer_edge_coupler(
        start_port_spec,
        end_port_spec,
        lower_profile,
        upper_profile,
        upper_taper_length,
        total_taper_length,
        slab_removal_width,
        input_ext,
        technology,
        name,
        model,
    )
