import pathlib
import subprocess
import xml.etree.ElementTree as et


def hex_to_rgba(color):
    "Convert a hex string to RGBA color components"

    if not isinstance(color, str) or len(color) == 0:
        raise TypeError("Argument must be a valid string.")

    if color[0] == "#":
        color = color[1:]

    n = len(color)
    if n == 3:  # "RGB"
        return tuple(int(c * 2, 16) for c in color) + (255,)
    if n == 4:  # "RGBA"
        return tuple(int(c * 2, 16) for c in color)
    if n == 6:  # "RRGGBB"
        return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4)) + (255,)
    if n == 8:  # "RRGGBBAA"
        return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4, 6))
    raise ValueError("Argument not recognized as a hex-valued RGBA color.")


descriptions = {
    (2, 0): "LN etch (ridge)",
    (2, 1): "LN etch (ridge, periodic features)",
    (3, 0): "LN etch (full)",
    (3, 1): "Slab etch negative",
    (4, 0): "Labels (LN etch)",
    (6, 0): "Usable floorplan area",
    (6, 1): "Final chip boundaries",
    (21, 0): "Metal transmission lines",
    (21, 1): "Metal heaters",
    (31, 0): "Alignment markers (LN etch)",
    (50, 1): "Error markers",
    (201, 0): "Labels for GDS layout (not fabricated)",
    (990, 0): "Wafer",
}

colors = {
    (21, 0): "#ebb73418",
    (21, 1): "#d75c1b18",
}

extra = [
    ((2, 1), "LN_RIDGE_P", "#45099e18"),
    ((31, 0), "ALIGN", "#d4467c18"),
    ((50, 1), "ERROR", "#c7031c18"),
    ((201, 0), "DOC", "#857b7518"),
    ((990, 0), "WAFER", "#47332818"),
]

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        raise RuntimeError(
            "Please run the script providing the path the layer properties file: python layer_converter <PATH_TO_LYP_FILE>"
        )

    tree = et.parse(sys.argv[1])
    root = tree.getroot()

    output = (
        pathlib.Path(__file__).parent / "luxtelligence_lnoi400_forge" / "_layers.py"
    ).resolve()
    with open(output, "w", encoding="utf-8") as file:
        layers = {}
        for prop in root.findall("properties"):
            text = prop.find("source").text
            if text == "*/*":
                continue
            j = text.find("/")
            k = j + text[j:].find("@")
            layer = (int(text[:j]), int(text[j + 1 : k]))
            color = colors.get(layer) or prop.find("fill-color").text + "18"
            description = descriptions[layer]

            name = prop.find("name").text.strip()
            layers[layer] = f"\t{name!r} : pf.LayerSpec({layer}, {description!r}, {color!r}),\n"

        for layer, name, color in extra:
            assert layer not in layers
            description = descriptions[layer]
            layers[layer] = f"\t{name!r} : pf.LayerSpec({layer}, {description!r}, {color!r}),\n"

        lines = [
            "import photonforge as pf\n\n",
            "_layers = {\n",
        ] + [v for _, v in sorted(layers.items())]
        lines.append("}\n")
        file.writelines(lines)
        subprocess.run(["ruff", "format", output], check=True)
