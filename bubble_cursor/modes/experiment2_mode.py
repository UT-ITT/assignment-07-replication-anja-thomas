"""
Experiment 2 from the paper: a 2D target-acquisition task with controllable
distracter density.

A green start target sits at the center of the play area. After it (and
every subsequent goal) is clicked, a new goal target appears somewhere else
and the cursor must travel to it. This repeats 9 times per trial set (not
counting the initial click on the start target), matching the paper.

Two things are manipulated per trial set:
  - EW/W: the ratio between the goal's effective width and its actual
    width, controlled -- exactly as described in the paper -- by placing
    four same-sized distracters around the goal: one before it and one
    after it along the direction of travel, and one above/below it
    perpendicular to that direction, each at a distance of EW from the
    goal's center. Because all of these distracters share the goal's own
    radius, this produces a square activation zone of width EW for the
    bubble cursor.
  - D: the density of intermediate distracters along the straight-line path
    from the previous position to the new goal, confined (as in the paper)
    to a 20-degree angular slice around the direction of travel, plus a
    matching number of distracters scattered elsewhere for overall density.

A is *not* fixed per trial set -- as in the paper, each trial set's 9
selections use each of the three amplitudes exactly three times, shuffled.
"""

import itertools
import math
import random
import time

import pyglet

import config
import geometry
from cursors import CURSOR_CLASSES
from targets import Target
from results_logger import ResultsLogger


class Experiment2Mode:
    show_os_cursor = False

    def __init__(self, app, cursor_key):
        self.app = app
        self.cursor_key = cursor_key
        self.cursor = CURSOR_CLASSES[cursor_key]()

        self.mouse_x = config.WINDOW_WIDTH / 2
        self.mouse_y = config.WINDOW_HEIGHT / 2

        self.batch = pyglet.graphics.Batch()
        self.target_shapes = []
        self.current_targets = []
        self.current_goal = None
        self.prev_pos = (config.WINDOW_WIDTH / 2, config.WINDOW_HEIGHT * 0.46)
        self.prev_target_obj = None
        self.awaiting_start_click = True
        self.error_count = 0

        self.logger = ResultsLogger(
            "experiment2",
            fieldnames=["cursor", "block", "recorded", "combo_index",
                        "selection_index", "A", "W", "EW_ratio", "D",
                        "movement_time_s", "errors"])

        combos = list(itertools.product(
            config.EXP2_WIDTHS, config.EXP2_EW_RATIOS, config.EXP2_DENSITIES))
        warmup_combo = combos[len(combos) // 2]
        self.blocks = [{"recorded": False, "combos": [warmup_combo]}]
        for _ in range(config.EXP2_BLOCKS):
            shuffled = combos[:]
            random.shuffle(shuffled)
            self.blocks.append({"recorded": True, "combos": shuffled})

        self.block_index = 0
        self.combo_index = 0
        self.finished = False
        self.results_path = None

        self._build_header()
        self._start_trial_set()

    # ------------------------------------------------------------- header
    def _build_header(self):
        self.title_label = pyglet.text.Label(
            "Experiment 2 (2D)", x=20, y=config.WINDOW_HEIGHT - 32, font_size=22,
            weight='bold', color=config.COLOR_TEXT, batch=self.batch)
        self.progress_label = pyglet.text.Label(
            "", x=20, y=config.WINDOW_HEIGHT - 62, font_size=14,
            color=config.COLOR_TEXT, batch=self.batch)
        self.condition_label = pyglet.text.Label(
            "", x=20, y=config.WINDOW_HEIGHT - 86, font_size=13,
            color=config.COLOR_SUBTEXT, batch=self.batch)
        self.hint_label = pyglet.text.Label(
            "Click the GREEN target as it appears around the screen   |   Q: menu",
            x=20, y=18, font_size=12, color=config.COLOR_SUBTEXT, batch=self.batch)
        self.result_label = pyglet.text.Label(
            "", x=config.WINDOW_WIDTH / 2, y=config.WINDOW_HEIGHT / 2,
            anchor_x="center", anchor_y="center", font_size=18, weight='bold',
            color=config.COLOR_TEXT, batch=self.batch, multiline=True,
            width=900, align="center")

    def _display_name(self):
        return {"point": "Point Cursor", "bubble": "Bubble Cursor",
                "object": "Object Pointing"}[self.cursor_key]

    def _current_block(self):
        return self.blocks[self.block_index]

    # ------------------------------------------------------------- scene
    def _clamp_point(self, p, r):
        W, H = config.WINDOW_WIDTH, config.WINDOW_HEIGHT
        x = geometry.clamp(p[0], 20 + r, W - 20 - r)
        y = geometry.clamp(p[1], 70 + r, H - 120 - r)
        return (x, y)

    def _pick_goal_position(self, origin, A_px):
        W, H = config.WINDOW_WIDTH, config.WINDOW_HEIGHT
        side_margin, top_margin, bottom_margin = 150, 130, 90
        for _ in range(50):
            ang = random.uniform(0, 360)
            gx, gy = geometry.polar_offset(origin, ang, A_px)
            if side_margin <= gx <= W - side_margin and bottom_margin <= gy <= H - top_margin:
                return (gx, gy)
        # fallback: aim roughly back towards the window center
        center = (W / 2, H / 2)
        ang = geometry.angle_of((center[0] - origin[0], center[1] - origin[1]))
        dist = min(A_px, geometry.distance(origin, center) * 0.8, W / 2 - side_margin)
        gx, gy = geometry.polar_offset(origin, ang, max(dist, 20))
        gx = geometry.clamp(gx, side_margin, W - side_margin)
        gy = geometry.clamp(gy, bottom_margin, H - top_margin)
        return (gx, gy)

    def _make_outside_distractors(self, origin, goal_pos, r_px, count, existing):
        if count <= 0:
            return []
        W, H = config.WINDOW_WIDTH, config.WINDOW_HEIGHT
        direction = (goal_pos[0] - origin[0], goal_pos[1] - origin[1])
        extras = []
        attempts = 0
        while len(extras) < count and attempts < 500:
            attempts += 1
            x = random.uniform(20 + r_px, W - 20 - r_px)
            y = random.uniform(70 + r_px, H - 120 - r_px)
            vec = (x - origin[0], y - origin[1])
            if geometry.angle_between(direction, vec) <= 12.0:
                continue  # stay clear of the 20-degree travel slice
            if any(geometry.distance((x, y), t.pos) < r_px + t.radius + 8
                   for t in existing + extras):
                continue
            extras.append(Target(x, y, r_px, kind="distractor"))
        return extras

    def _place_next_goal(self):
        W_units = self.current_W
        ew_ratio = self.current_EWratio
        D = self.current_D
        A = self.amp_sequence[self.selection_index]
        self.current_amp_for_selection = A

        A_px = A * config.UNIT_PX
        r_px = max(3.0, (W_units * config.UNIT_PX) / 2.0)
        ew_px = ew_ratio * W_units * config.UNIT_PX

        origin = self.prev_pos
        goal_pos = self._pick_goal_position(origin, A_px)
        goal = Target(goal_pos[0], goal_pos[1], r_px, is_goal=True, kind="goal")

        dx, dy = goal_pos[0] - origin[0], goal_pos[1] - origin[1]
        path_len = math.hypot(dx, dy) or 1.0
        ux, uy = dx / path_len, dy / path_len
        perp_x, perp_y = -uy, ux

        targets = [goal]

        frame_specs = [
            (goal_pos[0] - ux * ew_px, goal_pos[1] - uy * ew_px),   # before, along path
            (goal_pos[0] + ux * ew_px, goal_pos[1] + uy * ew_px),   # after, along path
            (goal_pos[0] + perp_x * ew_px, goal_pos[1] + perp_y * ew_px),  # above
            (goal_pos[0] - perp_x * ew_px, goal_pos[1] - perp_y * ew_px),  # below
        ]
        for fx, fy in frame_specs:
            cx, cy = self._clamp_point((fx, fy), r_px)
            targets.append(Target(cx, cy, r_px, kind="distractor"))

        spacing = 2 * r_px + 4
        max_intermediate = max(0, int(path_len // spacing) - 1)
        n_extra = round(D * max_intermediate)

        for k in range(n_extra):
            t_frac = 0.15 + 0.7 * ((k + 1) / (n_extra + 1))
            base_x = origin[0] + dx * t_frac
            base_y = origin[1] + dy * t_frac
            max_lateral = math.tan(math.radians(10.0)) * (path_len * t_frac)
            lateral = random.uniform(-max_lateral, max_lateral)
            ix, iy = base_x + perp_x * lateral, base_y + perp_y * lateral
            ix, iy = self._clamp_point((ix, iy), r_px)
            targets.append(Target(ix, iy, r_px, kind="distractor"))

        targets.extend(self._make_outside_distractors(origin, goal_pos, r_px, n_extra, targets))

        self._install_scene(targets, goal)
        self.error_count = 0
        self.phase_start_time = time.perf_counter()

    def _install_scene(self, targets, goal):
        for (_, fill, ring) in self.target_shapes:
            fill.delete()
            ring.delete()
        self.target_shapes = []
        self.current_targets = targets
        self.current_goal = goal

        for t in targets:
            ring = pyglet.shapes.Arc(t.x, t.y, t.radius, thickness=2,
                                      color=config.COLOR_DISTRACTOR_OUTLINE, batch=self.batch)
            fill = pyglet.shapes.Circle(t.x, t.y, max(1.0, t.radius - 1),
                                         color=config.COLOR_GOAL, batch=self.batch)
            fill.opacity = 255 if t.is_goal else 0
            self.target_shapes.append((t, fill, ring))

        if not hasattr(self, "bubble_shape"):
            self.bubble_shape = pyglet.shapes.Circle(
                self.mouse_x, self.mouse_y, 20, color=config.COLOR_BUBBLE_FILL_EXP2,
                batch=self.batch)
            self.bubble_shape.opacity = config.COLOR_BUBBLE_OPACITY
            self.morph_shape = pyglet.shapes.Circle(
                self.mouse_x, self.mouse_y, 1, color=config.COLOR_BUBBLE_FILL_EXP2,
                batch=self.batch)
            self.morph_shape.opacity = 0
            self.cross_shape = pyglet.shapes.Circle(
                self.mouse_x, self.mouse_y, 4, color=config.COLOR_POINT_CROSS, batch=self.batch)

    def _start_trial_set(self):
        block = self._current_block()
        while self.combo_index >= len(block["combos"]):
            self.block_index += 1
            self.combo_index = 0
            if self.block_index >= len(self.blocks):
                self._finish()
                return
            block = self._current_block()

        W, ew_ratio, D = block["combos"][self.combo_index]
        self.current_W, self.current_EWratio, self.current_D = W, ew_ratio, D

        amps = list(config.EXP2_AMPLITUDES) * 3
        random.shuffle(amps)
        self.amp_sequence = amps
        self.selection_index = 0
        self.current_amp_for_selection = amps[0]

        play_center = (config.WINDOW_WIDTH / 2, config.WINDOW_HEIGHT * 0.46)
        r_px = max(3.0, (W * config.UNIT_PX) / 2.0)
        start_target = Target(play_center[0], play_center[1], r_px, is_goal=True, kind="start")
        self._install_scene([start_target], start_target)

        self.prev_pos = start_target.pos
        self.prev_target_obj = start_target
        self.awaiting_start_click = True
        self.error_count = 0
        self.phase_start_time = time.perf_counter()

        if hasattr(self.cursor, "reset"):
            self.cursor.reset(self.current_targets, start_pos=(self.mouse_x, self.mouse_y))

    def _advance_from(self, clicked_target):
        if hasattr(self.cursor, "set_current_target"):
            self.cursor.set_current_target(clicked_target, pos=clicked_target.pos)
        self.prev_pos = clicked_target.pos
        self.prev_target_obj = clicked_target

    def _finish(self):
        self.finished = True
        self.results_path = self.logger.save()
        mts = [r["movement_time_s"] for r in self.logger.rows]
        mean_mt = sum(mts) / len(mts) if mts else 0.0
        errs = [r["errors"] for r in self.logger.rows]
        err_rate = (sum(1 for e in errs if e > 0) / len(errs) * 100.0) if errs else 0.0
        lines = [
            "Experiment 2 complete!",
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

    # ------------------------------------------------------------- events
    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x, self.mouse_y = x, y

    def on_mouse_press(self, x, y, button, modifiers):
        if self.finished:
            return
        cap = self.cursor.captured_target
        now = time.perf_counter()

        if self.awaiting_start_click:
            if cap is self.current_goal:
                self._advance_from(self.current_goal)
                self.awaiting_start_click = False
                self._place_next_goal()
            return

        if cap is self.current_goal:
            mt = now - self.phase_start_time
            if self._current_block()["recorded"]:
                self.logger.log(
                    cursor=self.cursor_key, block=self.block_index, recorded=True,
                    combo_index=self.combo_index, selection_index=self.selection_index,
                    A=self.current_amp_for_selection, W=self.current_W,
                    EW_ratio=self.current_EWratio, D=self.current_D,
                    movement_time_s=round(mt, 4), errors=self.error_count)
            self._advance_from(self.current_goal)
            self.selection_index += 1
            if self.selection_index >= len(self.amp_sequence):
                self.combo_index += 1
                self._start_trial_set()
            else:
                self._place_next_goal()
        else:
            self.error_count += 1

    def on_key_press(self, symbol, modifiers):
        pass

    # --------------------------------------------------------------- loop
    def update(self, dt):
        if self.finished:
            return
        self.cursor.update(self.mouse_x, self.mouse_y, dt, self.current_targets)

        for (t, fill, ring) in self.target_shapes:
            captured = self.cursor.captured_target is t
            if captured:
                fill.color = config.COLOR_CAPTURED_EXP2
                fill.opacity = 230
            elif t.is_goal:
                fill.color = config.COLOR_GOAL
                fill.opacity = 255
            else:
                fill.opacity = 0

        self._update_cursor_shapes()

        block = self._current_block()
        tag = "WARM-UP (not recorded)" if not block["recorded"] else \
            f"Block {self.block_index} / {config.EXP2_BLOCKS}"
        combo_total = len(block["combos"])
        stage = "start target" if self.awaiting_start_click else \
            f"selection {self.selection_index + 1}/{len(self.amp_sequence)}"
        self.progress_label.text = (
            f"{tag}   |   Condition {self.combo_index + 1}/{combo_total}   |   {stage}")
        self.condition_label.text = (
            f"Cursor: {self._display_name()}   |   W={self.current_W}  "
            f"EW/W={self.current_EWratio}  D={self.current_D}")

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
