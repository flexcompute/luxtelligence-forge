import photonforge as pf
import luxtelligence_ltoi300_forge as lxt


def test_components():
    technology = lxt.ltoi300()
    for name in dir(lxt.component):
        if name[0] == "_":
            continue
        func = getattr(lxt.component, name)
        _ = func(technology=technology)


def test_defaults(request):
    pf.config.default_technology = lxt.ltoi300()
    components = {
        c.name[: c.name.rfind("_")]: c
        for c in (getattr(lxt.component, n)() for n in lxt.component_names)
    }

    assert len(components) == len(tuple((request.path.parent / "gdsii").glob("*.gds")))

    for name, component in components.items():
        path = request.path.parent / "gdsii" / f"{name}.gds"
        gdsii = pf.find_top_level(*(c for n, c in pf.load_layout(path).items() if "$" not in n))
        assert len(gdsii) == 1
        gdsii = gdsii[0]

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
            "terminated_mzm_1x2mmi_cband": 6e-5,
            "terminated_mzm_1x2mmi_oband": 5e-5,
            "terminated_mzm_2x2mmi_cband": 6e-5,
            "terminated_mzm_2x2mmi_oband": 5e-5,
            "unterminated_mzm_1x2mmi_cband": 9e-5,
            "unterminated_mzm_1x2mmi_oband": 7e-5,
            "unterminated_mzm_2x2mmi_cband": 9e-5,
            "unterminated_mzm_2x2mmi_oband": 7e-5,
        }.get(path.stem, 1e-5)
        if error > tol * total:
            component.write_gds()
            diff.write_gds()
            assert False, f"{component.name} error: {error / total:g}"
