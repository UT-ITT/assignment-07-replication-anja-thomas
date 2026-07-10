import pyglet
from pyglet.window import key

from scenes.scene import Scene


class MenuScene(Scene):

    def __init__(self, window, manager):
        self.window = window
        self.manager = manager

        self.cursor_index = 1      # Default Bubble Cursor
        self.mode_index = 0        # Default Demo

        self.cursor_options = [
            "Point Cursor",
            "Bubble Cursor",
            "Object Pointing"
        ]

        self.mode_options = [
            "Demo",
            "Experiment 1",
            "Experiment 2"
        ]

        self.title = pyglet.text.Label(
            "Bubble Cursor (CHI 2005)",
            font_size=28,
            x=window.width // 2,
            y=window.height - 80,
            anchor_x="center"
        )

    def draw(self):

        self.window.clear()

        self.title.draw()

        y = self.window.height - 180

        cursor_label = pyglet.text.Label(
            "Cursor",
            x=100,
            y=y,
            font_size=18
        )
        cursor_label.draw()

        y -= 40

        for i, option in enumerate(self.cursor_options):

            prefix = "> " if i == self.cursor_index else "  "

            pyglet.text.Label(
                prefix + option,
                x=120,
                y=y,
                font_size=16
            ).draw()

            y -= 30

        y -= 40

        mode_label = pyglet.text.Label(
            "Mode",
            x=100,
            y=y,
            font_size=18
        )
        mode_label.draw()

        y -= 40

        for i, option in enumerate(self.mode_options):

            prefix = "> " if i == self.mode_index else "  "

            pyglet.text.Label(
                prefix + option,
                x=120,
                y=y,
                font_size=16
            ).draw()

            y -= 30

        pyglet.text.Label(
            "Arrow Keys = Navigate",
            x=100,
            y=80
        ).draw()

        pyglet.text.Label(
            "ENTER = Start",
            x=100,
            y=50
        ).draw()

    def on_key_press(self, symbol, modifiers):

        if symbol == key.UP:

            self.mode_index = (self.mode_index - 1) % len(self.mode_options)

        elif symbol == key.DOWN:

            self.mode_index = (self.mode_index + 1) % len(self.mode_options)

        elif symbol == key.LEFT:

            self.cursor_index = (self.cursor_index - 1) % len(self.cursor_options)

        elif symbol == key.RIGHT:

            self.cursor_index = (self.cursor_index + 1) % len(self.cursor_options)

        elif symbol == key.ENTER:
            selected_mode = self.mode_options[self.mode_index]
            selected_cursor = self.cursor_options[self.cursor_index]

            if selected_mode == "Demo":
                # Import dynamically to avoid top-level circular dependencies
                from scenes.demo_scene import DemoScene 
                
                demo = DemoScene(self.window, self.manager, selected_cursor)
                self.manager.change_scene(demo) 
                
            elif selected_mode == "Experiment 1":
                # Dynamically import and transition to Experiment 1
                from scenes.experiment1_scene import Experiment1Scene
                
                experiment1 = Experiment1Scene(self.window, self.manager, selected_cursor)
                self.manager.change_scene(experiment1)              
                
            elif selected_mode == "Experiment 2":
                from scenes.experiment2_scene import Experiment2Scene
                
                experiment2 = Experiment2Scene(self.window, self.manager, selected_cursor)
                self.manager.change_scene(experiment2) 