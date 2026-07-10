import shutil

import photonforge as pf
from photonforge import pda

import luxtelligence_lnoi400_forge as lxt


def ignore_cache(path, names):
    return ["__pycache__"] if "__pycache__" in names else []


def create_library():
    name = "Luxtelligence LNOI400"
    version = lxt.lnoi400().version
    description ="Luxtelligence LNOI400 PDK"

    for lib in pda.list_libraries(name):
        if lib["version"] == version:
            print("Library already exists: " + str(lib))
            return

    print(f"Creating library {name!r} - version {version!r}", flush=True)
    project = pda.create_project(
        name=name,
        description=description,
        visibility="public",
        role="viewer",
        create_template=False,
    )

    # Add sources
    shutil.copytree(
        "./luxtelligence_lnoi400_forge",
        project.module_path / project.module_name,
        dirs_exist_ok=True,
        ignore=ignore_cache,
    )

    project.save_module()
    module = project.import_module(None)[project.module_name]

    tech = module.lnoi400()
    pf.config.default_technology = tech

    # NOTE: Make sure to pass technology so that we have it set on updates
    components = [getattr(module.component, n)(name=n, technology=tech) for n in lxt.component_names]

    # Add components
    update_config = True
    for component in components:
        print("Adding", repr(component.name), flush=True)
        project.add(component, update_existing_dependencies=False, update_config=update_config)
        update_config = False

    project.add_version(version)

    print(f"Done: {project!r}")


if __name__ == "__main__":
    pda.init()

    try:
        create_library()
    finally:
        pda.stop()
