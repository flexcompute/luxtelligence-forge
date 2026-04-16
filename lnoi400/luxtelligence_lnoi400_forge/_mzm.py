import warnings

import photonforge as pf
import photonforge.typing as pft

from ._bends import l_bend, s_bend_spline
from ._cpw import trail_cpw, cpw_pad_linear
from ._eo_phase_shifter import eo_phase_shifter
from ._heater import heated_straight
from ._mmi import mmi1x2_optimized1550
from .utils import _cpw_info


@pf.parametric_component
def mzm_unbalanced(
    *,
    splitter: pf.Component | None = None,
    cpw_spec: str | pf.PortSpec = "UniCPW-EO",
    taper_length: pft.PositiveDimension = 100.0,
    modulation_width: pft.PositiveDimension = 2.5,
    modulation_length: pft.PositiveDimension = 7500.0,
    length_imbalance: pft.Coordinate = 100.0,
    bias_tuning_section_length: pft.PositiveDimension = 700.0,
    rf_pad_width: pft.PositiveDimension = 80.0,
    rf_pad_straight_length: pft.PositiveDimension = 10.0,
    rf_pad_taper_length: pft.PositiveDimension = 300.0,
    heater_width: pft.PositiveDimension = 1.0,
    heater_offset: pft.Coordinate = 1.2,
    heater_pad_size: pft.PositiveDimension2D = (75.0, 75.0),
    draw_cpw: bool = True,
    with_t_rails: bool = False,
    with_heater: bool = False,
    technology: pf.Technology | None = None,
    name: str = "",
    model: pf.Model | None = pf.CircuitModel(),
) -> pf.Component:
    """Mach-Zehnder modulator based on the Pockels effect.

    The modulator works in a differential push-pull configuration driven by
    a single GSG line.

    Args:
        splitter: 1×2 MMI splitter used in the modulator. If not set, the
          default MMI is used.
        cpw_spec: Port specification for the CPW transmission line.
        taper_length: Length of the tapering section between the modulation
          and routing waveguides.
        modulation_width: Waveguide core width in the phase modulation
          section.
        modulation_length: Length of the phase modulation section.
        length_imbalance: Length difference between the two arms of the MZI.
        bias_tuning_section_length: Length of the horizontal section that
          can be used for phase tuning.
        rf_pad_width: Width of the central conductor on the pad side.
        rf_pad_straight_length: Length of the straight section of the taper
          on the pad side.
        rf_pad_taper_length: Length of the tapered section.
        draw_cpw: If ``False``, the CPW transmission line is not included.
        with_t_rails: If ``True``, includes T-rails in the CPW.
        with_heater: If ``True``, adds a heater for phase tuning in the
          imbalance section.
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

    if isinstance(cpw_spec, str):
        cpw_spec = technology.ports[cpw_spec]

    if splitter is None:
        splitter = mmi1x2_optimized1550(technology=technology)

    splitter_ports = sorted(splitter.ports.items())
    if len(splitter_ports) < 3:
        raise TypeError("'splitter' is expected to be a component with 3 ports.")
    opt_spec = splitter_ports[0][1].spec
    splitter_port_distance = abs(splitter_ports[2][1].center[1] - splitter_ports[1][1].center[1])

    central_width, tl_gap, _, _, _ = _cpw_info(cpw_spec)
    phase_shifters_distance = central_width + tl_gap
    phase_shifter = eo_phase_shifter(
        opt_spec=opt_spec,
        cpw_spec=cpw_spec,
        taper_length=taper_length,
        modulation_width=modulation_width,
        modulation_length=modulation_length,
        draw_cpw=False,
        with_t_rails=with_t_rails,
        technology=technology,
    )

    scaling = rf_pad_width / central_width
    pad_gap_distance = scaling * (central_width + tl_gap)
    input_s_offset = 0.5 * (pad_gap_distance - splitter_port_distance)
    input_s_bend = s_bend_spline(
        port_spec=opt_spec,
        length=input_s_offset * 3.6,
        offset=input_s_offset,
        straight_length=5.0,
        technology=technology,
    )

    pad_s_straight = 0.5 * rf_pad_straight_length
    pad_s_offset = 0.5 * (phase_shifters_distance - pad_gap_distance)
    pad_s_bend = s_bend_spline(
        port_spec=opt_spec,
        length=rf_pad_straight_length + rf_pad_taper_length - 2 * pad_s_straight,
        offset=pad_s_offset,
        straight_length=pad_s_straight,
        technology=technology,
    )

    bend = l_bend(
        port_spec=opt_spec, effective_radius=75, euler_fraction=1.0, technology=technology
    )

    short_length = 20.0
    long_straight = pf.parametric.straight(
        port_spec=opt_spec,
        length=short_length + abs(length_imbalance) / 2,
        technology=technology,
    )
    short_straight = pf.parametric.straight(
        port_spec=opt_spec, length=short_length, technology=technology
    )

    bias = pf.parametric.straight(
        port_spec=opt_spec,
        length=bias_tuning_section_length,
        technology=technology,
    )
    heated = heated_straight(
        port_spec=opt_spec,
        length=bias_tuning_section_length,
        heater_width=heater_width,
        heater_offset=heater_offset,
        pad_size=heater_pad_size,
        draw_heater=with_heater,
        technology=technology,
    )

    if length_imbalance > 0:
        top_straight = long_straight
        bot_straight = short_straight
        top_bias = pf.Reference(heated, x_reflection=True)
        bot_bias = pf.Reference(bias)
    else:
        top_straight = short_straight
        bot_straight = long_straight
        top_bias = pf.Reference(bias)
        bot_bias = pf.Reference(heated)

    c = pf.Component(name, technology=technology)
    c.properties.__thumbnail__ = "mzm"

    ps_top = pf.Reference(phase_shifter, (0, 0.5 * phase_shifters_distance))
    ps_bot = pf.Reference(phase_shifter, (0, -0.5 * phase_shifters_distance))
    c.add(ps_top, ps_bot)

    ref_top = c.add_reference(pad_s_bend).connect("P1", ps_top["P0"])
    ref_top = c.add_reference(input_s_bend).connect("P1", ref_top["P0"])

    top_port = 2 if splitter_ports[2][1].center[1] > splitter_ports[1][1].center[1] else 1
    ref_input = c.add_reference(splitter).connect(splitter_ports[top_port][0], ref_top["P0"])
    c.add_port(ref_input[splitter_ports[0][0]])

    ref_bot = c.add_reference(pad_s_bend).mirror().connect("P1", ps_bot["P0"])
    ref_bot = c.add_reference(input_s_bend).mirror().connect("P1", ref_bot["P0"])

    ref_top = c.add_reference(pad_s_bend).mirror().connect("P0", ps_top["P1"])
    ref_top = c.add_reference(bend).connect("P0", ref_top["P1"])
    ref_top = c.add_reference(top_straight).connect("P0", ref_top["P1"])
    ref_top = c.add_reference(bend).connect("P1", ref_top["P1"])
    c.add(top_bias)
    top_bias.connect("P0", ref_top["P0"])
    ref_top = c.add_reference(bend).connect("P1", top_bias["P1"])
    ref_top = c.add_reference(top_straight).connect("P0", ref_top["P0"])

    ref_bot = c.add_reference(pad_s_bend).connect("P0", ps_bot["P1"])
    ref_bot = c.add_reference(bend).connect("P1", ref_bot["P1"])
    ref_bot = c.add_reference(bot_straight).connect("P0", ref_bot["P0"])
    ref_bot = c.add_reference(bend).connect("P0", ref_bot["P1"])
    c.add_reference(bot_bias)
    bot_bias.connect("P0", ref_bot["P1"])
    ref_bot = c.add_reference(bend).connect("P0", bot_bias["P1"])
    ref_bot = c.add_reference(bot_straight).connect("P0", ref_bot["P1"])

    out_bend = l_bend(
        port_spec=opt_spec,
        effective_radius=ref_top["P1"].center[1] - 0.5 * splitter_port_distance,
        euler_fraction=1.0,
        technology=technology,
    )

    ref_top = c.add_reference(out_bend).connect("P0", ref_top["P1"])
    ref_bot = c.add_reference(out_bend).connect("P1", ref_bot["P1"])

    ref_output = c.add_reference(splitter).connect(splitter_ports[top_port][0], ref_bot["P0"])
    c.add_port(ref_output[splitter_ports[0][0]])

    if with_heater:
        if length_imbalance > 0:
            c.add_terminal({"heater_0": top_bias["T0"], "heater_1": top_bias["T1"]})
        else:
            c.add_terminal({"heater_0": bot_bias["T0"], "heater_1": bot_bias["T1"]})

    if draw_cpw:
        pad = cpw_pad_linear(
            cpw_spec=cpw_spec,
            pad_width=rf_pad_width,
            straight_length=rf_pad_straight_length,
            taper_length=rf_pad_taper_length,
            technology=technology,
        )
        if with_t_rails:
            tl = trail_cpw(
                port_spec=cpw_spec, length=modulation_length, technology=technology
            )
        else:
            tl = pf.parametric.straight(
                port_spec=cpw_spec, length=modulation_length, technology=technology
            )

        tl_ref = c.add_reference(tl)
        pad0 = c.add_reference(pad).connect("E0", tl_ref["E0"])
        pad1 = c.add_reference(pad).mirror().connect("E0", tl_ref["E1"])
        c.add_terminal(
            {
                "G0_in": pad0["G0"],
                "S_in": pad0["S"],
                "G1_in": pad0["G1"],
                "G0_out": pad1["G0"],
                "S_out": pad1["S"],
                "G1_out": pad1["G1"],
            }
        )

    if model is not None:
        c.add_model(model)

    return c


@pf.parametric_component
def mzm_unbalanced_high_speed(
    *,
    splitter: pf.Component | None = None,
    cpw_spec: str | pf.PortSpec = "UniCPW-HS",
    taper_length: pft.PositiveDimension = 100.0,
    modulation_width: pft.PositiveDimension = 2.5,
    modulation_length: pft.PositiveDimension = 7500.0,
    length_imbalance: pft.Coordinate = 100.0,
    bias_tuning_section_length: pft.PositiveDimension = 700.0,
    rf_pad_width: pft.PositiveDimension = 80.0,
    rf_pad_straight_length: pft.PositiveDimension = 10.0,
    rf_pad_taper_length: pft.PositiveDimension = 300.0,
    heater_width: pft.PositiveDimension = 1.0,
    heater_offset: pft.Coordinate = 1.2,
    heater_pad_size: pft.PositiveDimension2D = (75.0, 75.0),
    draw_cpw: bool = True,
    with_t_rails: bool = True,
    with_heater: bool = False,
    technology: pf.Technology | None = None,
    name: str = "",
    model: pf.Model | None = pf.CircuitModel(),
) -> pf.Component:
    """High-speed Mach-Zehnder modulator based on the Pockels effect.

    The modulator works in a differential push-pull configuration driven by
    a single GSG line.

    Args:
        splitter: 1×2 MMI splitter used in the modulator. If not set, the
          default MMI is used.
        cpw_spec: Port specification for the CPW transmission line.
        taper_length: Length of the tapering section between the modulation
          and routing waveguides.
        modulation_width: Waveguide core width in the phase modulation
          section.
        modulation_length: Length of the phase modulation section.
        length_imbalance: Length difference between the two arms of the MZI.
        bias_tuning_section_length: Length of the horizontal section that
          can be used for phase tuning.
        rf_pad_width: Width of the central conductor on the pad side.
        rf_pad_straight_length: Length of the straight section of the taper
          on the pad side.
        rf_pad_taper_length: Length of the tapered section.
        draw_cpw: If ``False``, the CPW transmission line is not included.
        with_t_rails: If ``True``, includes T-rails in the CPW.
        with_heater: If ``True``, adds a heater for phase tuning in the
          imbalance section.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component.

    Returns:
        Component with the modulator, ports, and model.
    """
    c = mzm_unbalanced(
        splitter=splitter,
        cpw_spec=cpw_spec,
        taper_length=taper_length,
        modulation_width=modulation_width,
        modulation_length=modulation_length,
        length_imbalance=length_imbalance,
        bias_tuning_section_length=bias_tuning_section_length,
        rf_pad_width=rf_pad_width,
        rf_pad_straight_length=rf_pad_straight_length,
        rf_pad_taper_length=rf_pad_taper_length,
        heater_width=heater_width,
        heater_offset=heater_offset,
        heater_pad_size=heater_pad_size,
        draw_cpw=draw_cpw,
        with_t_rails=with_t_rails,
        with_heater=with_heater,
        technology=technology,
        name=name,
        model=model,
    )
    c.name = ""
    return c
