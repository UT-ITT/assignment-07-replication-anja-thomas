from cursors.base_cursor import BaseCursor
import pyglet

class BubbleCursor(BaseCursor):
    def __init__(self):
        # Call the base constructor with no arguments
        super().__init__()
        
        # Override the crosshair size directly if you want it slightly smaller
        self.size = 5 
        self.radius = 5
        
        # 1. The main cursor bubble (follows the mouse)
        self.bubble = pyglet.shapes.Circle(
            x=self.x, y=self.y, radius=self.radius, color=(200, 235, 255, 140)
        )
        
        # 2. The secondary morphing bubble (snaps to targets when crowded)
        self.target_bubble = pyglet.shapes.Circle(
            x=0, y=0, radius=0, color=(200, 235, 255, 90)
        )
        self.show_target_bubble = False

    def update(self, targets):
        if not targets:
            return

        sorted_targets = sorted(
            targets, 
            key=lambda t: t.get_intersecting_distance(self.x, self.y)
        )

        closest_target = sorted_targets[0]
        
        if len(sorted_targets) > 1:
            second_closest_target = sorted_targets[1]
            cond_closest = closest_target.get_containment_distance(self.x, self.y)
            intd_second = second_closest_target.get_intersecting_distance(self.x, self.y)
            
            self.radius = min(cond_closest, intd_second)
            
            # --- THE PAPER'S VISUAL MORPHING LOGIC ---
            if self.radius < cond_closest:
                self.show_target_bubble = True
                self.target_bubble.x = closest_target.x
                self.target_bubble.y = closest_target.y
                self.target_bubble.radius = closest_target.radius + 4 
            else:
                self.show_target_bubble = False
        else:
            self.radius = closest_target.get_containment_distance(self.x, self.y)
            self.show_target_bubble = False

        # State updates
        for t in targets:
            t.is_captured = False
            
        self.captured_target = closest_target
        self.captured_target.is_captured = True

        # Sync main cursor bubble position
        self.bubble.x = self.x
        self.bubble.y = self.y
        self.bubble.radius = self.radius
        
        self.update_crosshair()

    def draw(self):
        pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
        pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
        
        # Draw the main cursor bubble
        self.bubble.draw()
        
        # Draw the secondary morphing bubble if the paper's proximity rule is met
        if self.show_target_bubble:
            self.target_bubble.draw()
            
        self.draw_crosshair()