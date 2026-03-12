import photonforge as pf
import luxtelligence_lnoi400_forge as lxt


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
        c.name[: c.name.rfind("_")]: c
        for c in (getattr(lxt.component, n)() for n in lxt.component_names)
    }
    components["UBEND"] = components.pop("UBEND_RACETRACK")

    for path in (request.path.parent / "gdsii").glob("*.gds"):
        gdsii = pf.find_top_level(*pf.load_layout(path).values())
        assert len(gdsii) == 1
        gdsii = gdsii[0]

        component = components[path.stem]

        diff = pf.Component(component.name + ".diff")
        total = 0
        error = 0
        layers = component.layers(include_dependencies=True)
        layers.update(gdsii.layers(include_dependencies=True))
        for layer in layers:
            gdsii_structs = gdsii.get_structures(layer)
            diff_structs = pf.offset(
                pf.boolean(component.get_structures(layer), gdsii_structs, "^"),
                -pf.config.tolerance,
            )
            if len(gdsii_structs) > 0:
                total += sum(x.area() for x in gdsii_structs)
            if len(diff_structs) > 0:
                diff.add(layer, *diff_structs)
                error += sum(x.area() for x in diff_structs)

        tol = {
            "DIR_COUPL": 0.059,
            "MZM": 4.0e-5,
            "MZM_HS": 4.2e-5,
            "SBEND": 0.011,
            "SBEND_VAR_WIDTH": 0.083,
            "UBEND": 6e-5,
        }.get(path.stem, 1e-5)
        if error > tol * total:
            component.write_gds()
            diff.write_gds()
            assert False, f"{component.name} error: {error / total:g}"
