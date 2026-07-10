import pyglet
import math

class Target:
    def __init__(self, x, y, radius, color=(200, 200, 200, 255)):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.is_captured = False
        
        # Pyglet shape for rendering
        self.shape = pyglet.shapes.Circle(
            x=self.x, y=self.y, radius=self.radius, color=self.color
        )

    def distance_to(self, cx, cy):
        """Calculates the Euclidean distance from a point to the target's center."""
        return math.sqrt((self.x - cx)**2 + (self.y - cy)**2)

    def get_intersecting_distance(self, cx, cy):
        """Length of the shortest line connecting cursor center to target border."""
        return max(0, self.distance_to(cx, cy) - self.radius)

    def get_containment_distance(self, cx, cy):
        """Length of the longest line connecting cursor center to target border."""
        return self.distance_to(cx, cy) + self.radius

    def draw(self):
        if self.is_captured:
            self.shape.color = (0, 255, 0, 255) # Green when captured
        else:
            self.shape.color = self.color
        self.shape.draw()