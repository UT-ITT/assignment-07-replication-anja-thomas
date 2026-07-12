"""Small geometry helpers used by the cursors and the experiment modes."""

import math


def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def point_towards(origin, target, dist):
    """Point at `dist` from origin, along the direction to target."""
    dx = target[0] - origin[0]
    dy = target[1] - origin[1]
    d = math.hypot(dx, dy)
    if d < 1e-9:
        return origin
    return (origin[0] + dx / d * dist, origin[1] + dy / d * dist)


def angle_of(vec):
    return math.degrees(math.atan2(vec[1], vec[0]))


def angle_between(v1, v2):
    """Smallest absolute angle (degrees) between two direction vectors."""
    a1 = math.atan2(v1[1], v1[0])
    a2 = math.atan2(v2[1], v2[0])
    diff = math.degrees(a2 - a1)
    diff = (diff + 180.0) % 360.0 - 180.0
    return abs(diff)


def polar_offset(origin, angle_deg, dist):
    rad = math.radians(angle_deg)
    return (origin[0] + math.cos(rad) * dist, origin[1] + math.sin(rad) * dist)
