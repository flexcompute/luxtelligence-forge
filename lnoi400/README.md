# Luxtelligence LNOI400

This python module implements the [Luxtelligence](https://luxtelligence.ai/)
LNOI400 PDK as components and technology specification for
[PhotonForge](https://docs.flexcompute.com/projects/photonforge/)

For LNOI400 design rules, design manual and PDK specifications, please [contact
Luxtelligence](https://luxtelligence.ai/service-request/).


## Installation

Installation via `pip`:

    pip install luxtelligence-lnoi400-forge


## Usage

The simplest way to use the this PDK in PhotonForge is to set its technology as
default:

    import photonforge as pf
    import luxtelligence_lnoi400_forge as lxt

    tech = lxt.lnoi400()
    pf.config.default_technology = tech


The `lnoi400` function creates a parametric technology and accepts a number of
parameters to fine-tune the technology.

PDK components are available in the `component` submodule. The list of
components can be discovered by:

    dir(lxt.component)
    
    pdk_component = lxt.component.mmi1x2()


Utility functions `cpw_spec` and `place_edge_couplers` are also available for
generating CPW port specifications and placing edge couplers at chip boudaries.

More information can be obtained in the documentation for each function:

    help(lxt.lnoi400)

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

### 1.4.0 - 2025-12-12

- Added `eo_phase_shifter_high_speed` and `mz_modulator_unbalanced_high_speed`.
- Added RF pads to `eo_phase_shifter` and corresponding terminals.
- Replace and deprecate the use of `*_kwargs` model parameters with model
  instances.
- Changed default values in accordance to 1.4.0 PDK release.
- Fixed missing terminal in straight heater.


### 1.2.4 - 2025-04-18

- Better error detection when inspecting port specifications


### 1.2.0 - 2025-03-04

- Added electrical ports and terminals.


### 1.1.0 - 2024-12-03

- Added arguments `slab_removal_width` and `input_ext` to
  `double_linear_inverse_taper`.
- Added arguments `center` and `exclusion_zone_width` to `chip_frame`.
- Added argument `start_section_width` to `s_bend_vert`.
- Added parametric components `dir_coupl`, `heater_pad`, `heater_straight`, and
  `heated_straight_waveguide`.
- `chip_frame` is centered around the origin by default.
- Changed `mz_modulator_unbalanced` default length.
- Removed port symmetries that were only valid for fundamental modes.


### 1.0.1 - 2024-10-17

- Add missing technology docstring.
- Fixed port symmetries in MMI2x2.
