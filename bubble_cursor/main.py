"""
The Bubble Cursor -- pyglet replica of:

  Grossman, T. and Balakrishnan, R. (2005). The Bubble Cursor: Enhancing
  Target Acquisition by Dynamic Resizing of the Cursor's Activation Area.
  ACM CHI 2005.

Run with:  python main.py

From the menu, choose a Mode (Demo / Experiment 1 / Experiment 2) and a
Cursor (Point / Bubble / Object Pointing), then click Start.
Press Q at any time to go back to the menu.
"""

import pyglet

import config
from app import App

window = pyglet.window.Window(
    config.WINDOW_WIDTH, config.WINDOW_HEIGHT,
    caption="The Bubble Cursor -- CHI 2005 replica")

pyglet.gl.glClearColor(*(c / 255 for c in config.BG_COLOR))

app = App(window)


@window.event
def on_mouse_motion(x, y, dx, dy):
    app.on_mouse_motion(x, y, dx, dy)


@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    app.on_mouse_drag(x, y, dx, dy, buttons, modifiers)


@window.event
def on_mouse_press(x, y, button, modifiers):
    app.on_mouse_press(x, y, button, modifiers)


@window.event
def on_key_press(symbol, modifiers):
    app.on_key_press(symbol, modifiers)


@window.event
def on_draw():
    app.draw()


def update(dt):
    app.update(dt)


pyglet.clock.schedule_interval(update, 1.0 / config.FPS)
pyglet.app.run()
