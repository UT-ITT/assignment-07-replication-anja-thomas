class SceneManager:

    def __init__(self):
        self.current_scene = None

    def change_scene(self, scene):

        if self.current_scene:
            self.current_scene.on_exit()

        self.current_scene = scene
        self.current_scene.on_enter()

    def update(self, dt):

        if self.current_scene:
            self.current_scene.update(dt)

    def draw(self):

        if self.current_scene:
            self.current_scene.draw()

    def on_mouse_motion(self, *args):
        if self.current_scene:
            self.current_scene.on_mouse_motion(*args)

    def on_mouse_press(self, *args):
        if self.current_scene:
            self.current_scene.on_mouse_press(*args)

    def on_key_press(self, *args):
        if self.current_scene:
            self.current_scene.on_key_press(*args)