from collections.abc import Sequence as Sequence
from warnings import warn

import photonforge as pf
import photonforge.typing as pft

from ._cpw import TRailSpec, straight_cpw, cpw_pad, cpw_termination


def base_eo_phase_shifter(
    opt_spec: str | pf.PortSpec,
    cpw_spec: str | pf.PortSpec,
    modulation_length: pft.PositiveDimension,
    modulation_bulge: pft.Coordinate,
    modulation_bulge_taper: pft.Dimension,
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

    if isinstance(opt_spec, str):
        opt_spec = technology.ports[opt_spec]

    if isinstance(cpw_spec, str):
        cpw_spec = technology.ports[cpw_spec]

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
        waveguide_position="top",
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
        waveguide_position="top",
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

    c = pf.Component(name, technology)
    c.properties.__thumbnail__ = "eo-ps"

    cpw_ref = c.add_reference(cpw)
    pad0 = c.add_reference(pad).mirror().connect("E0", cpw_ref["E0"])
    c.add_port(pad0["P1"])

    c.add_terminal(pad0["signal"], "signal_l")
    c.add_terminal(pad0["gnd_b"], "gnd_tl")
    c.add_terminal(pad0["gnd_t"], "gnd1_bl")

    if termination is not None:
        c.add_reference(termination).connect("E0", cpw_ref["E1"])
        extension = pf.parametric.straight(
            port_spec=opt_spec, length=termination.size()[0], technology=technology
        )
        ext_ref = c.add_reference(extension).connect("P0", cpw_ref["P1"])
        c.add_port(ext_ref["P1"])
    else:
        pad1 = c.add_reference(pad).connect("E0", cpw_ref["E1"])
        c.add_terminal(pad1["signal"], "signal_r")
        c.add_terminal(pad1["gnd_b"], "gnd0_br")
        c.add_terminal(pad1["gnd_t"], "gnd1_tr")
        c.add_port(pad1["P1"])

    return c


@pf.parametric_component
def terminated_eo_phase_shifter_oband(
    *,
    opt_spec: str | pf.PortSpec = "RWG700",
    cpw_spec: str | pf.PortSpec = "UniCPW-EO-oband",
    modulation_length: pft.PositiveDimension = 5000,
    modulation_bulge: pft.Coordinate = 1.8,
    modulation_bulge_taper: pft.Dimension = 100,
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
    """Terminated electro-optic phase shifter for O band.

    Args:
        opt_spec: Port specification for the optical waveguide.
        cpw_spec: Port specification for the CPW.
        modulation_length: Length of the modulation section.
        modulation_bulge: Width added to the waveguide in the modulation
          region.
        modulation_bulge_taper: Length of the bulge transition taper.
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
        EO phase shifter component.
    """
    return base_eo_phase_shifter(
        opt_spec,
        cpw_spec,
        modulation_length,
        modulation_bulge,
        modulation_bulge_taper,
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
def unterminated_eo_phase_shifter_oband(
    *,
    opt_spec: str | pf.PortSpec = "RWG700",
    cpw_spec: str | pf.PortSpec = "UniCPW-EO-oband",
    modulation_length: pft.PositiveDimension = 5000,
    modulation_bulge: pft.Coordinate = 1.8,
    modulation_bulge_taper: pft.Dimension = 100,
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
    """Unterminated electro-optic phase shifter for O band.

    Args:
        opt_spec: Port specification for the optical waveguide.
        cpw_spec: Port specification for the CPW.
        modulation_length: Length of the modulation section.
        modulation_bulge: Width added to the waveguide in the modulation
          region.
        modulation_bulge_taper: Length of the bulge transition taper.
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
        EO phase shifter component.
    """
    return base_eo_phase_shifter(
        opt_spec,
        cpw_spec,
        modulation_length,
        modulation_bulge,
        modulation_bulge_taper,
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
def terminated_eo_phase_shifter_cband(
    *,
    opt_spec: str | pf.PortSpec = "RWG900",
    cpw_spec: str | pf.PortSpec = "UniCPW-EO-cband",
    modulation_length: pft.PositiveDimension = 5000,
    modulation_bulge: pft.Coordinate = 1.6,
    modulation_bulge_taper: pft.Dimension = 100,
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
    """Terminated electro-optic phase shifter for C band.

    Args:
        opt_spec: Port specification for the optical waveguide.
        cpw_spec: Port specification for the CPW.
        modulation_length: Length of the modulation section.
        modulation_bulge: Width added to the waveguide in the modulation
          region.
        modulation_bulge_taper: Length of the bulge transition taper.
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
        EO phase shifter component.
    """
    return base_eo_phase_shifter(
        opt_spec,
        cpw_spec,
        modulation_length,
        modulation_bulge,
        modulation_bulge_taper,
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
def unterminated_eo_phase_shifter_cband(
    *,
    opt_spec: str | pf.PortSpec = "RWG900",
    cpw_spec: str | pf.PortSpec = "UniCPW-EO-cband",
    modulation_length: pft.PositiveDimension = 5000,
    modulation_bulge: pft.Coordinate = 1.6,
    modulation_bulge_taper: pft.Dimension = 100,
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
    """Unterminated electro-optic phase shifter for C band.

    Args:
        opt_spec: Port specification for the optical waveguide.
        cpw_spec: Port specification for the CPW.
        modulation_length: Length of the modulation section.
        modulation_bulge: Width added to the waveguide in the modulation
          region.
        modulation_bulge_taper: Length of the bulge transition taper.
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
        EO phase shifter component.
    """
    return base_eo_phase_shifter(
        opt_spec,
        cpw_spec,
        modulation_length,
        modulation_bulge,
        modulation_bulge_taper,
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
