import pyglet
from pyglet.window import key
import random

from scenes.scene import Scene
from objects.target import Target
from cursors.point_cursor import PointCursor
from cursors.bubble_cursor import BubbleCursor

class DemoScene(Scene):
    def __init__(self, window, manager, cursor_type):
        self.window = window
        self.manager = manager
        
        # Generate random targets
        self.targets = []
        for _ in range(30):
            x = random.randint(50, self.window.width - 50)
            y = random.randint(50, self.window.height - 50)
            radius = random.randint(10, 30)
            self.targets.append(Target(x, y, radius))

        # Set the active cursor based on menu selection
        if cursor_type == "Point Cursor":
            self.cursor = PointCursor()
        elif cursor_type == "Bubble Cursor":
            self.cursor = BubbleCursor()
        elif cursor_type == "Object Pointing":
            self.cursor = PointCursor() # Placeholder for now

        # UI Label - Added text instructions for the toggle feature
        self.label = pyglet.text.Label(
            f'Mode: {cursor_type} Demo | Press V: Toggle Voronoi | Press ESC: Menu',
            font_name='Arial',
            font_size=12,
            x=10, y=self.window.height - 25,
            color=(255, 255, 255, 255)
        )

        # --- VORONOI DIAGRAM GENERATION (Calculated once at startup) ---
        self.show_voronoi = False
        self.voronoi_batch = pyglet.graphics.Batch()
        self.voronoi_lines = [] # Kept alive in memory to prevent garbage collection
        self._generate_voronoi_diagram()

    def _generate_voronoi_diagram(self):
        """Scans the screen area using a grid to compute and map precise cell boundaries."""
        STEP = 6  # Spacing in pixels. Lower is sharper but slower; 6 is an ideal sweet spot.
        width = self.window.width
        height = self.window.height
        
        grid = {}
        
        # Step 1: Find the closest target index for every coordinate intersection
        for y in range(0, height, STEP):
            for x in range(0, width, STEP):
                closest_idx = -1
                min_dist = float('inf')
                
                for idx, target in enumerate(self.targets):
                    # Uses the paper's exact Intersecting Distance calculation
                    dist = target.get_intersecting_distance(x, y)
                    if dist < min_dist:
                        min_dist = dist
                        closest_idx = idx
                        
                grid[(x, y)] = closest_idx

        # Step 2: Detect where cell IDs switch between neighbors and draw a line segment
        for y in range(0, height, STEP):
            for x in range(0, width, STEP):
                current_idx = grid[(x, y)]
                
                # Check right neighbor boundary
                if x + STEP < width:
                    if grid[(x + STEP, y)] != current_idx:
                        boundary_x = x + STEP // 2
                        line = pyglet.shapes.Line(
                            boundary_x, y, boundary_x, y + STEP, 
                            thickness=1, 
                            color=(130, 170, 200, 80),  # Subtle semi-transparent muted blue
                            batch=self.voronoi_batch
                        )
                        self.voronoi_lines.append(line)
                        
                # Check upper neighbor boundary
                if y + STEP < height:
                    if grid[(x, y + STEP)] != current_idx:
                        boundary_y = y + STEP // 2
                        line = pyglet.shapes.Line(
                            x, boundary_y, x + STEP, boundary_y, 
                            thickness=1, 
                            color=(130, 170, 200, 80),
                            batch=self.voronoi_batch
                        )
                        self.voronoi_lines.append(line)

    def on_enter(self):
        self.window.set_mouse_visible(False)

    def on_exit(self):
        self.window.set_mouse_visible(True)

    def on_mouse_motion(self, x, y, dx, dy):
        self.cursor.update_position(x, y)
        self.cursor.update(self.targets)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.on_mouse_motion(x, y, dx, dy)

    def on_key_press(self, symbol, modifiers):
        if symbol == key.V:
            self.show_voronoi = not self.show_voronoi
            return True
        elif symbol == key.ESCAPE:
            from scenes.menu_scene import MenuScene
            self.manager.change_scene(MenuScene(self.window, self.manager))
            return True 

    def update(self, dt):
        pass

    def draw(self):
        self.window.clear()
        
        # Enable blending for alpha-transparent lines and circles
        pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
        pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
        
        # Draw the Voronoi mesh in the background if toggled on
        if self.show_voronoi:
            self.voronoi_batch.draw()
            
        # Draw targets
        for target in self.targets:
            target.draw()
            
        # Draw interactive elements over the top
        self.cursor.draw()
        self.label.draw()