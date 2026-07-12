import pyglet


class Button:
    """A simple rectangular clickable button drawn with pyglet.shapes,
    sharing a Batch with everything else for a single draw call."""

    def __init__(self, x, y, w, h, text, batch,
                 base_color=(232, 232, 236),
                 hover_color=(212, 218, 235),
                 selected_color=(90, 140, 240),
                 text_color=(30, 30, 35),
                 selected_text_color=(255, 255, 255),
                 font_size=16, weight='normal'):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.base_color = base_color
        self.hover_color = hover_color
        self.selected_color = selected_color
        self.text_color = text_color
        self.selected_text_color = selected_text_color
        self.selected = False

        self.rect = pyglet.shapes.BorderedRectangle(
            x, y, w, h, border=2, color=base_color,
            border_color=(195, 195, 200), batch=batch)
        self.label = pyglet.text.Label(
            text, x=x + w / 2, y=y + h / 2,
            anchor_x="center", anchor_y="center",
            color=(*text_color, 255), font_size=font_size, weight=weight,
            batch=batch)

    def hit(self, mx, my):
        return self.x <= mx <= self.x + self.w and self.y <= my <= self.y + self.h

    def set_hover(self, hovering):
        if self.selected:
            self.rect.color = self.selected_color
            self.label.color = (*self.selected_text_color, 255)
        elif hovering:
            self.rect.color = self.hover_color
            self.label.color = (*self.text_color, 255)
        else:
            self.rect.color = self.base_color
            self.label.color = (*self.text_color, 255)

    def set_selected(self, sel):
        self.selected = sel
        self.set_hover(False)

    def set_text(self, text):
        self.label.text = text
