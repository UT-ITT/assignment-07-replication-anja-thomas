import pyglet

import config
from widgets import Button

MODES = [
    ("demo", "Demo", "Free exploration in a simple scene"),
    ("exp1", "Experiment 1 (1D)", "Reciprocal pointing task"),
    ("exp2", "Experiment 2 (2D)", "Multi-target task, varying density"),
]

CURSORS = [
    ("point", "Point Cursor"),
    ("bubble", "Bubble Cursor"),
    ("object", "Object Pointing"),
]


class MenuMode:
    show_os_cursor = True

    def __init__(self, app, selected_mode="demo", selected_cursor="bubble"):
        self.app = app
        self.batch = pyglet.graphics.Batch()
        self.selected_mode = selected_mode
        self.selected_cursor = selected_cursor
        self.mode_buttons = {}
        self.cursor_buttons = {}
        self._all_buttons = []
        self._build_ui()

    def _build_ui(self):
        W, H = config.WINDOW_WIDTH, config.WINDOW_HEIGHT
        self._labels = []

        title = pyglet.text.Label(
            "The Bubble Cursor", x=W / 2, y=H - 70, anchor_x="center",
            font_size=34, weight='bold', color=config.COLOR_TEXT, batch=self.batch)
        subtitle = pyglet.text.Label(
            "A pyglet replica of Grossman & Balakrishnan, CHI 2005 -- pick a mode and a cursor",
            x=W / 2, y=H - 108, anchor_x="center", font_size=14,
            color=config.COLOR_SUBTEXT, batch=self.batch)
        self._labels += [title, subtitle]

        col_mode_x = W * 0.30
        col_cursor_x = W * 0.72
        header_y = H - 175

        mode_header = pyglet.text.Label(
            "Mode", x=col_mode_x, y=header_y, anchor_x="center", font_size=20,
            weight='bold', color=config.COLOR_TEXT, batch=self.batch)
        cursor_header = pyglet.text.Label(
            "Cursor", x=col_cursor_x, y=header_y, anchor_x="center", font_size=20,
            weight='bold', color=config.COLOR_TEXT, batch=self.batch)
        self._labels += [mode_header, cursor_header]

        btn_w, btn_h, gap = 320, 64, 20
        y = header_y - 55
        for key, text, desc in MODES:
            b = Button(col_mode_x - btn_w / 2, y - btn_h, btn_w, btn_h, text, self.batch,
                       font_size=17)
            self.mode_buttons[key] = b
            self._all_buttons.append(b)
            desc_label = pyglet.text.Label(
                desc, x=col_mode_x, y=y - btn_h - 18, anchor_x="center", font_size=11,
                color=config.COLOR_SUBTEXT, batch=self.batch)
            self._labels.append(desc_label)
            y -= (btn_h + gap + 20)

        y = header_y - 55
        for key, text in CURSORS:
            b = Button(col_cursor_x - btn_w / 2, y - btn_h, btn_w, btn_h, text, self.batch,
                       font_size=17)
            self.cursor_buttons[key] = b
            self._all_buttons.append(b)
            y -= (btn_h + gap)

        self.start_button = Button(
            W / 2 - 120, 70, 240, 68, "Start", self.batch,
            base_color=(60, 175, 100), hover_color=(50, 158, 90),
            text_color=(255, 255, 255), font_size=22, weight='bold')
        self._all_buttons.append(self.start_button)

        self.hint_label = pyglet.text.Label(
            "Esc returns to this menu from any mode",
            x=W / 2, y=30, anchor_x="center", font_size=12,
            color=config.COLOR_SUBTEXT, batch=self.batch)

        self._refresh_selection()

    def _refresh_selection(self):
        for k, b in self.mode_buttons.items():
            b.set_selected(k == self.selected_mode)
        for k, b in self.cursor_buttons.items():
            b.set_selected(k == self.selected_cursor)

    def on_mouse_motion(self, x, y, dx, dy):
        for b in self._all_buttons:
            if not b.selected:
                b.set_hover(b.hit(x, y))

    def on_mouse_press(self, x, y, button, modifiers):
        for k, b in self.mode_buttons.items():
            if b.hit(x, y):
                self.selected_mode = k
                self._refresh_selection()
                return
        for k, b in self.cursor_buttons.items():
            if b.hit(x, y):
                self.selected_cursor = k
                self._refresh_selection()
                return
        if self.start_button.hit(x, y):
            self.app.start_mode(self.selected_mode, self.selected_cursor)

    def on_key_press(self, symbol, modifiers):
        pass

    def update(self, dt):
        pass

    def draw(self):
        self.batch.draw()
