import photonforge as pf


def _core_and_clad_info(port_spec: pf.PortSpec, technology: pf.Technology):
    ridge = port_spec.path_profile_for((2, 10), technology)
    slab = port_spec.path_profile_for((3, 10), technology)
    empty = port_spec.path_profile_for((3, 11), technology)
    if empty is None:
        if ridge is None or slab is None:
            raise RuntimeError(
                "Port specification profile is unexpected for an optical waveguide in the LTOI300 "
                "platform."
            )
        core = ridge
        core_layer = (2, 10)
        clad = slab
        clad_layer = (3, 10)
    else:
        if ridge is None and slab is None:
            raise RuntimeError(
                "Port specification profile is unexpected for an optical waveguide in the LTOI300 "
                "platform."
            )
        elif ridge is None:
            core = slab
            core_layer = (3, 10)
        else:
            core = ridge
            core_layer = (2, 10)
        clad = empty
        clad_layer = (3, 11)

    core_width = (
        max(x[0] + 2 * abs(x[1]) for x in zip(*core))
        if isinstance(core[0], (list, tuple))
        else core[0] + 2 * abs(core[1])
    )

    clad_width = (
        max(x[0] + 2 * abs(x[1]) for x in zip(*clad))
        if isinstance(clad[0], (list, tuple))
        else clad[0] + 2 * abs(clad[1])
    )

    return (core_width, core_layer, clad_width, clad_layer)


def _cpw_info(port_spec):
    path_profiles = port_spec.path_profiles_list()

    ground_profile = None
    central_profile = None
    for profile in path_profiles:
        if profile[1] == 0:
            central_profile = profile
        elif profile[1] > 0:
            ground_profile = profile

    if (
        central_profile is None
        or ground_profile is None
        or central_profile[2] != ground_profile[2]
        or not port_spec.symmetric()
        or len(path_profiles) != 3
    ):
        raise RuntimeError(
            "Port specification does not correspond to an expected CPW transmission line."
        )

    central_width = central_profile[0]
    ground_width, ground_offset, layer = ground_profile
    gap = ground_offset - 0.5 * (ground_width + central_width)

    return central_width, gap, ground_width, ground_offset, layer
