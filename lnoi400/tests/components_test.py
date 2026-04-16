import photonforge as pf
import luxtelligence_lnoi400_forge as lxt

ps1 = pf.PortSpec(
    description="Custom",
    width=5,
    limits=(-1.5, 1.9),
    num_modes=1,
    target_neff=2.2,
    path_profiles=((0.2, 0, (2, 0)), (10, 0, (3, 0))),
)

ps2 = pf.PortSpec(
    description="Custom",
    width=5,
    limits=(-1.5, 1.9),
    num_modes=1,
    target_neff=2.2,
    path_profiles=((0.3, 0, (2, 0)), (10, 0, (3, 0))),
)

gdsii_to_func = {
    "CPW_pad_linear": "cpw_pad_linear",
    "L_turn_bend": "l_bend",
    "S_bend_vert": "s_bend_spline",
    "U_bend_racetrack": "racetrack_u_bend",
    "bend_S_spline": ("s_bend_spline", {"length": 100.0, "offset": 30.0, "straight_length": 0.0}),
    "bend_S_spline_varying_width": (
        "s_bend_spline_varying_width",
        {"port_spec1": ps1, "port_spec2": ps2},
    ),
    "chip_frame": "chip_frame",
    "directional_coupler_balanced": "directional_coupler_balanced",
    "double_linear_inverse_taper": "edge_coupler",
    "eo_phase_shifter": "eo_phase_shifter",
    "eo_phase_shifter_high_speed": "eo_phase_shifter_high_speed",
    "gc_focusing_1550": "gc_focusing_1550",
    "heater_straight_single": "straight_heater",
    "mmi1x2_optimized1550": "mmi1x2_optimized1550",
    "mmi2x2_optimized1550": "mmi2x2_optimized1550",
    "mzm_unbalanced": "mzm_unbalanced",
    "mzm_unbalanced_high_speed": "mzm_unbalanced_high_speed",
}


def test_components():
    technology = lxt.lnoi400()
    for name in dir(lxt.component):
        if name[0] == "_":
            continue
        func = getattr(lxt.component, name)
        _ = func(technology=technology)


def test_defaults(request):
    pf.config.default_technology = lxt.lnoi400()
    components = {
        c.parametric_function[c.parametric_function.rfind(".") + 1 :]: c
        for c in (getattr(lxt.component, n)() for n in lxt.component_names)
    }

    # assert len(components) == len(tuple((request.path.parent / "gdsii").glob("*.gds")))

    for path in sorted((request.path.parent / "gdsii").glob("*.gds")):
        gdsii = pf.find_top_level(*(c for n, c in pf.load_layout(path).items() if "$" not in n))
        assert len(gdsii) == 1
        gdsii = gdsii[0]

        component_name = gdsii_to_func[path.stem]
        if isinstance(component_name, tuple):
            component = getattr(lxt.component, component_name[0])(**component_name[1])
        else:
            component = components[component_name]

        diff = pf.Component(component.name + ".diff")
        total = 0
        error = 0
        layers = component.layers(include_dependencies=True)
        layers.update(gdsii.layers(include_dependencies=True))
        for layer in layers:
            gdsii_structs = gdsii.get_structures(layer)
            diff_structs = pf.boolean(component.get_structures(layer), gdsii_structs, "^")
            diff_structs = pf.offset(diff_structs, -0.5 * pf.config.tolerance)
            if len(gdsii_structs) > 0:
                total += sum(x.area() for x in gdsii_structs)
            if len(diff_structs) > 0:
                diff.add(layer, *diff_structs)
                error += sum(x.area() for x in diff_structs)

        tol = {
            "L_turn_bend": 1.3e-3,
            "S_bend_vert": 7e-4,
            "U_bend_racetrack": 9e-4,
            "bend_S_spline": 9e-4,
            "bend_S_spline_varying_width": 1.1e-3,
            "directional_coupler_balanced": 7e-4,
            "eo_phase_shifter": 7e-6,
            "eo_phase_shifter_high_speed": 6e-6,
            "gc_focusing_1550": 0.02,
            "heater_straight_single": 0,
            "mmi1x2_optimized1550": 0.15,  # claddings don't match
            "mmi2x2_optimized1550": 0.18,  # claddings don't match
            "mzm_unbalanced": 1.3e-4,
            "mzm_unbalanced_high_speed": 1.2e-4,
        }.get(path.stem, 0)
        if error > tol * total:
            component.write_gds()
            diff.write_gds()
            assert False, f"{path.stem} error: {error / total:g}"
