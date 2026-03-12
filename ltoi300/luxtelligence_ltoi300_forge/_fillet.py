import numpy as np
import photonforge as pf


# TODO: Simplified implementation while pf.Polygon.fillet is not released (planned for v1.4)
def fillet(polygon, radius):
    if radius <= 0:
        return polygon

    vertices = polygon.vertices
    pts = np.array(vertices, dtype=float)
    pts = _remove_collinear(pts)
    size = len(pts)
    if size < 3:
        return polygon

    result: list[tuple[float, float]] = []

    for j in range(size):
        i = size - 1 if j == 0 else j - 1
        k = 0 if j == size - 1 else j + 1

        p0x, p0y = pts[i]
        p1x, p1y = pts[j]
        p2x, p2y = pts[k]

        v0x = p1x - p0x
        v0y = p1y - p0y
        len0 = np.sqrt(v0x * v0x + v0y * v0y)
        if len0 < 2 * pf.config.tolerance:
            result.append((p1x, p1y))
            continue
        v0x /= len0
        v0y /= len0

        v1x = p2x - p1x
        v1y = p2y - p1y
        len1 = np.sqrt(v1x * v1x + v1y * v1y)
        if len1 < 2 * pf.config.tolerance:
            result.append((p1x, p1y))
            continue
        v1x /= len1
        v1y /= len1

        dot = v0x * v1x + v0y * v1y
        if 1.0 - abs(dot) < 1.0e-10:
            result.append((p1x, p1y))
            continue

        theta = np.acos(dot)
        tant = np.tan(0.5 * theta)
        r = radius
        tan_len = r * tant

        if tan_len > 0.5 * len0:
            tan_len = 0.5 * len0
            r = tan_len / tant
        if tan_len > 0.5 * len1:
            tan_len = 0.5 * len1
            r = tan_len / tant
        if r < pf.config.tolerance:
            result.append((p1x, p1y))
            continue

        # Arc center direction: bisector of (-v0, v1) normalized
        dvx = v1x - v0x
        dvy = v1y - v0y
        dv_len = np.sqrt(dvx * dvx + dvy * dvy)
        cost = np.cos(0.5 * theta)
        fac = 1.0 / (cost * dv_len)
        dvx *= fac
        dvy *= fac

        # Arc start/end angles relative to the center
        a0x = -v0x * tant - dvx
        a0y = -v0y * tant - dvy
        a1x = v1x * tant - dvx
        a1y = v1y * tant - dvy
        angle0 = np.atan2(a0y, a0x)
        angle1 = np.atan2(a1y, a1x)

        if angle1 - angle0 > np.pi:
            angle1 -= 2.0 * np.pi
        elif angle1 - angle0 < -np.pi:
            angle1 += 2.0 * np.pi

        n = _arc_num_points(angle1 - angle0, r)
        if n < 2:
            n = 2

        cx = p1x + dvx * r
        cy = p1y + dvy * r
        for ii in range(n):
            a = angle0 + ii * (angle1 - angle0) / (n - 1)
            result.append((cx + r * np.cos(a), cy + r * np.sin(a)))

    out = np.array(result, dtype=float)
    return pf.Polygon(_remove_duplicates(out))


def _arc_num_points(angle: float, radius: float) -> int:
    c = 1 - abs(pf.config.tolerance / radius)
    a = np.pi if c < -1 else np.acos(c)
    return int(0.5 + 0.5 * abs(angle) / a)


def _remove_collinear(pts: np.ndarray) -> np.ndarray:
    n = len(pts)
    if n < 3:
        return pts
    keep = []
    for j in range(n):
        i = n - 1 if j == 0 else j - 1
        k = 0 if j == n - 1 else j + 1
        d0 = pts[j] - pts[i]
        d1 = pts[k] - pts[j]
        if abs(d0[0] * d1[1] - d0[1] * d1[0]) > 1e-12:
            keep.append(j)
    return pts[keep] if keep else pts


def _remove_duplicates(pts: np.ndarray) -> np.ndarray:
    if len(pts) < 2:
        return pts
    keep = [0]
    for i in range(1, len(pts)):
        if not np.allclose(pts[i], pts[keep[-1]]):
            keep.append(i)
    if len(keep) > 1 and np.allclose(pts[keep[-1]], pts[keep[0]]):
        keep.pop()
    return pts[keep]
