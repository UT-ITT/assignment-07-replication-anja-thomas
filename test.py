import pyglet
from pyglet import shapes
from pyglet.window import key, mouse
import math
import random

WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768

class Target:
    def __init__(self, x, y, radius, color, is_active=False, is_outline=False):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.is_active = is_active
        self.is_outline = is_outline
        
        if self.is_outline:
            # Distracter targets are grey outlined circles
            self.shape = shapes.Arc(x, y, radius, color=color, batch=batch)
        else:
            self.shape = shapes.Circle(x, y, radius, color=color, batch=batch)

    def int_d(self, cx, cy):
        """Intersecting Distance: Shortest line to target border."""
        dist = math.hypot(self.x - cx, self.y - cy)
        return max(0, dist - self.radius)

    def con_d(self, cx, cy):
        """Containment Distance: Longest line to target border."""
        dist = math.hypot(self.x - cx, self.y - cy)
        return dist + self.radius

class BubbleCursorApp(pyglet.window.Window):
    def __init__(self):
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, "Bubble Cursor Replication")
        self.set_mouse_visible(False)
        
        self.state = "MENU"
        self.selected_cursor = "BUBBLE"  # Options: POINT, BUBBLE, OBJECT
        self.targets = []
        
        # Cursor Visuals
        self.cursor_x = WINDOW_WIDTH // 2
        self.cursor_y = WINDOW_HEIGHT // 2
        # Bubble cursor rendered as semi-transparent[cite: 1]
        self.bubble_shape = shapes.Circle(self.cursor_x, self.cursor_y, 5, color=(100, 100, 255, 128))
        self.crosshair_h = shapes.Line(0, 0, 0, 0, color=(0, 0, 0))
        self.crosshair_v = shapes.Line(0, 0, 0, 0, color=(0, 0, 0))
        
        # Menu Labels
        self.labels = [
            pyglet.text.Label("Select Cursor: [1] Point  [2] Bubble  [3] Object", x=50, y=600),
            pyglet.text.Label("Select Mode:", x=50, y=500),
            pyglet.text.Label("[D] Demo Mode", x=100, y=450),
            pyglet.text.Label("[E] Experiment 1 (1D Reciprocal)", x=100, y=400),
            pyglet.text.Label("[R] Experiment 2 (2D Acquisition)", x=100, y=350),
            pyglet.text.Label("Press ESC to return to menu at any time", x=50, y=100)
        ]

    def setup_demo(self):
        self.targets.clear()
        self.state = "DEMO"
        # Generate random targets for simple showcase
        for _ in range(15):
            x = random.randint(100, WINDOW_WIDTH - 100)
            y = random.randint(100, WINDOW_HEIGHT - 100)
            self.targets.append(Target(x, y, 20, color=(150, 150, 150), is_outline=True))
        # Add one active target
        self.targets.append(Target(WINDOW_WIDTH//2, WINDOW_HEIGHT//2, 20, color=(0, 255, 0), is_active=True))

    def setup_exp1(self):
        self.targets.clear()
        self.state = "EXP1"
        # Reciprocal 1D pointing task along horizontal axis[cite: 1]
        self.targets.append(Target(200, WINDOW_HEIGHT//2, 16, color=(0, 255, 0), is_active=True))
        self.targets.append(Target(800, WINDOW_HEIGHT//2, 16, color=(150, 150, 150), is_active=False))
        # Add distracter targets to control effective width[cite: 1]
        self.targets.append(Target(500, WINDOW_HEIGHT//2, 16, color=(150, 150, 150), is_outline=True))
        
    def setup_exp2(self):
        self.targets.clear()
        self.state = "EXP2"
        # Start target in the center[cite: 1]
        self.targets.append(Target(WINDOW_WIDTH//2, WINDOW_HEIGHT//2, 16, color=(0, 255, 0), is_active=True))
        # Add 2D distracter targets (simplified layout)
        for _ in range(30):
            x = random.randint(50, WINDOW_WIDTH - 50)
            y = random.randint(50, WINDOW_HEIGHT - 50)
            self.targets.append(Target(x, y, 16, color=(150, 150, 150), is_outline=True))

    def on_key_press(self, symbol, modifiers):
        if self.state == "MENU":
            if symbol == key._1: self.selected_cursor = "POINT"
            elif symbol == key._2: self.selected_cursor = "BUBBLE"
            elif symbol == key._3: self.selected_cursor = "OBJECT"
            elif symbol == key.D: self.setup_demo()
            elif symbol == key.E: self.setup_exp1()
            elif symbol == key.R: self.setup_exp2()
        elif symbol == key.ESCAPE:
            self.state = "MENU"
            self.targets.clear()
            return pyglet.event.EVENT_HANDLED

    def on_mouse_motion(self, x, y, dx, dy):
        self.cursor_x = x
        self.cursor_y = y

    def on_mouse_press(self, x, y, button, modifiers):
        if self.state != "MENU":
            # Logic for capturing target based on current cursor
            captured_target = self.get_captured_target()
            if captured_target and captured_target.is_active:
                self.handle_successful_click()

    def get_captured_target(self):
        if not self.targets:
            return None
            
        if self.selected_cursor == "POINT":
            for t in self.targets:
                if math.hypot(t.x - self.cursor_x, t.y - self.cursor_y) <= t.radius:
                    return t
            return None
            
        elif self.selected_cursor == "BUBBLE":
            # Target closest to center is captured[cite: 1]
            distances = [(math.hypot(t.x - self.cursor_x, t.y - self.cursor_y), t) for t in self.targets]
            distances.sort(key=lambda item: item[0])
            return distances[0][1] if distances else None
            
        elif self.selected_cursor == "OBJECT":
            # Simplified Object Pointing: Jumps to nearest target boundary (velocity logic omitted for brevity)
            distances = [(math.hypot(t.x - self.cursor_x, t.y - self.cursor_y), t) for t in self.targets]
            distances.sort(key=lambda item: item[0])
            return distances[0][1] if distances else None

    def handle_successful_click(self):
        if self.state == "EXP1":
            # Swap colors for reciprocal pointing[cite: 1]
            for t in self.targets:
                if t.is_active:
                    t.is_active = False
                    t.shape.color = (150, 150, 150)
                elif not t.is_outline:
                    t.is_active = True
                    t.shape.color = (0, 255, 0)
                    
        elif self.state == "EXP2" or self.state == "DEMO":
            # Redraw scene with new goal[cite: 1]
            if self.state == "DEMO": self.setup_demo()
            if self.state == "EXP2": self.setup_exp2()

    def update_cursor_visuals(self):
        self.crosshair_h.x = self.cursor_x - 5
        self.crosshair_h.y = self.cursor_y
        self.crosshair_h.x2 = self.cursor_x + 5
        self.crosshair_h.y2 = self.cursor_y
        
        self.crosshair_v.x = self.cursor_x
        self.crosshair_v.y = self.cursor_y - 5
        self.crosshair_v.x2 = self.cursor_x
        self.crosshair_v.y2 = self.cursor_y + 5

        if self.selected_cursor == "BUBBLE" and len(self.targets) > 1:
            # Sort targets by intersecting distance
            sorted_targets = sorted(self.targets, key=lambda t: t.int_d(self.cursor_x, self.cursor_y))
            closest = sorted_targets[0]
            second_closest = sorted_targets[1]
            
            # Radius = min(ConD_closest, IntD_second_closest)[cite: 1]
            radius = min(closest.con_d(self.cursor_x, self.cursor_y), 
                         second_closest.int_d(self.cursor_x, self.cursor_y))
            
            self.bubble_shape.x = self.cursor_x
            self.bubble_shape.y = self.cursor_y
            self.bubble_shape.radius = max(5, radius) # Prevent negative/zero radius
            self.bubble_shape.visible = True
        else:
            self.bubble_shape.visible = False

    def on_draw(self):
        self.clear()
        if self.state == "MENU":
            # Update menu label to show current selection
            self.labels[0].text = f"Select Cursor: [1] Point  [2] Bubble  [3] Object   | CURRENT: {self.selected_cursor}"
            for label in self.labels:
                label.draw()
        else:
            batch.draw()
            self.update_cursor_visuals()
            if self.selected_cursor == "BUBBLE":
                self.bubble_shape.draw()
            self.crosshair_h.draw()
            self.crosshair_v.draw()

if __name__ == "__main__":
    batch = pyglet.graphics.Batch()
    app = BubbleCursorApp()
    pyglet.app.run()