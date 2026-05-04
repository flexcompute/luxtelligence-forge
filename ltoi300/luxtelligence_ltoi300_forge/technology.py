from typing import Literal

import tidy3d as td
import photonforge as pf
import photonforge.typing as pft
from ._layers import _layers

_Medium = pft.Medium | dict[Literal["optical", "electrical"], pft.Medium]

_litao3_o = td.PoleResidue(
    eps_inf=1.0,
    poles=(
        (
            (-128.31667601800837 - 1.159741683521218e16j),
            (450.9968400106222 + 2.031278998762267e16j),
        ),
        ((-1.0542028796810354 - 119344671377731.11j), 326801694935530.4j),
    ),
    frequency_range=(75e12, 650e12),
)

_litao3_e = td.PoleResidue(
    eps_inf=2.1784044,
    poles=(
        ((-738327.1118742588 - 105532992666189.89j), (-76720.69102847303 + 377813754248090.94j)),
        ((-13726680.358478123 - 9768105711143944j), (30325584.214157067 + 1.146178065089112e16j)),
    ),
    frequency_range=(75e12, 650e12),
)


@pf.parametric_technology
def ltoi300(
    *,
    lt_thickness: pft.PositiveDimension = 0.3,
    slab_thickness: pft.PositiveDimension = 0.12,
    sidewall_angle: pft.Angle = 20,
    oxide_thickness: pft.PositiveDimension = 2.5,
    m1_thickness: pft.PositiveDimension = 0.9,
    m2_thickness: pft.PositiveDimension = 0.9,
    hrm_thickness: pft.PositiveDimension = 0.1,
    m1_oxide_thickness: pft.PositiveDimension = 1.0,
    m2_oxide_thickness: pft.PositiveDimension = 0.3,
    box_thickness: pft.PositiveDimension = 7.0,
    via_sidewall_angle: pft.Angle = 45,
    sio2: _Medium = {
        "optical": td.material_library["SiO2"]["Palik_Lossless"].updated_copy(
            viz_spec=td.VisualizationSpec(facecolor="#8dc2f7")
        ),
        "electrical": td.Medium(
            permittivity=3.9, name="SiO2", viz_spec=td.VisualizationSpec(facecolor="#8dc2f7")
        ),
    },
    si: _Medium = {
        "optical": td.material_library["cSi"]["Li1993_293K"].updated_copy(
            viz_spec=td.VisualizationSpec(facecolor="#060534")
        ),
        "electrical": td.Medium(
            permittivity=11.7, name="Si", viz_spec=td.VisualizationSpec(facecolor="#060534")
        ),
    },
    lt: _Medium = {
        "optical": td.AnisotropicMedium(
            xx=_litao3_o,
            yy=_litao3_e,
            zz=_litao3_o,
            viz_spec=td.VisualizationSpec(facecolor="#5d179a"),
        ),
        "electrical": td.AnisotropicMedium(
            xx=td.Medium(permittivity=51),
            yy=td.Medium(permittivity=44),
            zz=td.Medium(permittivity=51),
            viz_spec=td.VisualizationSpec(facecolor="#5d179a"),
        ),
    },
    metal: _Medium = {
        "optical": td.material_library["Au"]["JohnsonChristy1972"].updated_copy(
            viz_spec=td.VisualizationSpec(facecolor="#f8b50c")
        ),
        "electrical": td.LossyMetalMedium(
            conductivity=41,
            frequency_range=[0.1e9, 300e9],
            viz_spec=td.VisualizationSpec(facecolor="#f8b50c"),
        ),
    },
    hr_metal: _Medium = {
        "optical": td.material_library["Pt"]["Werner2009"].updated_copy(
            viz_spec=td.VisualizationSpec(facecolor="#778195")
        ),
        "electrical": td.LossyMetalMedium(
            conductivity=7.252,
            frequency_range=[0.1e9, 100e9],
            viz_spec=td.VisualizationSpec(facecolor="#778195"),
        ),
    },
    opening: pft.Medium = td.Medium(permittivity=1.0, name="Opening"),
) -> pf.Technology:
    """Create a technology for the LTOI300 PDK.

    Args:
        lt_thickness: LiTaO₃ layer thickness.
        slab_thickness: Partially etched slab thickness in LiTaO₃.
        sidewall_angle: Sidewall angle for LiTaO₃ etching.
        oxide_thickness: Top oxide thickness above the LiTaO₃ layer.
        m1_thickness: Metal 1 thickness.
        m2_thickness: Metal 2 thickness.
        hrm_thickness: High-resistivity metal thickness.
        m1_oxide_thickness: Thickness of oxide above M1.
        m2_oxide_thickness: Additional oxide thickness below M2.
        box_thickness: Thickness of the bottom oxide clad.
        via_sidewall_angle: Sidewall angle  for via openings.
          and via layers.
        sio2: Oxide and background medium.
        si: Silicon medium.
        lt: LiTaO₃ medium.
        metal: Medium for metals 1 and 2.
        hr_metal: High-resistivity metal.
        opening: Medium for openings.

    Returns:
        Technology: LTOI300 technology definition.
    """
    layers = {k: v.copy() for k, v in _layers.items()}

    extrusion_specs = []

    bounds = pf.MaskSpec()

    z_m1_top = slab_thickness + m1_thickness

    z_hrm = slab_thickness + oxide_thickness
    z_m2 = z_hrm + m2_oxide_thickness
    z_m2_hrm = z_m2 + hrm_thickness
    z_m2_m1 = z_m1_top + m1_oxide_thickness

    m1_mask = pf.MaskSpec((20, 0))
    m2_mask = pf.MaskSpec((22, 0))
    hrm_mask = pf.MaskSpec((23, 0))
    v2_mask = pf.MaskSpec((40, 0))
    v3_mask = pf.MaskSpec((41, 0))

    # m1_open = m1_mask - (m2_mask + v2_mask**dilation)
    full_lt_mask = pf.MaskSpec([(2, 10), (4, 0)], [], "+")
    slab_etch_mask = pf.MaskSpec((3, 11), (3, 10), "-")

    extrusion_specs = [
        pf.ExtrusionSpec(bounds, si, (-pf.Z_INF, 0)),
        pf.ExtrusionSpec(bounds, sio2, (-box_thickness, 0)),
        # M2
        pf.ExtrusionSpec(v2_mask, metal, (z_m1_top, z_m1_top + m2_thickness)),
        pf.ExtrusionSpec(
            m2_mask - m1_mask - hrm_mask,
            metal,
            (z_m1_top, z_m2 + m2_thickness),
            via_sidewall_angle,
        ),
        pf.ExtrusionSpec(
            m2_mask * m1_mask - v2_mask,
            metal,
            (z_m1_top + m2_thickness, z_m2_m1 + m2_thickness),
            via_sidewall_angle,
        ),
        # First oxide layer
        pf.ExtrusionSpec(
            m1_mask - v2_mask,
            sio2,
            (z_m1_top, z_m1_top + m1_oxide_thickness),
            via_sidewall_angle,
        ),
        pf.ExtrusionSpec(bounds - m1_mask, sio2, (slab_thickness, z_hrm), via_sidewall_angle),
        # M2
        pf.ExtrusionSpec(
            m2_mask * hrm_mask - v3_mask,
            metal,
            (z_hrm, z_m2_hrm + m2_thickness),
            via_sidewall_angle,
        ),
        pf.ExtrusionSpec(
            v3_mask, metal, (z_hrm + hrm_thickness, z_hrm + hrm_thickness + m2_thickness)
        ),
        # Second oxide layer
        pf.ExtrusionSpec(
            m2_mask - (m1_mask + v2_mask + v3_mask),
            sio2,
            (z_m1_top + m1_oxide_thickness, z_hrm + m2_oxide_thickness),
            via_sidewall_angle,
        ),
        pf.ExtrusionSpec(
            m2_mask * hrm_mask - v3_mask,
            sio2,
            (z_hrm, z_hrm + hrm_thickness + m2_oxide_thickness),
            via_sidewall_angle,
        ),
        # Heater
        pf.ExtrusionSpec(hrm_mask, hr_metal, (z_hrm, z_hrm + hrm_thickness), via_sidewall_angle),
        # M1
        pf.ExtrusionSpec(m1_mask, metal, (slab_thickness, z_m1_top)),
        # Optical layers
        pf.ExtrusionSpec(bounds, lt, (0, slab_thickness), 0),
        pf.ExtrusionSpec(full_lt_mask, lt, (0, lt_thickness), sidewall_angle),
        pf.ExtrusionSpec(slab_etch_mask, sio2, (0, lt_thickness), -sidewall_angle),
    ]

    technology = pf.Technology("LTOI300", "2.1.0", layers, extrusion_specs, {}, opening)
    technology.ports = {
        "RWG900": pf.PortSpec(
            description="LT single mode rib for C band",
            width=4,
            limits=(-1.7 + lt_thickness, 1.7),
            num_modes=1,
            target_neff=2.2,
            path_profiles=((0.9, 0, (2, 10)), (12 + 0.9, 0, (3, 10))),
            default_radius=50,
        ),
        "RWG700": pf.PortSpec(
            description="LT single mode rib for O band",
            width=4,
            limits=(-1.5 + lt_thickness, 1.5),
            num_modes=1,
            target_neff=2.2,
            path_profiles=((0.7, 0, (2, 10)), (12 + 0.7, 0, (3, 10))),
            default_radius=60,
        ),
        "RWG2500": pf.PortSpec(
            description="LT low-loss multi-mode rib waveguide for C and O bands",
            width=8,
            limits=(-2 + lt_thickness, 2),
            num_modes=4,
            target_neff=2.2,
            path_profiles=((2.5, 0, (2, 10)), (12 + 2.5, 0, (3, 10))),
            default_radius=50,
        ),
        "SWG350": pf.PortSpec(
            description="350nm LT strip waveguide",
            width=18,
            limits=(-box_thickness, oxide_thickness + 0.5),
            num_modes=1,
            target_neff=2.2,
            path_profiles=((0.35, 0, (3, 10)), (20, 0, (3, 11))),
            default_radius=10,
        ),
        "SWG500": pf.PortSpec(
            description="500nm LT strip waveguide",
            width=12,
            limits=(-5, oxide_thickness + 0.5),
            num_modes=1,
            target_neff=2.2,
            path_profiles=((0.5, 0, (3, 10)), (20, 0, (3, 11))),
            default_radius=10,
        ),
        "UniCPW": pf.cpw_spec(
            (20, 0),
            15,
            5,
            50,
            added_solver_modes=0,
            target_neff=2.2,
            conductor_limits=(slab_thickness, z_m1_top),
            technology=technology,
        ),
        "UniCPW-EO-oband": pf.cpw_spec(
            (20, 0),
            20,
            5.5,
            50,
            added_solver_modes=0,
            target_neff=2.2,
            conductor_limits=(slab_thickness, z_m1_top),
            technology=technology,
        ),
        "UniCPW-EO-cband": pf.cpw_spec(
            (20, 0),
            16,
            5.5,
            50,
            added_solver_modes=0,
            target_neff=2.2,
            conductor_limits=(slab_thickness, z_m1_top),
            technology=technology,
        ),
    }

    return technology
