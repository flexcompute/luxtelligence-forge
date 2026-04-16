from typing import Literal

import tidy3d as td
import photonforge as pf
import photonforge.typing as pft
from ._layers import _layers

_Medium = pft.Medium | dict[Literal["optical", "electrical"], pft.Medium]

# RMS error: 5.1e-08
ln_o_fit = td.PoleResidue(
    frequency_range=(td.C_0 / 2.0, td.C_0 / 0.5),
    eps_inf=1.834,
    poles=(
        ((-28758150.15401611 - 9272218283034106j), (-87088826899.25455 + 1.390184209108208e16j)),
        ((-2444588756.812169 - 9270364681667586j), (86846467771.13329 + 6374390707738.091j)),
        ((-4166996607130.011 - 6662941620389938j), (247761142.9987356 + 75457122287.2009j)),
        ((-53162033355695.1 - 1762364305777755.5j), (-31834.678431910543 + 795369.1205774402j)),
    ),
)

# RMS error: 1.5e-12
ln_e_fit = td.PoleResidue(
    frequency_range=(td.C_0 / 2.0, td.C_0 / 0.5),
    eps_inf=2.513,
    poles=(
        ((-175372.3922070572 - 8665247807373606j), (-31765987.412040588 + 8665246284870236j)),
        ((-84975854556.77737 - 8637602153098374j), (31902737.82444976 + 1517143903.4557555j)),
        ((-6981161765450.6875 - 5575102734114382j), (17062.58498426836 + 304558.89969198254j)),
        ((-9930099272379.094 - 2213216358451682.8j), (-12.376051830855069 + 2.238441656216347j)),
    ),
)


@pf.parametric_technology
def lnoi400(
    *,
    ln_thickness: pft.PositiveDimension = 0.4,
    slab_thickness: pft.PositiveDimension = 0.2,
    sidewall_angle: pft.Angle = 13.5,
    box_thickness: pft.PositiveDimension = 4.7,
    tl_thickness: pft.PositiveDimension = 0.9,
    tl_separation: pft.PositiveDimension = 1,
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
    ln: dict[str, pft.Medium] = {
        "optical": td.AnisotropicMedium(
            xx=ln_o_fit,
            yy=ln_e_fit,
            zz=ln_o_fit,
            viz_spec=td.VisualizationSpec(facecolor="#dd2f62"),
        ),
        "electrical": td.AnisotropicMedium(
            xx=td.Medium(permittivity=38),
            yy=td.Medium(permittivity=28),
            zz=td.Medium(permittivity=38),
            viz_spec=td.VisualizationSpec(facecolor="#dd2f62"),
        ),
    },
    metal: dict[str, pft.Medium] = {
        "optical": td.material_library["Au"]["Olmon2012evaporated"].updated_copy(
            viz_spec=td.VisualizationSpec(facecolor="#f8b50c")
        ),
        "electrical": td.LossyMetalMedium(
            conductivity=41,
            frequency_range=[0.1e9, 100e9],
            fit_param=td.SurfaceImpedanceFitterParam(max_num_poles=16),
            viz_spec=td.VisualizationSpec(facecolor="#f8b50c"),
        ),
    },
    opening: pft.Medium = td.Medium(permittivity=1.0, name="Opening"),
) -> pf.Technology:
    """Create a technology for the LNOI400 PDK.

    Args:
        ln_thickness: LiNbO₃ layer thickness.
        slab_thickness: Partially etched slab thickness in LiNbO₃.
        sidewall_angle: Sidewall angle (in degrees) for LiNbO₃ etching.
        box_thickness: Thickness of the bottom oxide clad.
        tl_thickness: TL layer thickness.
        tl_separation: Separation between the LiNbO₃ and TL layers.
        sio2: Oxide and background medium.
        si: Silicon medium.
        ln: LiNbO₃ medium.
        metal: TL and heater metal medium.
        opening: Medium for openings.

    Returns:
        Technology: LNOI400 technology definition.
    """
    # Layers
    layers = {k: v.copy() for k, v in _layers.items()}

    # Extrusion specifications
    bounds = pf.MaskSpec()  # Empty mask for all chip bounds
    full_ln_mask = pf.MaskSpec([(2, 0), (2, 1), (4, 0), (31, 0)], [], "+")
    slab_etch_mask = pf.MaskSpec((3, 1), (3, 0), "-")
    tl_mask = pf.MaskSpec((21, 0))
    ht_mask = pf.MaskSpec((21, 1))

    z_tl = ln_thickness + tl_separation
    z_top = z_tl + tl_thickness

    extrusion_specs = [
        pf.ExtrusionSpec(bounds, si, (-pf.Z_INF, 0)),
        pf.ExtrusionSpec(bounds, sio2, (-box_thickness, z_top)),
        pf.ExtrusionSpec(bounds, ln, (0, slab_thickness), 0),
        pf.ExtrusionSpec(full_ln_mask, ln, (0, ln_thickness), sidewall_angle),
        pf.ExtrusionSpec(slab_etch_mask, sio2, (0, ln_thickness), -sidewall_angle),
        pf.ExtrusionSpec(tl_mask, metal, (z_tl, z_top)),
        pf.ExtrusionSpec(ht_mask, metal, (z_tl, z_top)),
    ]

    rwg_port_gap = min(1.5, box_thickness)
    rwg_port_limits = (-rwg_port_gap, ln_thickness + rwg_port_gap)
    swg_port_gap = min(2.1, box_thickness)
    swg_port_limits = (-swg_port_gap, slab_thickness + swg_port_gap)

    # default T-rail full height
    t_height = 3

    technology = pf.Technology("LNOI400", "1.4.0", layers, extrusion_specs, {}, opening)
    technology.ports = {
        "RWG1000": pf.PortSpec(
            description="LN single mode ridge waveguide for C-band, TE mode",
            width=5,
            limits=rwg_port_limits,
            num_modes=1,
            target_neff=2.2,
            path_profiles=((1, 0, (2, 0)), (10, 0, (3, 0))),
        ),
        "RWG3000": pf.PortSpec(
            description="LN multimode mode ridge for C-band",
            width=8,
            limits=rwg_port_limits,
            num_modes=5,
            target_neff=2.2,
            path_profiles=((3, 0, (2, 0)), (12, 0, (3, 0))),
        ),
        "SWG250": pf.PortSpec(
            description="LN strip waveguide for C-band, TE mode",
            width=10,
            limits=swg_port_limits,
            num_modes=1,
            target_neff=2.2,
            path_profiles=((0.25, 0, (3, 0)), (12, 0, (3, 1))),
        ),
        "UniCPW": pf.cpw_spec(
            (21, 0), 15, 5, 250, added_solver_modes=0, target_neff=2.2, technology=technology
        ),
        "UniCPW-EO": pf.cpw_spec(
            (21, 0), 10, 4, 180, added_solver_modes=0, target_neff=2.2, technology=technology
        ),
        "UniCPW-HS": pf.cpw_spec(
            (21, 0),
            21,
            4 + 2 * t_height,
            180,
            added_solver_modes=0,
            target_neff=2.2,
            technology=technology,
        ),
    }

    return technology
