"""
The three target-acquisition cursors compared in the paper.

Each cursor exposes:
    .x, .y                current rendered cursor position
    .captured_target       the Target that would be selected if you clicked now (or None)
    .update(mx, my, dt, targets)   called every frame with the raw mouse position

PointCursor and BubbleCursor are direct, faithful implementations of the
algorithms described in the paper. ObjectPointingCursor is a reasonable
approximation of Guiard et al.'s technique as summarized in the "Object
Pointing" section of the paper -- the original relies on some internal
parameters (jump thresholds, angular search sequence) that are described
only at a high level, so this is functionally similar rather than a
byte-exact reproduction.
"""

import math

import config
import geometry


class PointCursor:
    """Standard single-pixel-hotspot cursor. Selects whatever target its
    single point happens to land inside of."""

    name = "Point"
    display_name = "Point Cursor"

    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.captured_target = None

    def reset(self, targets, start_pos=None):
        if start_pos:
            self.x, self.y = start_pos

    def update(self, mx, my, dt, targets):
        self.x, self.y = mx, my
        self.captured_target = None
        for t in targets:
            if t.contains_point(mx, my):
                self.captured_target = t
                break


class BubbleCursor:
    """The bubble cursor (Grossman & Balakrishnan, CHI 2005).

    Algorithm (from the paper):
        i = index of closest target by intersecting distance (IntD)
        j = index of second closest target by intersecting distance
        radius = min(ConD_i, IntD_j)

    where, for a circular target of radius r at distance d from the cursor
    center:
        IntD = d - r      (distance to the *nearest* point on the target's border)
        ConD = d + r      (distance to the *farthest* point on the target's border)

    This guarantees the bubble always touches/contains the closest target
    and never reaches the second-closest one, so exactly one target is
    ever captured.

    Per the paper, we also leave a small GAP so the bubble doesn't always
    touch the second-closest target -- which means the bubble sometimes
    only *intersects* the closest target instead of fully containing it.
    When that happens, we morph a second, smaller bubble that quickly
    expands from that intersection to envelop the captured target
    entirely (Figure 4b in the paper), as a reinforcing visual cue that
    the target really is captured. That state is exposed as
    `.morph_target` / `.morph_radius` for the drawing code to render.
    """

    name = "Bubble"
    display_name = "Bubble Cursor"

    GAP = 1.5          # small buffer so the bubble doesn't kiss the 2nd-closest target
    MIN_RADIUS = 4.0
    EMPTY_SPACE_RADIUS = 45.0  # radius shown when there are no targets around at all

    MORPH_PAD = 4.0            # how far past the target's own edge the envelope bubble sits
    MORPH_DURATION = 0.12      # seconds for the envelope to "quickly expand" into place
    MORPH_START_FRACTION = 0.35  # envelope starts at this fraction of its final size

    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.radius = self.EMPTY_SPACE_RADIUS
        self.captured_target = None
        self.fully_contains = True  # whether the bubble completely encloses the target
        self.morph_target = None
        self.morph_progress = 0.0

    def reset(self, targets, start_pos=None):
        if start_pos:
            self.x, self.y = start_pos
        self.morph_target = None
        self.morph_progress = 0.0

    def update(self, mx, my, dt, targets):
        self.x, self.y = mx, my

        if not targets:
            self.radius = self.EMPTY_SPACE_RADIUS
            self.captured_target = None
            self.fully_contains = True
            self.morph_target = None
            self.morph_progress = 0.0
            return

        scored = []
        for t in targets:
            d = math.hypot(mx - t.x, my - t.y)
            int_d = d - t.radius
            con_d = d + t.radius
            scored.append((int_d, con_d, t))
        scored.sort(key=lambda s: s[0])

        closest_int, closest_con, closest_t = scored[0]

        if len(scored) > 1:
            second_int = scored[1][0]
            radius = min(closest_con, second_int - self.GAP)
        else:
            radius = closest_con

        # Always at least reach the closest target's near edge.
        radius = max(radius, closest_int)
        radius = max(radius, self.MIN_RADIUS)

        self.radius = radius
        self.captured_target = closest_t
        self.fully_contains = radius >= closest_con - 0.01

        if not self.fully_contains:
            if self.morph_target is not closest_t:
                self.morph_target = closest_t
                self.morph_progress = 0.0
            self.morph_progress = min(1.0, self.morph_progress + dt / self.MORPH_DURATION)
        else:
            self.morph_target = None
            self.morph_progress = 0.0

    @property
    def morph_radius(self):
        """Current radius of the envelope bubble around `.morph_target`, or
        None if no morph is currently active. Eases from a small starting
        size up to fully enclosing the target."""
        if self.morph_target is None:
            return None
        final_r = self.morph_target.radius + self.MORPH_PAD
        start_r = final_r * self.MORPH_START_FRACTION
        eased = 1.0 - (1.0 - self.morph_progress) ** 3  # ease-out cubic: quick, then settles
        return start_r + (final_r - start_r) * eased


class ObjectPointingCursor:
    """Approximation of Object Pointing (Guiard, Blanch & Beaudouin-Lafon 2004)
    as summarized in the paper's "Object Pointing" section.

    Behavior:
      - While the raw mouse stays within the current target's "safety zone"
        (a radius around the target, here target.radius + SAFETY_ZONE_PAD),
        the cursor tracks the mouse 1:1, same as a point cursor.
      - Once the mouse leaves the safety zone, if its speed is above a
        threshold, we search progressively wider angular slices
        (ANGLE_STEPS) centered on the movement direction for the nearest
        target in that direction and, if found, the cursor jumps straight
        to it (skipping the empty space in between).
      - If no target is found in any slice, or speed is below threshold,
        the cursor snaps back to the boundary of the current target instead
        of following the mouse into empty space.
    """

    name = "Object"
    display_name = "Object Pointing"

    SAFETY_ZONE_PAD = 32.0 * 3.125  # paper: 32 units == 100 px on their setup
    VELOCITY_THRESHOLD_PX_S = 90.0 * 3.125
    ANGLE_STEPS = (20.0, 25.0, 30.0)

    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.current_target = None
        self.captured_target = None
        self._prev_mouse = None

    def reset(self, targets, start_pos=None):
        """Call this whenever the scene / target list changes (new trial),
        so the cursor's notion of "current target" stays sane."""
        self.current_target = targets[0] if targets else None
        if start_pos is not None:
            self.x, self.y = start_pos
        elif self.current_target is not None:
            self.x, self.y = self.current_target.pos
        self._prev_mouse = (self.x, self.y)
        self.captured_target = self.current_target

    def set_current_target(self, target, pos=None):
        self.current_target = target
        if pos is not None:
            self.x, self.y = pos
        elif target is not None:
            self.x, self.y = target.pos
        self.captured_target = target

    def update(self, mx, my, dt, targets):
        if self._prev_mouse is None:
            self._prev_mouse = (mx, my)

        if self.current_target is None and targets:
            self.set_current_target(targets[0])

        if dt > 0:
            vx = (mx - self._prev_mouse[0]) / dt
            vy = (my - self._prev_mouse[1]) / dt
        else:
            vx = vy = 0.0
        speed = math.hypot(vx, vy)
        self._prev_mouse = (mx, my)

        if self.current_target is None:
            self.x, self.y = mx, my
            self.captured_target = None
            return

        ct = self.current_target
        safety_r = ct.radius + self.SAFETY_ZONE_PAD
        d_to_current = math.hypot(mx - ct.x, my - ct.y)

        if d_to_current <= safety_r:
            self.x, self.y = mx, my
            self.captured_target = ct
            return

        # Left the safety zone: maybe jump to a new target.
        jumped = False
        if speed >= self.VELOCITY_THRESHOLD_PX_S:
            direction = (mx - ct.x, my - ct.y)
            for half_angle in self.ANGLE_STEPS:
                candidates = [
                    t for t in targets
                    if t is not ct
                    and geometry.angle_between(direction, (t.x - ct.x, t.y - ct.y)) <= half_angle
                ]
                if candidates:
                    candidates.sort(key=lambda t: math.hypot(t.x - mx, t.y - my))
                    found = candidates[0]
                    self.current_target = found
                    self.x, self.y = found.pos
                    self.captured_target = found
                    jumped = True
                    break

        if not jumped:
            # snap back to the boundary of the current target, in the
            # direction the mouse has moved
            bx, by = geometry.point_towards(ct.pos, (mx, my), ct.radius)
            self.x, self.y = bx, by
            self.captured_target = ct


CURSOR_CLASSES = {
    "point": PointCursor,
    "bubble": BubbleCursor,
    "object": ObjectPointingCursor,
}

CURSOR_ORDER = ["point", "bubble", "object"]
