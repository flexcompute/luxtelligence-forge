import warnings

import photonforge as pf
import photonforge.typing as pft

from ._cpw import trail_cpw, cpw_pad_linear
from .utils import _core_and_clad_info, _cpw_info


@pf.parametric_component
def eo_phase_shifter(
    *,
    opt_spec: str | pf.PortSpec = "RWG1000",
    cpw_spec: str | pf.PortSpec = "UniCPW-EO",
    taper_length: pft.PositiveDimension = 100.0,
    modulation_width: pft.PositiveDimension = 2.5,
    modulation_length: pft.PositiveDimension = 7500.0,
    rf_pad_width: pft.PositiveDimension = 80.0,
    rf_pad_straight_length: pft.PositiveDimension = 10.0,
    rf_pad_taper_length: pft.PositiveDimension = 190.0,
    draw_cpw: bool = True,
    with_t_rails: bool = False,
    technology: pf.Technology | None = None,
    name: str = "",
    model: pf.Model | None = pf.CircuitModel(),
) -> pf.Component:
    """Phase modulator based on the Pockels effect.

    The modulator waveguide is located within the upper gap of an RF
    coplanar waveguide.

    Args:
        opt_spec: Port specification for the optical waveguide.
        cpw_spec: Port specification for the CPW transmission line.
        taper_length: Length of the tapering section between the modulation
          and routing waveguides.
        modulation_width: Waveguide core width in the phase modulation
          section.
        modulation_length: Length of the phase modulation section.
        rf_pad_width: Width of the central conductor on the bonding side.
        rf_pad_straight_length: Length of the straight section of the RF
          pad, opposite to the transmission line.
        rf_pad_taper_length: Length of the tapered section of the RF pad.
        draw_cpw: If ``False``, the CPW transmission line is not included.
        with_t_rails: If ``True``, includes T-rails in the CPW.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component.

    Returns:
        Component with the modulator, ports, and model.
    """
    if taper_length <= 0:
        raise ValueError("'taper_length' must be positive.")
    if modulation_length <= 2 * taper_length:
        raise ValueError("'modulation_length' must be larger than '2 * taper_length'.")

    if technology is None:
        technology = pf.config.default_technology
        if "LNOI400" not in technology.name:
            warnings.warn(
                f"Current default technology {technology.name} does not seem supported by the "
                "Luxtelligence LNOI400 component library.",
                RuntimeWarning,
                1,
            )
    if isinstance(opt_spec, str):
        opt_spec = technology.ports[opt_spec]
    if isinstance(cpw_spec, str):
        cpw_spec = technology.ports[cpw_spec]

    core_width, core_layer, *_ = _core_and_clad_info(opt_spec, technology)
    added_width = modulation_width - core_width
    mod_spec = opt_spec.copy()
    path_profiles = opt_spec.path_profiles_list()
    mod_spec.path_profiles = [
        ((w + added_width) if a == core_layer else w, g, a) for w, g, a in path_profiles
    ]

    taper = pf.parametric.transition(
        port_spec1=opt_spec,
        port_spec2=mod_spec,
        length=taper_length,
        technology=technology,
    )
    straight = pf.parametric.straight(
        port_spec=mod_spec,
        length=modulation_length - 2 * taper_length,
        technology=technology,
    )

    c = pf.Component(name, technology=technology)
    c.properties.__thumbnail__ = "eo_ps"

    ref = c.add_reference(taper)
    c.add_port(ref["P0"])
    ref = c.add_reference(straight).connect("P0", ref["P1"])
    ref = c.add_reference(taper).connect("P1", ref["P1"])
    c.add_port(ref["P0"])

    if draw_cpw:
        central_width, gap, _, _, _ = _cpw_info(cpw_spec)
        if with_t_rails:
            tl = trail_cpw(
                port_spec=cpw_spec, length=modulation_length, technology=technology
            )
        else:
            tl = pf.parametric.straight(
                port_spec=cpw_spec, length=modulation_length, technology=technology
            )
        pad = cpw_pad_linear(
            cpw_spec=cpw_spec,
            pad_width=rf_pad_width,
            straight_length=rf_pad_straight_length,
            taper_length=rf_pad_taper_length,
            technology=technology,
        )
        ref = pf.Reference(tl, (0, -0.5 * (central_width + gap)))
        c.add(ref)
        pad0 = c.add_reference(pad).connect("E0", ref["E0"])
        pad1 = c.add_reference(pad).connect("E0", ref["E1"])
        c.add_terminal(
            {
                "G0_in": pad0["G0"],
                "S_in": pad0["S"],
                "G1_in": pad0["G1"],
                "G0_out": pad1["G1"],
                "S_out": pad1["S"],
                "G1_out": pad1["G0"],
            }
        )

    if model is not None:
        c.add_model(model)

    return c


@pf.parametric_component
def eo_phase_shifter_high_speed(
    *,
    opt_spec: str | pf.PortSpec = "RWG1000",
    cpw_spec: str | pf.PortSpec = "UniCPW-HS",
    taper_length: pft.PositiveDimension = 100.0,
    modulation_width: pft.PositiveDimension = 2.5,
    modulation_length: pft.PositiveDimension = 7500.0,
    rf_pad_width: pft.PositiveDimension = 80.0,
    rf_pad_straight_length: pft.PositiveDimension = 10.0,
    rf_pad_taper_length: pft.PositiveDimension = 190.0,
    draw_cpw: bool = True,
    with_t_rails: bool = True,
    technology: pf.Technology | None = None,
    name: str = "",
    model: pf.Model | None = pf.CircuitModel(),
) -> pf.Component:
    """High-speed phase modulator based on the Pockels effect.

    The modulator waveguide is located within the upper gap of an RF
    coplanar waveguide.

    Args:
        opt_spec: Port specification for the optical waveguide.
        cpw_spec: Port specification for the CPW transmission line.
        taper_length: Length of the tapering section between the modulation
          and routing waveguides.
        modulation_width: Waveguide core width in the phase modulation
          section.
        modulation_length: Length of the phase modulation section.
        rf_pad_width: Width of the central conductor on the bonding side.
        rf_pad_straight_length: Length of the straight section of the RF
          pad, opposite to the transmission line.
        rf_pad_taper_length: Length of the tapered section of the RF pad.
        draw_cpw: If ``False``, the CPW transmission line is not included.
        with_t_rails: If ``True``, includes T-rails in the CPW.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component.

    Returns:
        Component with the modulator, ports, and model.
    """
    c = eo_phase_shifter(
        opt_spec=opt_spec,
        cpw_spec=cpw_spec,
        taper_length=taper_length,
        modulation_width=modulation_width,
        modulation_length=modulation_length,
        rf_pad_width=rf_pad_width,
        rf_pad_straight_length=rf_pad_straight_length,
        rf_pad_taper_length=rf_pad_taper_length,
        draw_cpw=draw_cpw,
        with_t_rails=with_t_rails,
        technology=technology,
        name=name,
        model=model,
    )
    c.name = ""
    return c
