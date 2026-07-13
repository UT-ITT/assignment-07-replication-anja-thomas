import pyglet

from modes.menu_mode import MenuMode
from modes.demo_mode import DemoMode
from modes.experiment1_mode import Experiment1Mode
from modes.experiment2_mode import Experiment2Mode


MODE_CLASSES = {
    "demo": DemoMode,
    "exp1": Experiment1Mode,
    "exp2": Experiment2Mode,
}


class App:
    def __init__(self, window):
        self.window = window
        self.mode = MenuMode(self)
        self._last_selection = ("demo", "bubble")
        self.window.set_mouse_visible(True)

    def start_mode(self, mode_key, cursor_key):
        self._last_selection = (mode_key, cursor_key)
        self.mode = MODE_CLASSES[mode_key](self, cursor_key)
        self.window.set_mouse_visible(getattr(self.mode, "show_os_cursor", False))

    def return_to_menu(self):
        mode_key, cursor_key = self._last_selection
        self.mode = MenuMode(self, selected_mode=mode_key, selected_cursor=cursor_key)
        self.window.set_mouse_visible(True)

    def on_mouse_motion(self, x, y, dx, dy):
        self.mode.on_mouse_motion(x, y, dx, dy)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.mode.on_mouse_motion(x, y, dx, dy)

    def on_mouse_press(self, x, y, button, modifiers):
        self.mode.on_mouse_press(x, y, button, modifiers)

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.Q:
            if not isinstance(self.mode, MenuMode):
                self.return_to_menu()
                return
        if hasattr(self.mode, "on_key_press"):
            self.mode.on_key_press(symbol, modifiers)

    def update(self, dt):
        self.mode.update(dt)

    def draw(self):
        self.window.clear()
        self.mode.draw()
