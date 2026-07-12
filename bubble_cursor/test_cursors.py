import math
from targets import Target
from cursors import PointCursor, BubbleCursor, ObjectPointingCursor


def approx(a, b, tol=1e-6):
    assert abs(a - b) <= tol, f"{a} != {b}"


def test_bubble_exact_on_target_fully_contains():
    t1 = Target(100, 100, 10)
    t2 = Target(200, 100, 10)
    c = BubbleCursor()
    c.update(100, 100, 1 / 60, [t1, t2])
    assert c.captured_target is t1
    approx(c.radius, 10.0)          # ConD1 = 0+10 = 10, IntD2 = 90-GAP -> min is 10
    assert c.fully_contains


def test_bubble_between_targets_never_reaches_second_closest():
    t1 = Target(100, 100, 10)
    t2 = Target(200, 100, 10)
    c = BubbleCursor()
    # Slightly closer to t1 than to t2 (145 vs. the exact 150 midpoint) so
    # there's an unambiguous single closest target.
    c.update(145, 100, 1 / 60, [t1, t2])
    d1 = math.hypot(145 - 100, 0)
    int_d1, con_d1 = d1 - 10, d1 + 10
    d2 = math.hypot(200 - 145, 0)
    int_d2 = d2 - 10
    expected_radius = min(con_d1, int_d2 - BubbleCursor.GAP)
    approx(c.radius, expected_radius)
    assert c.radius >= int_d1 - 1e-6   # reaches the closest target's near edge
    assert c.radius < int_d2           # stays clear of the 2nd-closest's near edge
    assert c.captured_target is t1


def test_bubble_exact_tie_still_touches_the_closest_listed_target():
    # A degenerate boundary case: two equal-size targets exactly equidistant
    # from the cursor. IntD_i == IntD_j here, so the "leave a gap" adjustment
    # would (if left unclamped) shrink the bubble below the closest target's
    # own near edge. The implementation clamps radius up to at least
    # closest_int, guaranteeing the bubble always at least touches whichever
    # target sorted first -- this is a one-pixel-wide boundary condition in
    # practice, not something a real mouse position will land on exactly.
    t1 = Target(100, 100, 10)
    t2 = Target(200, 100, 10)
    c = BubbleCursor()
    c.update(150, 100, 1 / 60, [t1, t2])
    approx(c.radius, 40.0)
    assert c.captured_target is t1


def test_bubble_single_target_encloses_it():
    t1 = Target(300, 300, 15)
    c = BubbleCursor()
    c.update(300, 300, 1 / 60, [t1])
    approx(c.radius, 15.0)
    assert c.captured_target is t1
    assert c.fully_contains


def test_bubble_no_targets_falls_back_to_empty_radius():
    c = BubbleCursor()
    c.update(50, 50, 1 / 60, [])
    assert c.captured_target is None
    approx(c.radius, BubbleCursor.EMPTY_SPACE_RADIUS)


def test_bubble_morph_inactive_when_fully_containing():
    t1 = Target(100, 100, 10)
    t2 = Target(400, 100, 10)  # far away, doesn't constrain the bubble
    c = BubbleCursor()
    c.update(100, 100, 1 / 60, [t1, t2])
    assert c.fully_contains
    assert c.morph_target is None
    assert c.morph_radius is None


def test_bubble_morph_activates_when_only_intersecting():
    # t2 is close enough that the gap-adjusted radius can't fully enclose t1.
    t1 = Target(100, 100, 10)
    t2 = Target(115, 100, 5)
    c = BubbleCursor()
    c.update(100, 100, 1 / 60, [t1, t2])
    assert c.captured_target is t1
    assert not c.fully_contains
    assert c.morph_target is t1
    r = c.morph_radius
    assert r is not None
    # Envelope should always be big enough to reach past the target's edge,
    # and should grow towards (radius + MORPH_PAD) as progress advances.
    final_r = t1.radius + BubbleCursor.MORPH_PAD
    assert 0 < r <= final_r + 1e-6

    # Advancing time should grow the envelope towards its final size.
    c.update(100, 100, 1.0, [t1, t2])  # a full second is >> MORPH_DURATION
    approx(c.morph_radius, final_r, tol=1e-3)


def test_bubble_morph_clears_when_target_becomes_fully_contained():
    t1 = Target(100, 100, 10)
    t2 = Target(115, 100, 5)
    c = BubbleCursor()
    c.update(100, 100, 1 / 60, [t1, t2])
    assert c.morph_target is t1
    # Now remove the constraining neighbor -- bubble can fully contain t1 again.
    c.update(100, 100, 1 / 60, [t1])
    assert c.fully_contains
    assert c.morph_target is None
    assert c.morph_radius is None



    t1 = Target(100, 100, 10)
    c = PointCursor()
    c.update(105, 100, 1 / 60, [t1])   # inside (distance 5 < r 10)
    assert c.captured_target is t1
    c.update(150, 100, 1 / 60, [t1])   # outside
    assert c.captured_target is None


def test_object_pointing_tracks_within_safety_zone():
    t1 = Target(200, 200, 20)
    c = ObjectPointingCursor()
    c.reset([t1])
    assert c.current_target is t1
    # small move, well inside safety zone -> tracks mouse directly
    c.update(205, 205, 1 / 60, [t1])
    approx(c.x, 205)
    approx(c.y, 205)
    assert c.captured_target is t1


def test_object_pointing_jumps_to_target_in_direction_when_fast():
    t_start = Target(100, 100, 15)
    t_far = Target(500, 100, 15)  # straight ahead, far outside safety zone
    c = ObjectPointingCursor()
    c.reset([t_start, t_far], start_pos=(100, 100))
    c.set_current_target(t_start, pos=(100, 100))
    # The first update() after a reset intentionally seeds the velocity
    # tracker instead of computing a (potentially bogus) spike, so it takes
    # two calls before a fast, straight rightward motion is recognized and
    # triggers a jump.
    c.update(300, 100, 1 / 60, [t_start, t_far])
    c.update(480, 100, 1 / 60, [t_start, t_far])
    assert c.current_target is t_far
    assert c.captured_target is t_far


def test_object_pointing_snaps_back_without_target_in_cone():
    t_start = Target(100, 100, 15)
    other = Target(100, 500, 15)  # perpendicular, well outside any search cone
    c = ObjectPointingCursor()
    c.reset([t_start, other], start_pos=(100, 100))
    # Slow drift outside the safety zone, no candidate in the cone ahead
    c.update(400, 101, 1.0, [t_start, other])  # low speed (small dt-normalized distance/time)
    # Should snap back onto t_start's boundary rather than free-floating
    d_to_start = math.hypot(c.x - t_start.x, c.y - t_start.y)
    approx(d_to_start, t_start.radius, tol=0.5)


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("PASS", t.__name__)
    print(f"\nAll {len(tests)} tests passed.")
