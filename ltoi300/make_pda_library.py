import shutil
from argparse import ArgumentParser

from tidy3d.config import get_manager

import photonforge as pf
from photonforge import pda

import luxtelligence_ltoi300_forge as lxt

get_manager().switch_profile("dev")


def fix_function(obj, project):
    if obj.parametric_function is not None:
        obj.parametric_function = (
            project.module_name + "." + obj.parametric_function.partition(".")[2]
        )


def create_library():
    tech = lxt.ltoi300()
    pf.config.default_technology = tech

    name = "Luxtelligence LTOI300"
    version = tech.version

    for lib in pda.list_libraries(name):
        if lib["version"] == version:
            print("Library already exists: " + str(lib))
            return

    components = [getattr(lxt.component, n)(name=n) for n in lxt.component_names]

    project = pda.create_project(
        name=name,
        description="Luxtelligence LTOI300 PDK",
        visibility="public",
        role="viewer",
        create_template=False,
    )

    # Add sources
    shutil.copytree(
        "./luxtelligence_ltoi300_forge",
        project.module_path / project.module_name,
        dirs_exist_ok=True,
    )

    project.save_module()

    fix_function(tech, project)

    # Add components
    for component in components:
        print("Adding", repr(component.name), flush=True)
        fix_function(component, project)
        for dep in component.dependencies():
            fix_function(dep, project)
        project.add(component, update_existing_dependencies=False, update_config=False)

    project.add_version(version)

    print("Done:", project)


if __name__ == "__main__":
    parser = ArgumentParser(prog=__file__)
    parser.add_argument("--profile", default=None, help="tidy3d configuration profile")
    args = parser.parse_args()

    profile = args.profile
    if args.profile is not None:
        get_manager().switch_profile(args.profile)

    pda.init()

    try:
        create_library()
    finally:
        pda.stop()
