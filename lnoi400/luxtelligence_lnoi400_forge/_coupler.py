import warnings

import numpy as np
import photonforge as pf
import photonforge.typing as pft

from .utils import _core_and_clad_info


@pf.parametric_component
def edge_coupler(
    *,
    start_port_spec: str | pf.PortSpec = "SWG250",
    end_port_spec: str | pf.PortSpec = "RWG1000",
    lower_taper_end_width: pft.Dimension = 2.05,
    lower_taper_length: pft.PositiveDimension = 120.0,
    upper_taper_start_width: pft.Dimension = 0.25,
    upper_taper_length: pft.PositiveDimension = 240.0,
    slab_removal_width: pft.Dimension = 20.0,
    input_ext: pft.Dimension = 0.0,
    technology: pf.Technology | None = None,
    name: str = "",
    model: pf.Model | None = pf.Tidy3DModel(),
) -> pf.Component:
    """Dual layer inverse taper designed for matching with a lensed fiber.

    The taper transitions from a wire to a rib waveguide.

    Args:
        start_port_spec: Port specification describing the wire waveguide.
        end_port_spec: Port specification describing the rib waveguide.
        lower_taper_end_width: Lower taper width at the start of the upper
          taper.
        lower_taper_length: Length of the wire waveguide taper section.
        upper_taper_start_width: Start width of the rib waveguide section.
        upper_taper_length: Length of the rib waveguide taper.
        slab_removal_width: Width of the region where the slab is removed
          close to the coupler (for fabrication in positive tone).
        input_ext: Length of a straight segment extending beyond the lower
          taper.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component.

    Returns:
        Component with the taper, ports, and model.
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
    if isinstance(start_port_spec, str):
        start_port_spec = technology.ports[start_port_spec]
    if isinstance(end_port_spec, str):
        end_port_spec = technology.ports[end_port_spec]
    if input_ext < 0:
        raise ValueError("'input_ext' may not be negative.")
    if slab_removal_width < 0:
        raise ValueError("'slab_removal_width' may not be negative.")

    c = pf.Component(name, technology=technology)
    c.properties.__thumbnail__ = "taper"

    lower_taper_start_width, *_ = _core_and_clad_info(start_port_spec, technology)
    upper_taper_end_width, *_ = _core_and_clad_info(end_port_spec, technology)

    slope = (lower_taper_end_width - lower_taper_start_width) / lower_taper_length
    lower_taper_end_width = lower_taper_start_width + slope * (
        lower_taper_length + upper_taper_length
    )

    length = lower_taper_length + upper_taper_length
    c.add(
        "LN_RIDGE",
        pf.stencil.linear_taper(
            upper_taper_length,
            (upper_taper_start_width, upper_taper_end_width),
        ).translate((lower_taper_length, 0)),
        "LN_SLAB",
        pf.stencil.linear_taper(length, (lower_taper_start_width, lower_taper_end_width)),
    )

    if input_ext > 0:
        c.add(
            "LN_SLAB",
            pf.Rectangle(
                corner1=(-input_ext, -0.5 * lower_taper_start_width),
                corner2=(0, 0.5 * lower_taper_start_width),
            ),
        )

    if slab_removal_width > 0:
        c.add(
            "SLAB_NEGATIVE",
            pf.Rectangle(
                center=(0.5 * (lower_taper_length + upper_taper_length - input_ext), 0),
                size=(lower_taper_length + upper_taper_length + input_ext, slab_removal_width),
            ),
        )

    c.add_port(pf.Port((-input_ext if input_ext > 0 else 0, 0), 0, start_port_spec))
    c.add_port(pf.Port((length, 0), 180, end_port_spec, inverted=True))

    if model is not None:
        c.add_model(model)

    return c


@pf.parametric_component
def gc_focusing_1550(
    *,
    port_spec: str | pf.PortSpec = "RWG1000",
    waveguide_length: pft.Dimension = 10,
    technology: pf.Technology | None = None,
    name: str = "",
    model: pf.Model | None = pf.Tidy3DModel(),
) -> pf.Component:
    """Focusing grating coupler for C band.

    The grating is optimized for TE polarization and launch angle of 14.5°
    in air with respect to the surface normal.

    Args:
        port_spec: Port specification describing the grating waveguide.
        waveguide_length: Length of the waveguide added at the end of the
          grating.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component.

    Returns:
        Component with the grating, ports, and model.
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
    c.properties.__thumbnail__ = "grating_coupler"

    core_width, core_layer, clad_width, clad_layer = _core_and_clad_info(port_spec, technology)

    sin = np.sin(14.5 / 180 * np.pi)
    alpha = np.arcsin(sin / 1.44)
    input_vector = (-np.sin(alpha), 0, -np.cos(alpha))

    grating = [
        p.translate((0.3, 0))
        for p in pf.stencil.apodized_focused_grating(
            teeth_gaps=[0.35, 0.38, 0.47] + [0.564] * 57,
            teeth_widths=[0.685, 0.62, 0.54] + [0.46] * 57,
            n_eff=1.85,
            n_sin=sin,
            focal_length=12.55,
            angle=50.5,
            input_width=core_width,
        )
    ]
    envelope = pf.envelope(grating, 0.5 * (clad_width - core_width))
    c.add(core_layer, *grating, clad_layer, envelope)

    waveguide_length = abs(waveguide_length)
    if waveguide_length > 0:
        for layer, path in port_spec.get_paths((0.3 - waveguide_length, 0)):
            c.add(layer, path.segment((0.3, 0)))

    c.add_port(pf.Port((-waveguide_length, 0), 0, port_spec))
    c.add_port(pf.GaussianPort((20, 0, 0.5), input_vector, 10, polarization_angle=90))

    if model is not None:
        c.add_model(model)

    return c
