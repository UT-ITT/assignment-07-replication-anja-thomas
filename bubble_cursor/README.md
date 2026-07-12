# The Bubble Cursor -- pyglet replica

A hands-on pyglet replica of:

> Grossman, T. and Balakrishnan, R. (2005). **The Bubble Cursor: Enhancing
> Target Acquisition by Dynamic Resizing of the Cursor's Activation Area.**
> ACM CHI 2005, pp. 281-290.

From a menu you pick a **Mode** and a **Cursor**, then hit Start:

- **Modes:** Demo (free exploration) / Experiment 1 (1D reciprocal pointing)
  / Experiment 2 (2D task with varying density)
- **Cursors:** Point / Bubble / Object Pointing

Press **Esc** at any time to return to the menu.

## Running it

```bash
pip install -r requirements.txt
python main.py
```

## Project layout

```
config.py                 tunable constants (window size, colors, trial counts...)
geometry.py                small vector-math helpers
targets.py                  Target: a circular selectable object
cursors.py                  PointCursor, BubbleCursor, ObjectPointingCursor
widgets.py                   Button widget used by the menu
results_logger.py           tiny CSV writer used by the experiment modes
app.py                        owns the current mode, routes window events to it
main.py                        entry point / pyglet window setup
modes/
    menu_mode.py             mode + cursor picker
    demo_mode.py              Figure-1-style free exploration scene
    experiment1_mode.py     1D reciprocal pointing task (paper's Experiment 1)
    experiment2_mode.py    2D task with density manipulation (paper's Experiment 2)
test_cursors.py                 pure unit tests for the three cursor algorithms
```

## The cursor algorithms

- **Point cursor**: single-pixel hotspot, standard behavior.
- **Bubble cursor**: implements the paper's algorithm exactly --
  for targets `T1..Tn`, `IntD_i` = distance to the *nearest* point on
  `Ti`'s border, `ConD_i` = distance to the *farthest* point. With `i`
  = closest target by `IntD` and `j` = second-closest:
  `radius = min(ConD_i, IntD_j)` (with a small buffer so it doesn't
  touch the second-closest target, as the paper also does). This
  guarantees exactly one target is captured at any time. When that gap
  means the bubble only *intersects* the captured target instead of fully
  containing it, a second "morph" bubble quickly expands from the
  intersection to envelop the target (Figure 4b in the paper) as a
  reinforcing visual cue -- see `BubbleCursor.morph_target` /
  `.morph_radius` in `cursors.py`. See `test_cursors.py` for worked
  examples, including the degenerate exact-tie boundary case and the
  morph activation/deactivation behavior.
- **Object Pointing**: an approximation of Guiard et al.'s technique as
  summarized in the paper's "Object Pointing" section (a safety zone
  around the current target, a velocity threshold, and a widening
  angular search for a jump target). The original paper only describes
  this at a high level and doesn't publish its exact parameters, so this
  is functionally similar rather than a byte-exact reproduction. Three
  things matter for it to feel right and were bugs in an earlier version:
  - The safety-zone radius and velocity threshold are defined in the
    paper's abstract "units" and must be scaled by the same `UNIT_PX`
    the rest of the app uses for target sizes -- they used to be scaled
    by a different, hardcoded factor, making the safety zone wildly
    mismatched relative to target spacing.
  - The angular jump-search now uses the cursor's actual *velocity
    direction*, not the static offset from the last captured target, to
    decide which way to search -- matching "it analyzes its current
    direction, velocity, and acceleration" in the paper.
  - The velocity estimate is low-pass filtered, and the very first sample
    after a target/scene change is discarded, so a stale anchor position
    (or single noisy frame) can't fire a spurious jump.

## Honest notes on where this diverges from the paper

This is a personal-scale replica, not a research instrument, so a few
liberties were taken -- all called out in code comments too:

- **Units.** The paper's "units" (1 unit = 0.2cm on their 20" 1600x1200
  display) are just treated as `UNIT_PX` pixels here (`config.py`),
  scaled so the largest amplitudes fit in a normal window.
- **Effective-width control.** The paper controls each target's
  *effective width* (EW) using an additional placement technique that's
  only referenced, not described (ref. [7], "published elsewhere"). This
  replica instead places same-radius framing distracters at a
  center-to-center distance of `EW` from the goal -- along the movement
  axis in Experiment 1, and both along and perpendicular to it (matching
  the paper's own description) in Experiment 2. For same-size circles the
  bubble cursor's Voronoi-style boundary sits exactly halfway between
  neighbors, so this reproduces the intended controlled effective width.
- **Session length.** The paper ran 9 blocks (Exp 1) / 4 blocks (Exp 2) per
  participant for statistically robust, publishable data -- a long grind
  for one person exploring the techniques. Defaults here are lower
  (`EXP1_BLOCKS = 3`, `EXP2_BLOCKS = 2` in `config.py`) but easy to raise
  back up.
- **Object Pointing in Experiment 1.** The original study only compared
  Point vs. Bubble cursors in Experiment 1 (Object Pointing was added in
  Experiment 2). This replica lets you pick any of the three cursors in
  either experiment, for consistency and so you can compare all three
  head-to-head in the simpler 1D task too.
- **Movement-time measurement.** The paper's headline "movement time" is
  the time to make a *successful* selection (mis-clicks don't reset the
  timer, matching their described method); that's what's logged here too,
  alongside a per-selection error count.

## Results

Each completed Experiment run writes a timestamped CSV to `results/`
(one row per successful selection) with the condition (amplitude, width,
effective width / density, etc.) and movement time, so you can plot your
own Fitts'-law regressions if you want to check the `MT = a + b*log2(A/W+1)`
relationship the paper reports.

## Tests

```bash
python test_cursors.py
```

Pure, pyglet-free unit tests that check the Bubble cursor's radius math
against hand-computed expectations, the Point cursor's containment check,
and the Object Pointing cursor's safety-zone / jump / snap-back behavior.
