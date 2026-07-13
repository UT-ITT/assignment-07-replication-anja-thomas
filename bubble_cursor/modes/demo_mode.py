import random

import numpy as np
import pyglet
from pyglet.window import key
from scipy.spatial import Voronoi

import config
import geometry
from cursors import CURSOR_CLASSES
from targets import Target


class DemoMode:
    """Reproduces the intuition of Figure 1 in the paper: scatter targets of
    varied sizes around the screen and let you feel how the Point / Bubble /
    Object cursor each decide what would be selected."""

    show_os_cursor = False
    NUM_TARGETS = 16

    def __init__(self, app, cursor_key):
        self.app = app
        self.cursor_key = cursor_key
        self.cursor = CURSOR_CLASSES[cursor_key]()
        self.mouse_x = config.WINDOW_WIDTH / 2
        self.mouse_y = config.WINDOW_HEIGHT / 2

        self.batch = pyglet.graphics.Batch()
        self.targets = []
        self.target_shapes = []  # (fill_circle, ring_arc) per target, persistent
        self.show_voronoi = False
        self.voronoi_lines = []

        self._build_header()
        self._make_layout()
        self._build_cursor_shapes()

        if hasattr(self.cursor, "reset"):
            self.cursor.reset(self.targets, start_pos=(self.mouse_x, self.mouse_y))

    # ------------------------------------------------------------------ UI
    def _build_header(self):
        self.title_label = pyglet.text.Label(
            "Demo", x=20, y=config.WINDOW_HEIGHT - 34, font_size=22, weight='bold',
            color=config.COLOR_TEXT, batch=self.batch)
        self.info_label = pyglet.text.Label(
            "", x=20, y=config.WINDOW_HEIGHT - 64, font_size=14,
            color=config.COLOR_TEXT, batch=self.batch)
        self.hint_label = pyglet.text.Label(
            "1: Point   2: Bubble   3: Object Pointing   |   R: new layout   |   "
            "T: Voronoi   |   Q: menu",
            x=20, y=18, font_size=12, color=config.COLOR_SUBTEXT, batch=self.batch)

    def _make_layout(self):
        random.seed()
        self.targets = []
        self.target_shapes = []
        margin = 90
        top_margin = 130
        bottom_margin = 60
        W, H = config.WINDOW_WIDTH, config.WINDOW_HEIGHT
        attempts = 0
        while len(self.targets) < self.NUM_TARGETS and attempts < 2000:
            attempts += 1
            r = random.uniform(9, 30)
            x = random.uniform(margin, W - margin)
            y = random.uniform(bottom_margin, H - top_margin)
            ok = True
            for t in self.targets:
                if geometry.distance((x, y), t.pos) < r + t.radius + 16:
                    ok = False
                    break
            if ok:
                t = Target(x, y, r, kind="distractor")
                self.targets.append(t)

        for t in self.targets:
            ring = pyglet.shapes.Arc(t.x, t.y, t.radius, thickness=2,
                                      color=config.COLOR_DISTRACTOR_OUTLINE,
                                      batch=self.batch)
            fill = pyglet.shapes.Circle(t.x, t.y, t.radius,
                                         color=config.COLOR_CAPTURED_EXP1,
                                         batch=self.batch)
            fill.opacity = 0  # hidden until captured
            self.target_shapes.append((fill, ring))

        self._build_voronoi()

    def _build_voronoi(self):
        """Compute the Voronoi diagram over target centers and store it as
        persistent Line shapes in the batch (visibility toggled via opacity)."""
        for line in self.voronoi_lines:
            line.delete()
        self.voronoi_lines = []

        if len(self.targets) < 4:
            return

        color = getattr(config, "COLOR_VORONOI", (120, 200, 255))
        opacity = 130 if self.show_voronoi else 0

        pts = np.array([t.pos for t in self.targets])
        vor = Voronoi(pts)
        center = pts.mean(axis=0)
        far = max(config.WINDOW_WIDTH, config.WINDOW_HEIGHT) * 2

        for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices):
            if v1 >= 0 and v2 >= 0:
                x1, y1 = vor.vertices[v1]
                x2, y2 = vor.vertices[v2]
            else:
                # One end of the ridge is at infinity: extend it far enough
                # that the window edge clips it naturally.
                v_known = v1 if v1 >= 0 else v2
                x1, y1 = vor.vertices[v_known]
                tangent = pts[p2] - pts[p1]
                tangent = tangent / np.linalg.norm(tangent)
                normal = np.array([-tangent[1], tangent[0]])
                midpoint = pts[[p1, p2]].mean(axis=0)
                if np.dot(midpoint - center, normal) < 0:
                    normal = -normal
                x2, y2 = np.array([x1, y1]) + normal * far

            line = pyglet.shapes.Line(x1, y1, x2, y2, thickness=1.5,
                                       color=color, batch=self.batch)
            line.opacity = opacity
            self.voronoi_lines.append(line)

    def _build_cursor_shapes(self):
        self.bubble_shape = pyglet.shapes.Circle(
            self.mouse_x, self.mouse_y, 30, color=config.COLOR_BUBBLE_FILL,
            batch=self.batch)
        self.bubble_shape.opacity = config.COLOR_BUBBLE_OPACITY
        self.morph_shape = pyglet.shapes.Circle(
            self.mouse_x, self.mouse_y, 1, color=config.COLOR_BUBBLE_FILL,
            batch=self.batch)
        self.morph_shape.opacity = 0
        self.cross_shape = pyglet.shapes.Circle(
            self.mouse_x, self.mouse_y, 4, color=config.COLOR_POINT_CROSS,
            batch=self.batch)

    def _switch_cursor(self, key_):
        self.cursor_key = key_
        self.cursor = CURSOR_CLASSES[key_]()
        if hasattr(self.cursor, "reset"):
            self.cursor.reset(self.targets, start_pos=(self.mouse_x, self.mouse_y))

    # ------------------------------------------------------------- events
    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x, self.mouse_y = x, y

    def on_mouse_press(self, x, y, button, modifiers):
        pass

    def on_key_press(self, symbol, modifiers):
        if symbol == key._1:
            self._switch_cursor("point")
        elif symbol == key._2:
            self._switch_cursor("bubble")
        elif symbol == key._3:
            self._switch_cursor("object")
        elif symbol == key.R:
            self._make_layout()
            if hasattr(self.cursor, "reset"):
                self.cursor.reset(self.targets, start_pos=(self.mouse_x, self.mouse_y))
        elif symbol == key.T:
            self.show_voronoi = not self.show_voronoi
            opacity = 130 if self.show_voronoi else 0
            for line in self.voronoi_lines:
                line.opacity = opacity

    # --------------------------------------------------------------- loop
    def update(self, dt):
        self.cursor.update(self.mouse_x, self.mouse_y, dt, self.targets)

        for t, (fill, ring) in zip(self.targets, self.target_shapes):
            captured = self.cursor.captured_target is t
            fill.opacity = 210 if captured else 0

        if self.cursor_key == "bubble":
            self.bubble_shape.opacity = config.COLOR_BUBBLE_OPACITY
            self.bubble_shape.x, self.bubble_shape.y = self.cursor.x, self.cursor.y
            self.bubble_shape.radius = max(2, self.cursor.radius)
            self.cross_shape.x, self.cross_shape.y = self.cursor.x, self.cursor.y
            self.cross_shape.radius = 3
            self.cross_shape.color = config.COLOR_POINT_CROSS

            morph_target = getattr(self.cursor, "morph_target", None)
            if morph_target is not None:
                self.morph_shape.opacity = min(255, config.COLOR_BUBBLE_OPACITY + 90)
                self.morph_shape.x, self.morph_shape.y = morph_target.x, morph_target.y
                self.morph_shape.radius = max(1, self.cursor.morph_radius)
            else:
                self.morph_shape.opacity = 0
        else:
            self.bubble_shape.opacity = 0
            self.morph_shape.opacity = 0
            self.cross_shape.x, self.cross_shape.y = self.cursor.x, self.cursor.y
            self.cross_shape.radius = 5
            self.cross_shape.color = (
                config.COLOR_OBJECT_CROSS if self.cursor_key == "object"
                else config.COLOR_POINT_CROSS)

        cap = self.cursor.captured_target
        cap_text = "none" if cap is None else f"({cap.x:.0f}, {cap.y:.0f}), r={cap.radius:.0f}"
        self.title_label.text = f"Demo -- {self._display_name()}"
        self.info_label.text = f"Captured target: {cap_text}"

    def _display_name(self):
        return {"point": "Point Cursor", "bubble": "Bubble Cursor",
                "object": "Object Pointing"}[self.cursor_key]

    def draw(self):
        self.batch.draw()