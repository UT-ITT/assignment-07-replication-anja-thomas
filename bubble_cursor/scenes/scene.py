from abc import ABC, abstractmethod


class Scene(ABC):

    def on_enter(self):
        pass

    def on_exit(self):
        pass

    def update(self, dt):
        pass

    @abstractmethod
    def draw(self):
        pass

    def on_mouse_motion(self, x, y, dx, dy):
        pass

    def on_mouse_press(self, x, y, button, modifiers):
        pass

    def on_key_press(self, symbol, modifiers):
        pass