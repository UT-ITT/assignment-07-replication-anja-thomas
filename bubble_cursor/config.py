"""
Shared configuration / constants.

Note on units: the original paper measures amplitude/width in abstract
"units" where 1 unit = 0.2cm on their 20" 1600x1200 display. We don't know
the physical size of whoever runs this, so we just treat 1 "unit" as
UNIT_PX pixels, scaled so the largest amplitudes used in Experiment 1/2
comfortably fit inside the window.
"""

WINDOW_WIDTH = 1500
WINDOW_HEIGHT = 950
FPS = 120

UNIT_PX = 0.75  # 1 paper "unit" -> pixels

BG_COLOR = (245, 245, 248, 255)

COLOR_GOAL = (46, 160, 67)          # green - active/goal target
COLOR_INACTIVE_GOAL = (140, 140, 145)  # grey - the "other" target in exp1
COLOR_DISTRACTOR_OUTLINE = (140, 140, 148)
COLOR_CAPTURED_EXP1 = (60, 110, 220)   # blue highlight (exp 1 style)
COLOR_CAPTURED_EXP2 = (210, 60, 55)    # red highlight (exp 2 style)
COLOR_BUBBLE_FILL = (90, 140, 240)          # exp1-style semitransparent blue bubble
COLOR_BUBBLE_FILL_EXP2 = (150, 150, 158)    # exp2 uses a more subtle semitransparent grey
COLOR_BUBBLE_OPACITY = 70
COLOR_OBJECT_CROSS = (200, 60, 60)
COLOR_POINT_CROSS = (20, 20, 25)
COLOR_TEXT = (30, 30, 35, 255)
COLOR_SUBTEXT = (95, 95, 100, 255)
COLOR_START_CIRCLE = (210, 60, 55)
COLOR_VORONOI = (0, 0, 0)

# Number of blocks of trials. The paper used 9 (exp1) / 4 (exp2) blocks for
# statistically robust, publishable data. For a hands-on personal replica
# that default is a long grind, so we default lower but you can raise it.
EXP1_BLOCKS = 3          # paper: 9
EXP2_BLOCKS = 2          # paper: 4

EXP1_SELECTIONS_PER_SET = 5     # paper: 5 clicks (4 reciprocal movements)
EXP2_TARGETS_PER_SET = 9        # paper: 9 targets per trial set

EXP1_AMPLITUDES = [192, 384, 768]
EXP1_WIDTHS = [8, 16, 24]
EXP1_EFFECTIVE_WIDTHS = [32, 64, 96]

EXP2_AMPLITUDES = [256, 512, 768]
EXP2_WIDTHS = [8, 16, 24]
EXP2_EW_RATIOS = [1.33, 2, 3]
EXP2_DENSITIES = [0, 0.5, 1]

RESULTS_DIR = "results"
