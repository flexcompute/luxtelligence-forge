import shutil

from tidy3d.config import get_manager

import photonforge as pf
from photonforge import pda

import luxtelligence_lnoi400_forge as lxt

get_manager().switch_profile("dev")


def fix_function(obj, project):
    if obj.parametric_function is not None:
        obj.parametric_function = (
            project.module_name + "." + obj.parametric_function.partition(".")[2]
        )


def create_library():
    tech = lxt.lnoi400()
    pf.config.default_technology = tech

    name = "Luxtelligence LNOI400"
    version = tech.version

    for lib in pda.list_libraries(name):
        if lib["version"] == version:
            print("Library already exists: " + str(lib))
            return

    components = [getattr(lxt.component, n)() for n in lxt.component_names]

    project = pda.create_project(
        name=name,
        description="Luxtelligence LNOI400 PDK",
        visibility="public",
        role="viewer",
        create_template=False,
    )

    # Add sources
    shutil.copytree(
        "./luxtelligence_lnoi400_forge",
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
    pda.init("http://localhost:3030", "ws://localhost:3030")
    try:
        create_library()
    finally:
        pda.stop()
