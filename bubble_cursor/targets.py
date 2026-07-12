import math

import config


class Target:
    """A circular selectable object (goal or distracter)."""

    __slots__ = ("x", "y", "radius", "is_goal", "kind", "shape_fill", "shape_ring")

    def __init__(self, x, y, radius, is_goal=False, kind="distractor"):
        self.x = x
        self.y = y
        self.radius = radius
        self.is_goal = is_goal
        # kind is just a label used by draw code: "goal", "goal_inactive", "distractor"
        self.kind = kind
        self.shape_fill = None
        self.shape_ring = None

    @property
    def pos(self):
        return (self.x, self.y)

    def contains_point(self, px, py):
        return math.hypot(px - self.x, py - self.y) <= self.radius

    def move_to(self, x, y):
        self.x, self.y = x, y
