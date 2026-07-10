import pyglet
from pyglet.window import key  # Added this import for key detection

from config import *
from scenes.scene_manager import SceneManager
from scenes.menu_scene import MenuScene

class BubbleCursorApp(pyglet.window.Window):

    def __init__(self):
        super().__init__(
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            caption=WINDOW_TITLE
        )

        self.manager = SceneManager()
        menu = MenuScene(self, self.manager)
        self.manager.change_scene(menu)

        pyglet.clock.schedule_interval(
            self.update,
            1 / FPS
        )

    def update(self, dt):
        self.manager.update(dt)

    def on_draw(self):
        self.manager.draw()

    def on_key_press(self, symbol, modifiers):
        # 1. Intercept 'Q' globally right here at the window level!
        if symbol == key.Q:
            print("Q pressed. Exiting application...")
            pyglet.app.exit()
            return True
            
        # 2. If it's not 'Q', pass it along to your scenes like normal
        self.manager.on_key_press(symbol, modifiers)

    def on_mouse_motion(self, x, y, dx, dy):
        self.manager.on_mouse_motion(x, y, dx, dy)

    def on_mouse_press(self, x, y, button, modifiers):
        self.manager.on_mouse_press(x, y, button, modifiers)


if __name__ == "__main__":
    app = BubbleCursorApp()
    pyglet.app.run()