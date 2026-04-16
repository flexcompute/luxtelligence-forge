import pathlib
import subprocess
import sys
import xml.etree.ElementTree as et


# Klayout patterns
patterns = {
    "0": "solid",  # solid
    "1": "hollow",  # hollow
    "2": ":",  # dotted
    "3": ".",  # coarsely dotted
    "4": "\\\\",  # left-hatched
    "5": "\\",  # lightly left-hatched
    "6": "\\\\",  # strongly left-hatched dense
    "7": "\\",  # strongly left-hatched sparse
    "8": "//",  # right-hatched
    "9": "/",  # lightly right-hatched
    "10": "//",  # strongly right-hatched dense
    "11": "/",  # strongly right-hatched sparse
    "12": "xx",  # cross-hatched
    "13": "x",  # lightly cross-hatched
    "14": "+",  # checkerboard 2px
    "15": "x",  # strongly cross-hatched sparse
    "16": "xx",  # heavy checkerboard
    "17": "x",  # hollow bubbles
    "18": "x",  # solid bubbles
    "19": "+",  # pyramids
    "20": "+",  # turned pyramids
    "21": "+",  # plus
    "22": "-",  # minus
    "23": "/",  # 22.5 degree down
    "24": "\\",  # 22.5 degree up
    "25": "//",  # 67.5 degree down
    "26": "\\\\",  # 67.5 degree up
    "27": "x",  # 22.5 cross hatched
    "28": "x",  # zig zag
    "29": "x",  # sine
    "30": "+",  # special pattern for light heavy dithering
    "31": "+",  # special pattern for light frame dithering
    "32": "||",  # vertical dense
    "33": "|",  # vertical
    "34": "||",  # vertical thick
    "35": "|",  # vertical sparse
    "36": "|",  # vertical sparse, thick
    "37": "=",  # horizontal dense
    "38": "-",  # horizontal
    "39": "=",  # horizontal thick
    "40": "-",  # horizontal
    "41": "-",  # horizontal
    "42": "++",  # grid dense
    "43": "+",  # grid
    "44": "++",  # grid thick
    "45": "+",  # grid sparse
    "46": "+",  # grid sparse, thick
}


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
    ((31, 0), "ALIGN", "#d4467c18", ":"),
    ((50, 1), "ERROR", "#c7031c18", "xx"),
    ((201, 0), "DOC", "#857b7518", "++"),
    ((990, 0), "WAFER", "#47332818", "hollow"),
]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise RuntimeError(
            "Please run the script providing the path the layer properties file: lnoi400.lyp"
        )

    tree = et.parse(sys.argv[1])
    root = tree.getroot()

    layers = {}
    for prop in root.findall("properties"):
        text = prop.find("source").text
        if text == "*/*":
            continue
        j = text.find("/")
        k = j + text[j:].find("@")
        layer = (int(text[:j]), int(text[j + 1 : k]))
        color = prop.find("fill-color").text + "18"
        key = prop.find("dither-pattern").text
        key = layer if key is None else key[1:]
        pattern = patterns.get(key, "")
        description = descriptions[layer]

        name = prop.find("name").text.strip()
        layers[layer] = (
            f"\t{name!r} : pf.LayerSpec({layer}, {description!r}, {color!r}, {pattern!r}),"
        )

    for layer, name, color, pattern in extra:
        assert layer not in layers
        description = descriptions[layer]
        layers[layer] = (
            f"\t{name!r} : pf.LayerSpec({layer}, {description!r}, {color!r}, {pattern!r}),"
        )

    lines = [
        "import photonforge as pf",
        "_layers = {",
    ] + [v for _, v in sorted(layers.items())]
    lines.append("}")

    output = pathlib.Path(__file__).parent / "luxtelligence_lnoi400_forge" / "_layers.py"
    output.write_text("\n".join(lines))
    subprocess.run(["ruff", "format", output], check=True)
