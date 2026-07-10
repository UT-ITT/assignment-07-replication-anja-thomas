import os
import csv
import time
import math
import random
import pyglet
from pyglet.window import key, mouse

from scenes.scene import Scene
from cursors.point_cursor import PointCursor
from cursors.bubble_cursor import BubbleCursor

class Target2D:
    """Represents a 2D experimental target conforming to Experiment 2 rules."""
    def __init__(self, x, y, width, is_goal=False):
        self.x = x
        self.y = y
        self.width = width
        self.radius = width / 2.0
        
        self.is_goal = is_goal
        self.is_active = False  
        self.is_highlighted = False

    def get_intersecting_distance(self, cursor_x, cursor_y):
        """2D intersecting distance: distance to target border."""
        dist = math.hypot(cursor_x - self.x, cursor_y - self.y) - self.radius
        return max(0.0, dist)

    def get_containment_distance(self, cursor_x, cursor_y):
        """2D containment distance: distance to furthest target border."""
        return math.hypot(cursor_x - self.x, cursor_y - self.y) + self.radius

    def draw(self):
        if self.is_highlighted:
            # Paper Specification: Both goal and distracters turn solid red when captured
            pyglet.shapes.Circle(self.x, self.y, self.radius, color=(255, 40, 40, 255)).draw()
        elif self.is_active:
            # Active goal target is solid green
            pyglet.shapes.Circle(self.x, self.y, self.radius, color=(40, 200, 80, 255)).draw()
        else:
            # Distracters are rendered as grey outlined circles
            pyglet.shapes.Circle(self.x, self.y, self.radius, color=(140, 140, 140, 255)).draw()
            if self.radius > 2:
                pyglet.shapes.Circle(self.x, self.y, self.radius - 1.5, color=(0, 0, 0, 255)).draw()


class Experiment2Scene(Scene):
    def __init__(self, window, manager, cursor_type):
        self.window = window
        self.manager = manager
        self.cursor_type = cursor_type
        
        self.cx = self.window.width // 2
        self.cy = self.window.height // 2

        if cursor_type == "Bubble Cursor":
            self.cursor = BubbleCursor()
        else:
            self.cursor = PointCursor()

        # Fitts' Law Matrix Variables
        self.amplitudes = [256, 512] 
        self.widths = [8, 16, 32]
        self.ew_ratios = [1.33, 2, 3] 
        self.d_levels = [0, 0.5, 1]   
        
        self.conditions = []
        for a in self.amplitudes:
            for w in self.widths:
                for ew_r in self.ew_ratios:
                    for d in self.d_levels:
                        self.conditions.append((a, w, ew_r, d))

        self.total_blocks = 2
        self.current_block = 1
        self.condition_index = 0
        self.trials_per_condition = 3
        self.current_trial = 0 
        
        self.collected_data = []
        
        self.current_block_conditions = list(self.conditions)
        random.shuffle(self.current_block_conditions)
        
        self.targets = []
        self.start_target = None
        self.goal_target = None
        
        self.state = "WAITING_FOR_START" 
        self.start_time = None
        self.trial_errors = 0
        
        self.label = pyglet.text.Label(
            '', font_name='Arial', font_size=12,
            x=20, y=self.window.height - 30, color=(255, 255, 255, 255)
        )
        
        self._load_current_condition()

    def _load_current_condition(self):
        A, W, EW_ratio, D = self.current_block_conditions[self.condition_index]
        EW = W * EW_ratio
        
        self.targets.clear()
        
        # 1. Generate Start Target at center
        self.start_target = Target2D(self.cx, self.cy, W, is_goal=True)
        self.start_target.is_active = True
        self.targets.append(self.start_target)
        
        # Bounded angle checking loop to prevent the goal spawning off-screen
        valid_angle = False
        angle = 0.0
        gx, gy = 0.0, 0.0
        padding = EW + W
        
        while not valid_angle:
            angle = random.uniform(0, 2 * math.pi)
            gx = self.cx + A * math.cos(angle)
            gy = self.cy + A * math.sin(angle)
            
            # Ensure the goal target + its EW layout remains entirely inside window limits
            if (padding < gx < self.window.width - padding) and \
               (padding < gy < self.window.height - padding):
                valid_angle = True

        # 2. Generate Goal Target using validated coordinates
        self.goal_target = Target2D(gx, gy, W, is_goal=True)
        self.targets.append(self.goal_target)
        
        # 3. Generate EW Distracters (forces target's Voronoi cell width)
        ew_offsets = [(A - EW, 0), (A + EW, 0), (A, -EW), (A, EW)]
        for ox, oy in ew_offsets:
            rx = self.cx + ox * math.cos(angle) - oy * math.sin(angle)
            ry = self.cy + ox * math.sin(angle) + oy * math.cos(angle)
            self.targets.append(Target2D(rx, ry, W))
            
        # 4. Generate Intermediate Distracters along straight ideal line path
        if D > 0:
            num_intermediate = int(5 * D) 
            distances = list(range(int(W*3), int(A - EW - W), max(1, int((A - EW - W) / (num_intermediate+1)))))
            for dist in distances[:num_intermediate]:
                ang_offset = random.uniform(math.radians(-8), math.radians(8))
                ix = self.cx + dist * math.cos(angle + ang_offset)
                iy = self.cy + dist * math.sin(angle + ang_offset)
                self.targets.append(Target2D(ix, iy, W))
                
        # 5. Generate Random Environmental Distracters safely bounded inside screen space
        for _ in range(15):
            rx = random.uniform(W, self.window.width - W)
            ry = random.uniform(W, self.window.height - W)
            
            dist_to_goal = math.hypot(rx - gx, ry - gy)
            dist_to_start = math.hypot(rx - self.cx, ry - self.cy)
            
            if dist_to_goal > (EW + W) and dist_to_start > (W * 2):
                self.targets.append(Target2D(rx, ry, W))

        self.state = "WAITING_FOR_START"
        self.trial_errors = 0
        
        self.label.text = (f"Exp 2 ({self.cursor_type}) | "
                           f"Block: {self.current_block}/{self.total_blocks} | "
                           f"Cond: {self.condition_index + 1}/{len(self.conditions)} | "
                           f"A:{A} W:{W} EW/W:{EW_ratio} D:{D}")

    def on_enter(self):
        self.window.set_mouse_visible(False)

    def on_exit(self):
        self.window.set_mouse_visible(True)

    def _get_active_targets_subset(self):
        """Filters targets dynamically. Only start target is visible/active initially."""
        if self.state == "WAITING_FOR_START":
            return [self.start_target]
        return self.targets

    def on_mouse_motion(self, x, y, dx, dy):
        if hasattr(self.cursor, 'update_position'):
            self.cursor.update_position(x, y)
        else:
            self.cursor.x = x
            self.cursor.y = y
        
        active_subset = self._get_active_targets_subset()
        
        if hasattr(self.cursor, 'update'):
            self.cursor.update(active_subset)
        
        for target in self.targets:
            target.is_highlighted = False
            
        if self.cursor_type == "Bubble Cursor":
            if hasattr(self.cursor, 'captured_target') and self.cursor.captured_target in active_subset:
                self.cursor.captured_target.is_highlighted = True
        else:
            for target in active_subset:
                if math.hypot(x - target.x, y - target.y) <= target.radius:
                    target.is_highlighted = True

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.on_mouse_motion(x, y, dx, dy)

    def on_mouse_press(self, x, y, button, modifiers):
        if button != mouse.LEFT:
            return

        A, W, EW_ratio, D = self.current_block_conditions[self.condition_index]
        active_target = self.start_target if self.state == "WAITING_FOR_START" else self.goal_target
        
        success = False
        if self.cursor_type == "Bubble Cursor":
            if hasattr(self.cursor, 'captured_target') and self.cursor.captured_target == active_target:
                success = True
        else:
            if math.hypot(x - active_target.x, y - active_target.y) <= active_target.radius:
                success = True

        if success:
            if self.state == "WAITING_FOR_START":
                # Start selection complete, unlock the 2D layout matrix trial phase
                self.state = "WAITING_FOR_GOAL"
                self.start_target.is_active = False
                self.goal_target.is_active = True
                self.start_time = time.time()
                self.trial_errors = 0
                self.on_mouse_motion(x, y, 0, 0)
            
            elif self.state == "WAITING_FOR_GOAL":
                movement_time = time.time() - self.start_time
                
                self.collected_data.append({
                    'Block': self.current_block,
                    'CursorType': self.cursor_type,
                    'Amplitude': A,
                    'Width': W,
                    'EWRatio': EW_ratio,
                    'Density': D,
                    'MovementTime': round(movement_time, 4),
                    'Errors': self.trial_errors
                })
                
                self.current_trial += 1
                if self.current_trial >= self.trials_per_condition:
                    self.current_trial = 0
                    self.condition_index += 1
                    
                    if self.condition_index >= len(self.current_block_conditions):
                        self.condition_index = 0
                        self.current_block += 1
                        
                        if self.current_block > self.total_blocks:
                            self._save_data_to_csv()
                            self._return_to_menu()
                            return
                        
                        random.shuffle(self.current_block_conditions)
                
                self._load_current_condition()
        else:
            if self.state == "WAITING_FOR_GOAL":
                self.trial_errors += 1

    def on_key_press(self, symbol, modifiers):
        if symbol == key.ESCAPE:
            self._save_data_to_csv()
            self._return_to_menu()
            return True

    def _save_data_to_csv(self):
        if not self.collected_data:
            return
            
        filename = f"experiment2_{self.cursor_type.lower().replace(' ', '_')}_data.csv"
        file_exists = os.path.isfile(filename)
        fields = ['Block', 'CursorType', 'Amplitude', 'Width', 'EWRatio', 'Density', 'MovementTime', 'Errors']
        
        try:
            with open(filename, mode='a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                if not file_exists:
                    writer.writeheader()
                writer.writerows(self.collected_data)
            print(f"Logged data metrics safely to file: {filename}")
        except Exception as e:
            print(f"Error saving to CSV: {e}")
            
        self.collected_data.clear()

    def _return_to_menu(self):
        from scenes.menu_scene import MenuScene
        self.manager.change_scene(MenuScene(self.window, self.manager))

    def update(self, dt):
        pass

    def draw(self):
        self.window.clear()
        
        for target in self._get_active_targets_subset():
            target.draw()
            
        self.cursor.draw()
        self.label.draw()