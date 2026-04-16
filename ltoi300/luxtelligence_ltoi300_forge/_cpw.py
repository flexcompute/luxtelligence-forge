from collections.abc import Sequence as Sequence
from typing import NamedTuple, Literal

import photonforge as pf
import photonforge.typing as pft

from .utils import _cpw_info


class TRailSpec(NamedTuple):
    base_width: pft.Dimension = 0
    base_height: pft.Dimension = 0
    top_width: pft.Dimension = 0
    top_height: pft.Dimension = 0
    gap: pft.Dimension = 0
    fillet_radius: pft.Dimension = 0

    def is_valid(self):
        return (self.base_width > 0 and self.base_height > 0) or (
            self.top_width > 0 and self.top_height > 0
        )

    @property
    def width(self):
        return max(self.base_width, self.top_width)

    @property
    def period(self):
        return self.width + self.gap

    def polygon(self) -> pf.Polygon:
        base = pf.Rectangle(
            center=(0, self.base_height / 2), size=(self.base_width, self.base_height)
        )
        top = pf.Rectangle(
            center=(0, self.base_height + self.top_height / 2),
            size=(self.top_width, self.top_height),
        )

        if self.fillet_radius <= 0:
            return pf.boolean(base, top, "+")[0]

        fillet_fill = pf.Rectangle(
            center=(0, -pf.config.grid),
            size=(self.base_width + 4 * self.fillet_radius, 2 * pf.config.grid),
        )
        return pf.boolean([fillet_fill, base, top], [], "+")[0].fillet(self.fillet_radius)

    def negative_polygon(self) -> pf.Polygon:
        base_width = self.period - self.base_width
        top_width = self.period - self.top_width
        base = pf.Rectangle(
            center=(0, -self.top_height - self.base_height / 2), size=(base_width, self.base_height)
        )
        top = pf.Rectangle(center=(0, -self.top_height / 2), size=(top_width, self.top_height))

        if self.fillet_radius <= 0:
            return pf.boolean(base, top, "+")[0]

        fillet_fill = pf.Rectangle(
            center=(0, pf.config.grid),
            size=(top_width + 4 * self.fillet_radius, 2 * pf.config.grid),
        )
        return pf.boolean([fillet_fill, base, top], [], "+")[0].fillet(self.fillet_radius)


@pf.parametric_component
def straight_cpw(
    *,
    cpw_spec: pf.PortSpec,
    opt_spec: pf.PortSpec | None,
    length: pft.PositiveDimension,
    bulge_width: pft.Dimension,
    bulge_taper_length: pft.Dimension,
    t_rail: TRailSpec,
    waveguide_position: Literal["top", "bottom", "both"],
    technology: pf.Technology | None,
    name: str = "",
) -> pf.Component:
    c = pf.parametric.straight(
        port_spec=cpw_spec, length=length, technology=technology, use_parametric_cache=False
    )
    c.parametric_function = None
    c.parametric_kwargs = None
    c.random_variables = None
    c.name = name

    central_width, gap, _, _, layer = _cpw_info(cpw_spec)

    if t_rail.is_valid():
        t0 = t_rail.negative_polygon()
        t1 = t0.copy().mirror()

        period = t_rail.period
        count = int(length / period) - 1
        offset = 0.5 * (length - (count - 1) * period)

        negative = []
        y = -0.5 * central_width - gap
        negative.extend(t0.copy().translate((offset + period * i, y)) for i in range(count))
        y = -0.5 * central_width
        negative.extend(t1.copy().translate((offset + period * i, y)) for i in range(count))
        y = 0.5 * central_width
        negative.extend(t0.copy().translate((offset + period * i, y)) for i in range(count))
        y = 0.5 * central_width + gap
        negative.extend(t1.copy().translate((offset + period * i, y)) for i in range(count))

        new_polygons = pf.boolean(c.structures[layer], negative, "-")
        c.filter_layers([layer], keep=False)
        c.add(layer, *new_polygons)

    if opt_spec is not None:
        wg = pf.parametric.straight(
            port_spec=opt_spec,
            length=length,
            bulge_width=bulge_width,
            bulge_taper_length=bulge_taper_length,
            technology=technology,
        )
        offset = 0.5 * (central_width + gap)
        if waveguide_position != "bottom":
            wg_top = pf.Reference(wg, origin=(0, offset))
            c.add(wg_top)
            c.add_port([wg_top["P0"], wg_top["P1"]])
        if waveguide_position != "top":
            wg_bot = pf.Reference(wg, origin=(0, -offset))
            c.add(wg_bot)
            c.add_port([wg_bot["P1"], wg_bot["P0"]])

    return c


@pf.parametric_component
def via(
    *,
    layer: tuple[int, int],
    size: pft.PositiveDimension2D,
    fillet_radius: pft.Dimension,
    technology: pf.Technology | None,
    name: str = "",
) -> pf.Component:
    via = pf.Rectangle(size=size)
    if fillet_radius > 0:
        via = via.to_polygon().fillet(fillet_radius)
    return pf.Component(name, technology).add(layer, via)


def via_fill(
    layer: tuple[int, int],
    area: pf.Rectangle,
    via_size: pft.PositiveDimension | None,
    gap: pft.Dimension,
    margin: pft.Dimension,
    fillet_radius: pft.Dimension,
    technology: pf.Technology | None,
) -> list[pf.Reference]:
    size = area.size - 2 * margin

    if via_size is None:
        cols = 1
        rows = 1
    else:
        period = via_size + gap
        cols = int(size[0] / period)
        if via_size + period * cols <= size[0]:
            cols += 1
        rows = int(size[1] / period)
        if via_size + period * rows <= size[1]:
            rows += 1

    if cols * rows > 1:
        v = via(
            layer=layer,
            size=(via_size, via_size),
            fillet_radius=fillet_radius,
            technology=technology,
        )
        # TODO: Until PDA suports reference arrays, we need to dismember these
        vias = pf.Reference(v, columns=cols, rows=rows, spacing=(period, period))
        vias.x_mid, vias.y_mid = area.center
        vias = vias.get_repetition()
    else:
        v = via(
            layer=layer,
            size=size,
            fillet_radius=fillet_radius,
            technology=technology,
        )
        vias = [pf.Reference(v, area.center)]

    return vias


@pf.parametric_component
def cpw_termination(
    *,
    cpw_spec: pf.PortSpec,
    resistor_length: pft.PositiveDimension,
    resistor_width: pft.PositiveDimension,
    m1_length: pft.PositiveDimension,
    m2_separation: pft.Dimension,
    m2_hrl_length: pft.PositiveDimension,
    hrl_separation: pft.Dimension,
    via_size: pft.PositiveDimension,
    via_gap: pft.PositiveDimension,
    via_margin: pft.Dimension,
    fillet_radius: pft.Dimension,
    technology: pf.Technology | None,
    name: str = "",
) -> pf.Component:
    c = pf.Component(name, technology)
    c.properties.__thumbnail__ = "electrical_termination"

    central_width, gap, ground_width, _, _ = _cpw_info(cpw_spec)
    y0 = pf.snap_to_grid(0.5 * central_width)
    y1 = pf.snap_to_grid(0.5 * central_width + gap)
    y2 = pf.snap_to_grid(0.5 * central_width + gap + ground_width)

    x0 = pf.snap_to_grid(m1_length)
    x1 = pf.snap_to_grid(m1_length + m2_separation)
    x2 = pf.snap_to_grid(m1_length + m2_separation + m2_hrl_length)
    x3 = pf.snap_to_grid(m1_length + m2_separation + m2_hrl_length + hrl_separation)

    dy = central_width + gap
    dx = (2 * resistor_length - dy) / 3
    if dx < 10:
        dx = 10
        dy = 2 * resistor_length - 3 * dx
    if dy - 0.5 * resistor_width < y1:
        raise ValueError("Resistor length is too small for the CPW spec.")

    resistor = [
        pf.Path((x3, 0), resistor_width).segment([(x3 + dx, 0), (x3 + dx, dy), (x3, dy)]),
        pf.Path((x3 + dx, 0), resistor_width).segment([(x3 + dx, -dy), (x3, -dy)]),
    ]

    hrl_rects = (
        pf.Rectangle((x1 - fillet_radius, -y0), (x3, y0)),
        pf.Rectangle((x1 - fillet_radius, -y2), (x3, -y1)),
        pf.Rectangle((x1 - fillet_radius, y1), (x3, y2)),
    )

    merged = pf.boolean(hrl_rects, resistor, "+")[0]
    if fillet_radius > 0:
        tol = pf.config.tolerance
        cut = pf.Rectangle((x1 - fillet_radius - tol, -y2 - tol), (x1, y2 + tol))
        merged = pf.boolean(merged.fillet(fillet_radius), cut, "-")[0]

    m1_rects = (
        pf.Rectangle((0, -y0), (x0, y0)),
        pf.Rectangle((0, -y2), (x0, -y1)),
        pf.Rectangle((0, y1), (x0, y2)),
    )

    m1_m2_layer = c.technology.layers["VIA_M1_M2"].layer
    m2_hrl_layer = c.technology.layers["VIA_M2_HRL"].layer

    c.add(
        "M1",
        *m1_rects,
        "M2",
        pf.Rectangle((0, -y0), (x2, y0)),
        pf.Rectangle((0, -y2), (x2, -y1)),
        pf.Rectangle((0, y1), (x2, y2)),
        "HRL",
        merged,
        *(
            via
            for rect in m1_rects
            for via in via_fill(
                m1_m2_layer, rect, via_size, via_gap, via_margin, fillet_radius, technology
            )
        ),
        *(
            via
            for rect in (
                pf.Rectangle((x1, -y0), (x2, y0)),
                pf.Rectangle((x1, -y2), (x2, -y1)),
                pf.Rectangle((x1, y1), (x2, y2)),
            )
            for via in via_fill(
                m2_hrl_layer, rect, None, via_gap, via_margin, fillet_radius, technology
            )
        ),
    )

    c.add_port(pf.Port((0, 0), 0, cpw_spec))
    return c


@pf.parametric_component
def cpw_pad(
    *,
    cpw_spec: pf.PortSpec,
    opt_spec: pf.PortSpec | None,
    straight_length: pft.PositiveDimension,
    taper_length: pft.PositiveDimension,
    ground_pad_width: pft.PositiveDimension,
    pitch: pft.PositiveDimension,
    overlap_length: pft.PositiveDimension,
    m2_length: pft.Dimension,
    via_size: pft.PositiveDimension,
    via_gap: pft.PositiveDimension,
    via_margin: pft.PositiveDimension,
    via_fillet_radius: pft.Dimension,
    waveguide_position: Literal["top", "bottom", "both"],
    technology: pf.Technology | None,
    name: str = "",
) -> pf.Component:
    central_width, gap, ground_width, _, _ = _cpw_info(cpw_spec)

    aspect_ratio = central_width / (central_width + 2 * gap)
    central_pad_width = pitch * 2 * aspect_ratio / (1 + aspect_ratio)
    pad_gap = pitch * (1 - aspect_ratio) / (1 + aspect_ratio)

    # Make sure dimensions will produce symmetrical polygons when grid-aligned
    central_pad_width = pf.snap_to_grid(central_pad_width / 4) * 4
    pad_gap = pf.snap_to_grid(pad_gap / 4) * 4

    x0 = pf.snap_to_grid(taper_length)
    x1 = pf.snap_to_grid(taper_length + straight_length)
    x2 = pf.snap_to_grid(taper_length + straight_length + overlap_length)
    x3 = pf.snap_to_grid(taper_length + straight_length + overlap_length + m2_length)

    y0 = pf.snap_to_grid(0.5 * (central_width + gap))
    y1 = pf.snap_to_grid(0.5 * (central_pad_width + pad_gap))
    y2 = pf.snap_to_grid(0.5 * central_width + gap + ground_width)
    y3 = pf.snap_to_grid(0.5 * central_pad_width + pad_gap + ground_pad_width)
    y4 = pf.snap_to_grid(0.5 * central_pad_width)
    y5 = pf.snap_to_grid(0.5 * central_pad_width + pad_gap)

    s_shape = pf.Expression(
        "u",
        [
            ("v", "u^2 * (3 - 2 * u)"),
            ("dv", "6 * u * (1 - u)"),
            ("x", f"{x0} * u"),
            ("y", f"{y1} * v + {y0} * (1 - v)"),
            ("dx", f"{x0}"),
            ("dy", f"{y1 - y0} * dv"),
        ],
    )

    c = pf.Component(name, technology)
    c.properties.__thumbnail__ = "bondpad"

    if opt_spec is not None:
        wg = pf.Component("CPW_PAD_S_BEND", technology)
        for layer, path in opt_spec.get_paths((0, y0)):
            path.parametric(s_shape, relative=False).segment((x1, y1))
            wg.add(layer, path)
        wg.add_port([pf.Port((0, y0), 0, opt_spec), pf.Port((x1, y1), 180, opt_spec.inverted())])
        if waveguide_position != "top":
            c.add(pf.Reference(wg, x_reflection=True))
        if waveguide_position != "bottom":
            c.add(pf.Reference(wg))
        c.add_reference_ports()

    envelope = pf.Polygon([(0, -y2), (x0, -y3), (x2, -y3), (x2, y3), (x0, y3), (0, y2)])

    gap_factor = 2 * (1 - aspect_ratio) / (1 + aspect_ratio)
    top_gap = (
        pf.Path((-pf.config.grid, y0), gap)
        .segment((0, y0))
        .parametric(
            s_shape,
            width=pf.Expression(
                "u",
                [
                    ("v", "u^2 * (3 - 2 * u)"),
                    ("dv", "6 * u * (1 - u)"),
                    ("y", f"{y1} * v + {y0} * (1 - v)"),
                    ("dy", f"{y1 - y0} * dv"),
                    ("w", f"{gap_factor} * y"),
                    ("dw", f"{gap_factor} * dy"),
                ],
            ),
            relative=False,
        )
        .segment((x2 + pf.config.grid, y1))
    ).to_polygon()
    bot_gap = top_gap.copy().mirror()

    c.add(
        "M1",
        *pf.boolean(envelope, [top_gap, bot_gap], "-"),
        "M2",
        pf.Rectangle((x1, -y4), (x3, y4)),
        pf.Rectangle((x1, -y3), (x3, -y5)),
        pf.Rectangle((x1, y5), (x3, y3)),
    )

    c.add_port(pf.Port((0, 0), 0, cpw_spec))
    m2 = c.technology.layers["M2"].layer
    c.add_terminal(pf.Terminal(m2, pf.Rectangle((x2, -y4), (x3, y4))), "signal")
    c.add_terminal(pf.Terminal(m2, pf.Rectangle((x2, -y3), (x3, -y5))), "gnd_b")
    c.add_terminal(pf.Terminal(m2, pf.Rectangle((x2, y5), (x3, y3))), "gnd_t")

    layer = c.technology.layers["VIA_M1_M2"].layer
    c.add(
        *(
            via
            for rect in (
                pf.Rectangle((x1, -y4), (x2, y4)),
                pf.Rectangle((x1, -y3), (x2, -y5)),
                pf.Rectangle((x1, y5), (x2, y3)),
            )
            for via in via_fill(
                layer, rect, via_size, via_gap, via_margin, via_fillet_radius, technology
            )
        )
    )

    return c
