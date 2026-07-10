from abc import ABC, abstractmethod
import pyglet

class BaseCursor(ABC):
    def __init__(self):
        self.x = 0
        self.y = 0
        self.captured_target = None
        
        # Plain white crosshair setup
        self.size = 6
        self.hline = pyglet.shapes.Line(0, 0, 0, 0, thickness=2, color=(255, 255, 255, 255))
        self.vline = pyglet.shapes.Line(0, 0, 0, 0, thickness=2, color=(255, 255, 255, 255))

    def update_position(self, x, y):
        self.x = x
        self.y = y

    def update_crosshair(self):
        """Aligns the white crosshair lines with the cursor's current x, y coordinates."""
        self.hline.x = self.x - self.size
        self.hline.y = self.y
        self.hline.x2 = self.x + self.size
        self.hline.y2 = self.y
        
        self.vline.x = self.x
        self.vline.y = self.y - self.size
        self.vline.x2 = self.x
        self.vline.y2 = self.y + self.size

    def draw_crosshair(self):
        """Renders the white crosshair lines."""
        self.hline.draw()
        self.vline.draw()

    @abstractmethod
    def update(self, targets):
        """Updates the cursor state and identifies the captured target."""
        pass

    @abstractmethod
    def draw(self):
        pass