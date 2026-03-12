import photonforge as pf

_layers = {
    "LT_RIDGE": pf.LayerSpec((2, 10), "LT etch (ridge)", "#ca84f518", "/"),
    "LT_RIDGE_PERIODIC": pf.LayerSpec(
        (2, 11), "LT etch (ridge, periodic features)", "#ff00ff18", "//"
    ),
    "LT_SLAB": pf.LayerSpec((3, 10), "LT etch (full)", "#875dd418", "\\"),
    "SLAB_NEGATIVE": pf.LayerSpec((3, 11), "Slab etch negative", "#4c209e18", "."),
    "LABELS": pf.LayerSpec((4, 0), "Labels (LT etch)", "#5179b518", ""),
    "CHIP_CONTOUR": pf.LayerSpec((6, 0), "Usable floorplan area", "#ffc6b818", "hollow"),
    "CHIP_EXCLUSION_ZONE": pf.LayerSpec((6, 1), "Final chip boundaries", "#00fe9c18", "hollow"),
    "M1": pf.LayerSpec((20, 0), "Metal 1", "#3503fc18", "|"),
    "M2": pf.LayerSpec((22, 0), "Metal 2", "#3503fc18", "."),
    "HRL": pf.LayerSpec((23, 0), "High resistivity metal", "#e0666618", ""),
    "VIA_M1_M2": pf.LayerSpec((40, 0), "Via between M1 and M2", "#aaaaaa18", "//"),
    "VIA_M2_HRL": pf.LayerSpec((41, 0), "Via between M2 and HRL", "#59555518", "\\\\"),
    "ERROR": pf.LayerSpec((50, 1), "Error markers", "#c7031c18", "xx"),
    "DOC": pf.LayerSpec((201, 0), "Labels for GDS layout (not fabricated)", "#857b7518", "++"),
    "WAFER": pf.LayerSpec((990, 0), "Wafer", "#47332818", "hollow"),
}
