from collections.abc import Sequence
from warnings import warn

import photonforge as pf
import photonforge.typing as pft

from .utils import _core_and_clad_info


def ring_resonator(
    bus_spec,
    ring_spec,
    gap,
    ring_radius,
    bus_length,
    technology,
    name,
    model,
    inner_models,
):
    if technology is None:
        technology = pf.config.default_technology
        if "LTOI300" not in technology.name:
            warn(
                f"Current default technology {technology.name} does not seem supported by the "
                "Luxtelligence LTOI300 component library.",
                RuntimeWarning,
                3,
            )
    if isinstance(bus_spec, str):
        bus_spec = technology.ports[bus_spec]
    if ring_spec is None:
        ring_spec = bus_spec
    elif isinstance(ring_spec, str):
        ring_spec = technology.ports[ring_spec]

    c = pf.Component(name, technology=technology)
    c.properties.__thumbnail__ = "mrr"

    bus_core_width, *_ = _core_and_clad_info(bus_spec, technology)
    ring_core_width, *_ = _core_and_clad_info(ring_spec, technology)

    coupled = pf.parametric.ring_coupler(
        port_spec=(bus_spec, ring_spec),
        coupling_distance=0.5 * (bus_core_width + ring_core_width) + gap,
        radius=ring_radius,
        bus_length=ring_radius if bus_length is None else (0.5 * bus_length),
        coupling_length=0.0,
        euler_fraction=0.0,
        port_bends=True,
        technology=technology,
        name="",
        model=inner_models[0],
    )

    uncoupled = pf.parametric.ring_coupler(
        port_spec=ring_spec,
        coupling_distance=0.0,
        radius=ring_radius,
        bus_length=0.0,
        coupling_length=0.0,
        euler_fraction=0.0,
        port_bends=True,
        technology=technology,
        name="",
        model=inner_models[1],
    )

    r0 = pf.Reference(coupled, rotation=90)
    r1 = pf.Reference(uncoupled).connect("P0", r0["P3"])
    c.add(r0, r1)
    c.add_port([r0["P0"], r0["P2"]])

    c.add_model(model)
    return c


_wg_model = pf.WaveguideModel()
_coupler_model = pf.Tidy3DModel(port_symmetries=[(2, 3, 0, 1)])
_inner_models = (
    pf.DirectionalCouplerCircuitModel(arms_model=_wg_model, coupling_region_model=_coupler_model),
    _wg_model,
)


@pf.parametric_component
def ring_resonator_single_mode_point_coupler_oband(
    *,
    bus_spec: str | pf.PortSpec = "RWG700",
    ring_spec: str | pf.PortSpec | None = None,
    gap: pft.Coordinate = 1.05,
    ring_radius: pft.PositiveDimension = 200.0,
    bus_length: pft.PositiveDimension | None = None,
    technology: pf.Technology | None = None,
    name: str = "",
    model: pf.Model = pf.CircuitModel(),
    inner_models: pft.annotate(Sequence[pf.Model], minItems=2, maxItems=2) = _inner_models,
) -> pf.Component:
    """Evanescent-coupled ring resonator for O band.

    Args:
        bus_spec: Port specification describing the bus cross-section.
        ring_spec: Port specification describing the ring cross-section.
        gap: Distance between waveguide cores (edge-to-edge) in the coupling
          region.
        ring_radius: Ring radius (measured at the center of the core).
        slab_width: Slab width for the ring waveguide.
        bus_length: Length of the bus waveguide. If ``None``, defaults to
          ``2 * ring_radius``.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component.
        inner_models: Models to be used on the 2 subcomponents of the ring.
          The first is used on the ring half coupled to the bus waveguide,
          and the second on the other ring half.

    Returns:
        Component with the taper, ports and model.
    """
    return ring_resonator(
        bus_spec,
        ring_spec,
        gap,
        ring_radius,
        bus_length,
        technology,
        name,
        model,
        inner_models,
    )


_multimode_ring_o = pf.PortSpec(
    description="LT single mode rib for O band",
    width=4,
    limits=(-1.2, 1.5),
    num_modes=3,
    target_neff=2.2,
    path_profiles=((1.5, 0, (2, 10)), (12 + 1.5, 0, (3, 10))),
    default_radius=200,
)


@pf.parametric_component
def ring_resonator_multimode_point_coupler_oband(
    *,
    bus_spec: str | pf.PortSpec = "RWG700",
    ring_spec: str | pf.PortSpec | None = _multimode_ring_o,
    gap: pft.Coordinate = 0.75,
    ring_radius: pft.PositiveDimension = 200.0,
    bus_length: pft.PositiveDimension | None = None,
    technology: pf.Technology | None = None,
    name: str = "",
    model: pf.Model = pf.CircuitModel(),
    inner_models: pft.annotate(Sequence[pf.Model], minItems=2, maxItems=2) = _inner_models,
) -> pf.Component:
    """Evanescent-coupled ring resonator for O band.

    Args:
        bus_spec: Port specification describing the bus cross-section.
        ring_spec: Port specification describing the ring cross-section.
        gap: Distance between waveguide cores (edge-to-edge) in the coupling
          region.
        ring_radius: Ring radius (measured at the center of the core).
        slab_width: Slab width for the ring waveguide.
        bus_length: Length of the bus waveguide. If ``None``, defaults to
          ``2 * ring_radius``.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component.
        inner_models: Models to be used on the 2 subcomponents of the ring.
          The first is used on the ring half coupled to the bus waveguide,
          and the second on the other ring half.

    Returns:
        Component with the taper, ports and model.
    """
    return ring_resonator(
        bus_spec,
        ring_spec,
        gap,
        ring_radius,
        bus_length,
        technology,
        name,
        model,
        inner_models,
    )


@pf.parametric_component
def ring_resonator_single_mode_point_coupler_cband(
    *,
    bus_spec: str | pf.PortSpec = "RWG900",
    ring_spec: str | pf.PortSpec | None = None,
    gap: pft.Coordinate = 1.5,
    ring_radius: pft.PositiveDimension = 200.0,
    bus_length: pft.PositiveDimension | None = None,
    technology: pf.Technology | None = None,
    name: str = "",
    model: pf.Model = pf.CircuitModel(),
    inner_models: pft.annotate(Sequence[pf.Model], minItems=2, maxItems=2) = _inner_models,
) -> pf.Component:
    """Evanescent-coupled ring resonator for O band.

    Args:
        bus_spec: Port specification describing the bus cross-section.
        ring_spec: Port specification describing the ring cross-section.
        gap: Distance between waveguide cores (edge-to-edge) in the coupling
          region.
        ring_radius: Ring radius (measured at the center of the core).
        slab_width: Slab width for the ring waveguide.
        bus_length: Length of the bus waveguide. If ``None``, defaults to
          ``2 * ring_radius``.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component.
        inner_models: Models to be used on the 2 subcomponents of the ring.
          The first is used on the ring half coupled to the bus waveguide,
          and the second on the other ring half.

    Returns:
        Component with the taper, ports and model.
    """
    return ring_resonator(
        bus_spec,
        ring_spec,
        gap,
        ring_radius,
        bus_length,
        technology,
        name,
        model,
        inner_models,
    )


_multimode_ring_c = pf.PortSpec(
    description="LT single mode rib for C band",
    width=5,
    limits=(-1.4, 1.7),
    num_modes=3,
    target_neff=2.2,
    path_profiles=((1.5, 0, (2, 10)), (12 + 1.5, 0, (3, 10))),
    default_radius=200,
)


@pf.parametric_component
def ring_resonator_multimode_point_coupler_cband(
    *,
    bus_spec: str | pf.PortSpec = "RWG900",
    ring_spec: str | pf.PortSpec | None = _multimode_ring_c,
    gap: pft.Coordinate = 1.2,
    ring_radius: pft.PositiveDimension = 200.0,
    bus_length: pft.PositiveDimension | None = None,
    technology: pf.Technology | None = None,
    name: str = "",
    model: pf.Model = pf.CircuitModel(),
    inner_models: pft.annotate(Sequence[pf.Model], minItems=2, maxItems=2) = _inner_models,
) -> pf.Component:
    """Evanescent-coupled ring resonator for O band.

    Args:
        bus_spec: Port specification describing the bus cross-section.
        ring_spec: Port specification describing the ring cross-section.
        gap: Distance between waveguide cores (edge-to-edge) in the coupling
          region.
        ring_radius: Ring radius (measured at the center of the core).
        slab_width: Slab width for the ring waveguide.
        bus_length: Length of the bus waveguide. If ``None``, defaults to
          ``2 * ring_radius``.
        technology: Component technology. If ``None``, the default
          technology is used.
        name: Component name.
        model: Model to be used with this component.
        inner_models: Models to be used on the 2 subcomponents of the ring.
          The first is used on the ring half coupled to the bus waveguide,
          and the second on the other ring half.

    Returns:
        Component with the taper, ports and model.
    """
    return ring_resonator(
        bus_spec,
        ring_spec,
        gap,
        ring_radius,
        bus_length,
        technology,
        name,
        model,
        inner_models,
    )
