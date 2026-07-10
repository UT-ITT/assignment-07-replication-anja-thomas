from cursors.base_cursor import BaseCursor

class PointCursor(BaseCursor):
    def __init__(self):
        super().__init__()

    def update(self, targets):
        self.captured_target = None
        for target in targets:
            target.is_captured = False
            if target.distance_to(self.x, self.y) <= target.radius:
                self.captured_target = target
                target.is_captured = True
                
        self.update_crosshair()

    def draw(self):
        self.draw_crosshair()