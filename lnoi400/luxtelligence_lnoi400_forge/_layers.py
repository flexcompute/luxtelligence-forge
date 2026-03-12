import photonforge as pf

_layers = {
	'LN_RIDGE' : pf.LayerSpec((2, 0), 'LN etch (ridge)', '#7d57de18'),
	'LN_RIDGE_P' : pf.LayerSpec((2, 1), 'LN etch (ridge, periodic features)', '#45099e18'),
	'LN_SLAB' : pf.LayerSpec((3, 0), 'LN etch (full)', '#00008018'),
	'SLAB_NEGATIVE' : pf.LayerSpec((3, 1), 'Slab etch negative', '#6750bf18'),
	'LABELS' : pf.LayerSpec((4, 0), 'Labels (LN etch)', '#5179b518'),
	'CHIP_CONTOUR' : pf.LayerSpec((6, 0), 'Usable floorplan area', '#ffc6b818'),
	'CHIP_EXCLUSION_ZONE' : pf.LayerSpec((6, 1), 'Final chip boundaries', '#00fe9c18'),
	'TL' : pf.LayerSpec((21, 0), 'Metal transmission lines', '#ebb73418'),
	'HT' : pf.LayerSpec((21, 1), 'Metal heaters', '#d75c1b18'),
	'ALIGN' : pf.LayerSpec((31, 0), 'Alignment markers (LN etch)', '#d4467c18'),
	'ERROR' : pf.LayerSpec((50, 1), 'Error markers', '#c7031c18'),
	'DOC' : pf.LayerSpec((201, 0), 'Labels for GDS layout (not fabricated)', '#857b7518'),
	'WAFER' : pf.LayerSpec((990, 0), 'Wafer', '#47332818'),
}
