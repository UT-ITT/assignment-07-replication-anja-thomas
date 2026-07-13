"""
Experiment 1 from the paper: a reciprocal 1D pointing task.

Two goal targets sit on a fixed horizontal line, equidistant from the
center (amplitude A). The green target is the one to select; after a
successful click the colors swap and you move to the other one. Movement
is restricted to the horizontal line (as in the paper), regardless of
cursor type.

Distracters of the goal's own width are placed so as to control the
*effective width* (EW) of both goal targets. The paper controls EW with an
additional, separately-published placement technique (ref [7] in the
paper) that isn't detailed there. This replica instead places two framing
distracters of the same radius as the goal along the axis -- one between
the goal and the display center, one beyond it -- at a center-to-center
distance of EW. For equal-radius circles, the bubble-cursor Voronoi
boundary between two neighbors sits exactly halfway between them, so this
placement makes the goal's on-axis effective width exactly EW. A handful
of extra same-line-adjacent distracters of random size are scattered
elsewhere purely for visual density, kept far enough away that they can't
be captured before the controlled framing distracters.
"""

import itertools
import random
import time

import pyglet
from pyglet.window import key

import config
import geometry
from cursors import CURSOR_CLASSES
from targets import Target
from results_logger import ResultsLogger


class Experiment1Mode:
    show_os_cursor = False

    def __init__(self, app, cursor_key):
        self.app = app
        self.cursor_key = cursor_key
        self.cursor = CURSOR_CLASSES[cursor_key]()

        self.line_y = config.WINDOW_HEIGHT * 0.44
        self.mouse_x = config.WINDOW_WIDTH / 2

        self.batch = pyglet.graphics.Batch()
        self.target_shapes = []  # list of (Target, fill_circle, ring_arc)
        self.current_targets = []
        self.left_goal = None
        self.right_goal = None
        self.active_target = None
        self.inactive_target = None

        self.logger = ResultsLogger(
            "experiment1",
            fieldnames=["cursor", "block", "recorded", "combo_index",
                        "A", "W", "EW", "selection_index",
                        "movement_time_s", "errors"])

        combos = list(itertools.product(
            config.EXP1_AMPLITUDES, config.EXP1_WIDTHS, config.EXP1_EFFECTIVE_WIDTHS))
        warmup_combo = combos[len(combos) // 2]

        self.blocks = [{"recorded": False, "combos": [warmup_combo] * 3}]
        for _ in range(config.EXP1_BLOCKS):
            shuffled = combos[:]
            random.shuffle(shuffled)
            self.blocks.append({"recorded": True, "combos": shuffled})
        self.total_recorded_combos = config.EXP1_BLOCKS * len(combos)

        self.block_index = 0
        self.combo_index = 0
        self.finished = False
        self.results_path = None

        self.selection_index = 0
        self.error_count = 0
        self.phase_start_time = time.perf_counter()

        self._build_header()
        self._start_combo()

    # ------------------------------------------------------------- header
    def _build_header(self):
        self.title_label = pyglet.text.Label(
            "Experiment 1 (1D)", x=20, y=config.WINDOW_HEIGHT - 32, font_size=22,
            weight='bold', color=config.COLOR_TEXT, batch=self.batch)
        self.progress_label = pyglet.text.Label(
            "", x=20, y=config.WINDOW_HEIGHT - 62, font_size=14,
            color=config.COLOR_TEXT, batch=self.batch)
        self.condition_label = pyglet.text.Label(
            "", x=20, y=config.WINDOW_HEIGHT - 86, font_size=13,
            color=config.COLOR_SUBTEXT, batch=self.batch)
        self.hint_label = pyglet.text.Label(
            "Click the GREEN target, back and forth   |   Q: menu",
            x=20, y=18, font_size=12, color=config.COLOR_SUBTEXT, batch=self.batch)
        self.result_label = pyglet.text.Label(
            "", x=config.WINDOW_WIDTH / 2, y=config.WINDOW_HEIGHT / 2,
            anchor_x="center", anchor_y="center", font_size=18, weight='bold',
            color=config.COLOR_TEXT, batch=self.batch, multiline=True,
            width=900, align="center")
        self.result_label.text = ""

    # ------------------------------------------------------------- scene
    def _current_block(self):
        return self.blocks[self.block_index]

    def _build_scene(self, A, W, EW):
        A_px = A * config.UNIT_PX
        r_px = max(3.0, (W * config.UNIT_PX) / 2.0)
        ew_px = EW * config.UNIT_PX
        cx = config.WINDOW_WIDTH / 2
        cy = self.line_y

        left_x = geometry.clamp(cx - A_px, 40, config.WINDOW_WIDTH - 40)
        right_x = geometry.clamp(cx + A_px, 40, config.WINDOW_WIDTH - 40)

        left_goal = Target(left_x, cy, r_px, is_goal=True, kind="goal")
        right_goal = Target(right_x, cy, r_px, is_goal=True, kind="goal")

        targets = [left_goal, right_goal]

        frame_positions = [
            geometry.clamp(left_x + ew_px, 40, config.WINDOW_WIDTH - 40),   # left's inner neighbor
            geometry.clamp(left_x - ew_px, 40, config.WINDOW_WIDTH - 40),   # left's outer neighbor
            geometry.clamp(right_x - ew_px, 40, config.WINDOW_WIDTH - 40),  # right's inner neighbor
            geometry.clamp(right_x + ew_px, 40, config.WINDOW_WIDTH - 40),  # right's outer neighbor
        ]
        for fx in frame_positions:
            targets.append(Target(fx, cy, r_px, kind="distractor"))

        targets.extend(self._make_extra_distractors(left_goal, right_goal, ew_px))

        return targets, left_goal, right_goal

    def _make_extra_distractors(self, left_goal, right_goal, ew_px, count=6):
        extras = []
        W, H = config.WINDOW_WIDTH, config.WINDOW_HEIGHT
        goal_centers = [left_goal.pos, right_goal.pos]
        placed = []
        attempts = 0
        while len(extras) < count and attempts < 400:
            attempts += 1
            r = random.uniform(6, 16)
            x = random.uniform(50, W - 50)
            y = random.uniform(50, H - 170)
            if any(geometry.distance((x, y), gc) < ew_px * 1.15 for gc in goal_centers):
                continue
            if any(geometry.distance((x, y), t.pos) < r + t.radius + 10 for t in placed):
                continue
            t = Target(x, y, r, kind="distractor")
            placed.append(t)
            extras.append(t)
        return extras

    def _install_scene(self, targets):
        for (_, fill, ring) in self.target_shapes:
            fill.delete()
            ring.delete()
        self.target_shapes = []
        self.current_targets = targets
        for t in targets:
            ring = pyglet.shapes.Arc(t.x, t.y, t.radius, thickness=2,
                                      color=config.COLOR_DISTRACTOR_OUTLINE, batch=self.batch)
            fill = pyglet.shapes.Circle(t.x, t.y, max(1.0, t.radius - 1),
                                         color=config.COLOR_INACTIVE_GOAL, batch=self.batch)
            fill.opacity = 0
            self.target_shapes.append((t, fill, ring))

        self.bubble_shape = getattr(self, "bubble_shape", None)
        if self.bubble_shape is None:
            self.bubble_shape = pyglet.shapes.Circle(
                self.mouse_x, self.line_y, 20, color=config.COLOR_BUBBLE_FILL, batch=self.batch)
            self.bubble_shape.opacity = config.COLOR_BUBBLE_OPACITY
            self.morph_shape = pyglet.shapes.Circle(
                self.mouse_x, self.line_y, 1, color=config.COLOR_BUBBLE_FILL, batch=self.batch)
            self.morph_shape.opacity = 0
            self.cross_shape = pyglet.shapes.Circle(
                self.mouse_x, self.line_y, 4, color=config.COLOR_POINT_CROSS, batch=self.batch)

    def _start_combo(self):
        block = self._current_block()
        while self.combo_index >= len(block["combos"]):
            self.block_index += 1
            self.combo_index = 0
            if self.block_index >= len(self.blocks):
                self._finish()
                return
            block = self._current_block()

        A, W, EW = block["combos"][self.combo_index]
        self.current_A, self.current_W, self.current_EW = A, W, EW
        targets, left_goal, right_goal = self._build_scene(A, W, EW)
        self._install_scene(targets)
        self.left_goal, self.right_goal = left_goal, right_goal

        self.active_target = right_goal if random.random() < 0.5 else left_goal
        self.inactive_target = left_goal if self.active_target is right_goal else right_goal

        self.selection_index = 0
        self.error_count = 0
        self.phase_start_time = time.perf_counter()

        if hasattr(self.cursor, "reset"):
            self.cursor.reset(self.current_targets, start_pos=(self.mouse_x, self.line_y))

    def _finish(self):
        self.finished = True
        self.results_path = self.logger.save()
        mts = [r["movement_time_s"] for r in self.logger.rows]
        mean_mt = sum(mts) / len(mts) if mts else 0.0
        errs = [r["errors"] for r in self.logger.rows]
        err_rate = (sum(1 for e in errs if e > 0) / len(errs) * 100.0) if errs else 0.0
        lines = [
            "Experiment 1 complete!",
            "",
            f"Cursor: {self._display_name()}",
            f"Trials recorded: {len(self.logger.rows)}",
            f"Mean movement time: {mean_mt:.3f} s",
            f"Trials with a mis-click: {err_rate:.1f}%",
        ]
        if self.results_path:
            lines.append(f"Saved to: {self.results_path}")
        lines.append("")
        lines.append("Press Q to return to the menu.")
        self.result_label.text = "\n".join(lines)
        for (_, fill, ring) in self.target_shapes:
            fill.delete()
            ring.delete()
        self.target_shapes = []
        self.current_targets = []
        self.bubble_shape.opacity = 0
        self.morph_shape.opacity = 0
        self.cross_shape.opacity = 0

    def _display_name(self):
        return {"point": "Point Cursor", "bubble": "Bubble Cursor",
                "object": "Object Pointing"}[self.cursor_key]

    # ------------------------------------------------------------- events
    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x

    def on_mouse_press(self, x, y, button, modifiers):
        if self.finished:
            return
        cap = self.cursor.captured_target
        now = time.perf_counter()
        if cap is self.active_target:
            mt = now - self.phase_start_time
            self.selection_index += 1
            if self._current_block()["recorded"]:
                self.logger.log(
                    cursor=self.cursor_key, block=self.block_index,
                    recorded=True, combo_index=self.combo_index,
                    A=self.current_A, W=self.current_W, EW=self.current_EW,
                    selection_index=self.selection_index,
                    movement_time_s=round(mt, 4), errors=self.error_count)
            self.active_target, self.inactive_target = self.inactive_target, self.active_target
            self.error_count = 0
            self.phase_start_time = now
            if self.selection_index >= config.EXP1_SELECTIONS_PER_SET:
                self.combo_index += 1
                self._start_combo()
        else:
            self.error_count += 1

    def on_key_press(self, symbol, modifiers):
        pass

    # --------------------------------------------------------------- loop
    def update(self, dt):
        if self.finished:
            return
        self.cursor.update(self.mouse_x, self.line_y, dt, self.current_targets)

        for (t, fill, ring) in self.target_shapes:
            captured = self.cursor.captured_target is t
            if captured:
                fill.color = config.COLOR_CAPTURED_EXP1
                fill.opacity = 220
            elif t is self.active_target:
                fill.color = config.COLOR_GOAL
                fill.opacity = 255
            elif t is self.inactive_target:
                fill.color = config.COLOR_INACTIVE_GOAL
                fill.opacity = 255
            else:
                fill.opacity = 0

        self._update_cursor_shapes()

        block = self._current_block()
        tag = "WARM-UP (not recorded)" if not block["recorded"] else \
            f"Block {self.block_index} / {config.EXP1_BLOCKS}"
        combo_total = len(block["combos"])
        self.progress_label.text = (
            f"{tag}   |   Condition {self.combo_index + 1}/{combo_total}   |   "
            f"Selection {self.selection_index + 1}/{config.EXP1_SELECTIONS_PER_SET}")
        self.condition_label.text = (
            f"Cursor: {self._display_name()}   |   A={self.current_A}  W={self.current_W}  "
            f"EW={self.current_EW}")

    def _update_cursor_shapes(self):
        if self.cursor_key == "bubble":
            self.bubble_shape.opacity = config.COLOR_BUBBLE_OPACITY
            self.bubble_shape.x, self.bubble_shape.y = self.cursor.x, self.cursor.y
            self.bubble_shape.radius = max(2, self.cursor.radius)
            self.cross_shape.opacity = 255
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
            self.cross_shape.opacity = 255
            self.cross_shape.x, self.cross_shape.y = self.cursor.x, self.cursor.y
            self.cross_shape.radius = 5
            self.cross_shape.color = (
                config.COLOR_OBJECT_CROSS if self.cursor_key == "object"
                else config.COLOR_POINT_CROSS)

    def draw(self):
        self.batch.draw()
