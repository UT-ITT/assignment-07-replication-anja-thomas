import os
import csv
import time
import random
import pyglet
from pyglet.window import key, mouse

from scenes.scene import Scene
from cursors.point_cursor import PointCursor
from cursors.bubble_cursor import BubbleCursor

class Target1D:
    """Represents a 1D experimental target (goal or distracter)."""
    def __init__(self, x, y, width, is_goal=False):
        self.x = x
        self.y = y
        self.width = width
        self.radius = width / 2.0
        self.is_goal = is_goal
        self.is_active = False  # True if it's the green target
        self.is_highlighted = False

    def get_intersecting_distance(self, cursor_x, cursor_y):
        """1D intersecting distance: distance to target border along the horizontal axis."""
        dist = abs(cursor_x - self.x) - self.radius
        return max(0.0, dist)

    def get_containment_distance(self, cursor_x, cursor_y):
        """1D containment distance: distance to furthest target border along the horizontal axis."""
        return abs(cursor_x - self.x) + self.radius

    def draw(self):
        if self.is_goal:
            if self.is_highlighted:
                fill_color = (40, 120, 230, 255)  # Highlighted color matching bubble cursor
            elif self.is_active:
                fill_color = (40, 200, 80, 255)   # Active goal color (Green)
            else:
                fill_color = (140, 140, 140, 255) # Inactive goal color
                
            circle = pyglet.shapes.Circle(self.x, self.y, self.radius, color=fill_color)
            circle.draw()
        else:
            # Distracters are drawn as hollow circles/rings
            outline_color = (40, 120, 230, 255) if self.is_highlighted else (140, 140, 140, 255)
            circle = pyglet.shapes.Circle(self.x, self.y, self.radius, color=outline_color)
            circle.draw()
            if self.radius > 2:
                inner = pyglet.shapes.Circle(self.x, self.y, self.radius - 1.5, color=(0, 0, 0, 255))
                inner.draw()


class Experiment1Scene(Scene):
    def __init__(self, window, manager, cursor_type):
        self.window = window
        self.manager = manager
        self.cursor_type = cursor_type
        
        # Center coordinates
        self.cx = self.window.width // 2
        self.cy = self.window.height // 2

        # Initialize the chosen cursor
        if cursor_type == "Bubble Cursor":
            self.cursor = BubbleCursor()
        else:
            self.cursor = PointCursor()

        # Fitts' Law Matrix Variables (Experiment 1 Definition)
        self.amplitudes = [192, 384, 768]
        self.widths = [8, 16, 24]
        self.effective_widths = [32, 64, 96]
        
        # Generate all experimental conditions
        self.conditions = []
        for a in self.amplitudes:
            for w in self.widths:
                for ew in self.effective_widths:
                    self.conditions.append((a, w, ew))

        self.total_blocks = 2
        self.current_block = 1
        self.condition_index = 0
        self.click_count_in_set = 0 
        
        self.collected_data = []
        
        # Shuffle conditions for the first block
        self.current_block_conditions = list(self.conditions)
        random.shuffle(self.current_block_conditions)
        
        self.targets = []
        self.left_target = None
        self.right_target = None
        
        self.start_time = None
        self.trial_errors = 0
        
        # UI Information Text Label
        self.label = pyglet.text.Label(
            '', font_name='Arial', font_size=12,
            x=20, y=self.window.height - 30, color=(255, 255, 255, 255)
        )
        
        self._load_current_condition()

    def _load_current_condition(self):
        A, W, EW = self.current_block_conditions[self.condition_index]
        self.targets.clear()
        
        # Create primary 1D target pairs
        self.left_target = Target1D(self.cx - (A / 2), self.cy, W, is_goal=True)
        self.right_target = Target1D(self.cx + (A / 2), self.cy, W, is_goal=True)
        
        # Alternating task control
        if self.click_count_in_set == 0:
            self.left_target.is_active = True
        else:
            self.left_target.is_active = random.choice([True, False])
        self.right_target.is_active = not self.left_target.is_active
        
        self.targets.extend([self.left_target, self.right_target])
        
        # Surround them with 1D distracters matching the Effective Width (EW) layout rules
        left_distracter_outer = Target1D(self.left_target.x - EW, self.cy, W, is_goal=False)
        left_distracter_inner = Target1D(self.left_target.x + EW, self.cy, W, is_goal=False)
        right_distracter_inner = Target1D(self.right_target.x - EW, self.cy, W, is_goal=False)
        right_distracter_outer = Target1D(self.right_target.x + EW, self.cy, W, is_goal=False)
        
        self.targets.extend([left_distracter_outer, left_distracter_inner, right_distracter_inner, right_distracter_outer])
        
        # Reset counters and timer
        self.trial_errors = 0
        self.start_time = time.time()
        
        self.label.text = (f"Experiment 1 ({self.cursor_type}) | "
                           f"Block: {self.current_block}/{self.total_blocks} | "
                           f"Condition: {self.condition_index + 1}/{len(self.conditions)} | "
                           f"Parameters -> A: {A}, W: {W}, EW: {EW}")

    def on_enter(self):
        self.window.set_mouse_visible(False)

    def on_exit(self):
        self.window.set_mouse_visible(True)

    def on_mouse_motion(self, x, y, dx, dy):
        # 1D constraint: Lock cursor movement to the horizontal targets axis line
        fixed_y = self.cy
        
        if hasattr(self.cursor, 'update_position'):
            self.cursor.update_position(x, fixed_y)
        else:
            self.cursor.x = x
            self.cursor.y = fixed_y
        
        # Run your custom visual morphing & distance calculation updates
        if hasattr(self.cursor, 'update'):
            self.cursor.update(self.targets)
        
        # Clear previous frame highlights
        for target in self.targets:
            target.is_highlighted = False
            
        # Synchronize highlights directly from your object's custom attribute updates
        if self.cursor_type == "Bubble Cursor":
            if hasattr(self.cursor, 'captured_target') and self.cursor.captured_target:
                self.cursor.captured_target.is_highlighted = True
        else:
            for target in self.targets:
                if abs(x - target.x) <= target.radius:
                    target.is_highlighted = True

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.on_mouse_motion(x, y, dx, dy)

    def on_mouse_press(self, x, y, button, modifiers):
        if button != mouse.LEFT:
            return

        A, W, EW = self.current_block_conditions[self.condition_index]
        active_target = self.left_target if self.left_target.is_active else self.right_target
        
        success = False
        if self.cursor_type == "Bubble Cursor":
            # Seamless verification using your class's structural output
            if hasattr(self.cursor, 'captured_target') and self.cursor.captured_target == active_target:
                success = True
        else:
            if abs(x - active_target.x) <= active_target.radius:
                success = True

        if success:
            end_time = time.time()
            movement_time = end_time - self.start_time
            
            # Log metrics safely
            self.collected_data.append({
                'Block': self.current_block,
                'CursorType': self.cursor_type,
                'Amplitude': A,
                'Width': W,
                'EffectiveWidth': EW,
                'MovementTime': round(movement_time, 4),
                'Errors': self.trial_errors
            })
            
            self.click_count_in_set += 1
            
            # Change condition parameters after 5 consecutive successful selections
            if self.click_count_in_set >= 5:
                self.click_count_in_set = 0
                self.condition_index += 1
                
                if self.condition_index >= len(self.current_block_conditions):
                    self.condition_index = 0
                    self.current_block += 1
                    
                    # End of complete experiment sequence check
                    if self.current_block > self.total_blocks:
                        self._save_data_to_csv()
                        self._return_to_menu()
                        return
                    
                    random.shuffle(self.current_block_conditions)
                
                self._load_current_condition()
            else:
                # Alternate the active green goal selection target between left/right
                self.left_target.is_active = not self.left_target.is_active
                self.right_target.is_active = not self.right_target.is_active
                self.trial_errors = 0
                self.start_time = time.time()
        else:
            self.trial_errors += 1

    def on_key_press(self, symbol, modifiers):
        if symbol == key.ESCAPE:
            self._save_data_to_csv()
            self._return_to_menu()
            return True

    def _save_data_to_csv(self):
        if not self.collected_data:
            return
            
        filename = f"experiment1_{self.cursor_type.lower().replace(' ', '_')}_data.csv"
        file_exists = os.path.isfile(filename)
        fields = ['Block', 'CursorType', 'Amplitude', 'Width', 'EffectiveWidth', 'MovementTime', 'Errors']
        
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
        
        # Horizontal path reference track line layout
        pyglet.shapes.Line(0, self.cy, self.window.width, self.cy, thickness=1, color=(40, 40, 40, 255)).draw()
        
        for target in self.targets:
            target.draw()
            
        self.cursor.draw()
        self.label.draw()