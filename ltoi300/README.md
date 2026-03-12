# Luxtelligence LTOI300

This python module implements the [Luxtelligence](https://luxtelligence.ai/)
LTOI300 PDK as components and technology specification for
[PhotonForge](https://docs.flexcompute.com/projects/photonforge/)

For LTOI300 design rules, design manual and PDK specifications, please [contact
Luxtelligence](https://luxtelligence.ai/service-request/).


## Installation

Installation via `pip`:

    pip install luxtelligence-ltoi300-forge


## Usage

The simplest way to use the this PDK in PhotonForge is to set its technology as
default:

    import photonforge as pf
    import luxtelligence_ltoi300_forge as lxt

    tech = lxt.ltoi300()
    pf.config.default_technology = tech


The `ltoi300` function creates a parametric technology and accepts a number of
parameters to fine-tune the technology.

PDK components are available in the `component` submodule. The list of
components can be discovered by:

    dir(lxt.component)
    
    pdk_component = lxt.component.mmi1x2()


Utility functions `cpw_spec` and `place_edge_couplers` are also available for
generating CPW port specifications and placing edge couplers at chip boudaries.

More information can be obtained in the documentation for each function:

    help(lxt.ltoi300)

    help(lxt.component.mmi1x2)

    help(lxt.place_edge_couplers)


Finally, an extrusion demo for the technology can be seen by running:

    lxt.plot_cross_section()


## Warnings

Please note that the 3D structures obtained by extrusion through this module's
technologies are a best approximation of the intended fabricated structures,
but the actual final dimensions may differ due to several fabrication-specific
effects. In particular, doping profiles are represented with hard-boundary,
homogeneous solids, but, in practice will present process-dependent variations
with smooth boundaries.


## Changelog

### 1.0.0 - Unreleased

- Initial release
