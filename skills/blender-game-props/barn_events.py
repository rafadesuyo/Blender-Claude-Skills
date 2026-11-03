# Event-exclusive player barns (sheets 58 / 59) on the default barn's base (barn.py), recoloured
# and decorated. Every build runs check_closed + zfight (must be 0).
#   exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/barn_events.py")).read())
#   build_barn_halloween(); build_barn_christmas()
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/barn.py")).read())

_BASE = dict(RED=RED, RED_DARK=RED_DARK, ROOF_P=ROOF_P, ROOF_P2=ROOF_P2, TIMBER=TIMBER, FLOOR=FLOOR, TRIM=TRIM,
             WIN_PANEL=WIN_PANEL, LOFT_WINDOW=LOFT_WINDOW, SIDE_WINDOWS=SIDE_WINDOWS, DOOR_POST=DOOR_POST,
             GABLE_HOLES=GABLE_HOLES, SIDE_HOLES=SIDE_HOLES, FRONT_HOLES=FRONT_HOLES)


def _theme(**kw):
    """Sets barn.py's theme globals (base values first, so themes never leak into each other)."""
    globals().update(_BASE)
    globals().update(kw)


def jack_facing(bm, c, r, facing_x, seed):
    """Jack-o-lantern at c whose carved face points along +X (facing_x=1) or -X (-1)."""
    t = bmesh.new()
    f_jack(t, (facing_x * 1.0, 0.0, 0.0), r, seed)
    bmesh.ops.translate(t, vec=Vector(c) - Vector((facing_x * 1.0, 0.0, 0.0)), verts=t.verts)
    merge(bm, t)


# ---------------- Halloween ----------------
H_WALL = c0(30, 0.955, 0.985)   # deep plum, darker than the roof
H_SEAM = c0(30, 0.985, 0.998)
H_ORANGE = c0(8, 0.88, 0.95)
H_TIMBER = c0(8, 0.9, 0.97)
WEB = c0(27, 0.95, 0.99)
BAT_C = (0.95, 4.3)
WEB_C = (-1.25, 3.72)
PUMPKIN_Y = -0.7


def bat_pts(s, c):
    half = [(0.06, 0.16), (0.1, 0.08), (0.3, 0.16), (0.55, 0.22), (0.48, 0.02), (0.36, 0.06), (0.28, -0.04), (0.16, 0.0)]
    pts = [(0.0, 0.1)] + half + [(0.0, -0.2)] + [(-x, z) for x, z in reversed(half)]
    return [(c[0] + x * s, c[1] + z * s) for x, z in pts]


def halloween_extras(bm):
    y = -FACE
    # bat on the front gable
    slab(bm, bat_pts(1.6, BAT_C), H_ORANGE, 0.05, 0.015, center=(BAT_C[0], BAT_C[1] - 0.05), at=(0, y - 0.03, 0))
    # cobweb in the gable corner, under the left roof slope
    cx, cz = WEB_C
    r = 0.72
    for k in range(5):
        a = math.pi * k / 4
        dy = y - 0.025 - 0.005 * k   # spokes meet at the centre: each at its own depth
        beam(bm, (cx, dy, cz), (cx + r * math.cos(a), dy, cz + r * math.sin(a)), 0.012, 0.014, WEB)
    for i, rr in enumerate((0.35, 0.6, 0.85)):
        pts = [(cx + r * rr * math.cos(math.pi * k / 8), y - 0.052 - 0.006 * i, cz + r * rr * math.sin(math.pi * k / 8)) for k in range(9)]
        tube(bm, pts, [0.008] * 9, WEB, 4)
    # jack-o-lanterns stacked on both side walls
    for sx in (-1, 1):
        for z, rr, sd in ((0.95, 0.44, 1), (1.95, 0.4, 2)):
            jack_facing(bm, (sx * (FACE + rr * 1.08 + 0.02), PUMPKIN_Y, z), rr, sx, sd + (sx > 0) * 10)


def build_barn_halloween():
    _theme(RED=H_WALL, RED_DARK=H_SEAM, TRIM=H_ORANGE, TIMBER=H_TIMBER, FLOOR=c1(1, 0.77, 0.81),
           LOFT_WINDOW=False, SIDE_WINDOWS=False,
           GABLE_HOLES=[(BAT_C[0] - 0.95, BAT_C[0] + 0.95, BAT_C[1] - 0.4, BAT_C[1] + 0.45),
                        (WEB_C[0] - 0.78, WEB_C[0] + 0.78, WEB_C[1] - 0.05, WEB_C[1] + 0.78)],
           SIDE_HOLES=[(PUMPKIN_Y - 0.55, PUMPKIN_Y + 0.55, 0.45, 2.45)])
    try:
        return build_barn("SM_Barn_Halloween", -108.0, halloween_extras)
    finally:
        _theme()


# ---------------- Christmas ----------------
X_GREEN = c0(13, 0.86, 0.92)
X_GREEN2 = c0(13, 0.89, 0.95)
WARM = c0(23, 0.93, 0.99)


def candy_post(bm, x):
    pts = [(x, -HD - 0.05, 0.15 + (OPEN_H) * k / 8) for k in range(9)]
    for i in range(8):
        tube(bm, [pts[i], pts[i + 1]], [0.17, 0.17], XRED if i % 2 else SNOW, 10)


def christmas_extras(bm):
    y = -FACE
    # wreath with a bow and lights on the front gable
    t = bmesh.new()
    torus(t, (0, 0, 0), 0.46, 0.13, PINE_G, 'Z', 20, 8)
    bmesh.ops.rotate(t, cent=Vector(), matrix=Matrix.Rotation(math.radians(90), 3, 'X'), verts=t.verts)
    bmesh.ops.translate(t, vec=Vector((0, y - 0.2, 4.3)), verts=t.verts)
    merge(bm, t)
    for k in range(8):
        a = math.pi * 2 * k / 8 + 0.2
        glow(ball2)(bm, (0.46 * math.cos(a), y - 0.34, 4.3 + 0.46 * math.sin(a)), 0.055, GOLD)
    bow(bm, (0, y - 0.36, 4.78), 2.2, XRED)
    # garland with lights along the door frame, snow on top of it
    gar = [(-OPEN_W - 0.15 + (2 * OPEN_W + 0.3) * i / 12, y - 0.38, OPEN_H + 0.12 - 0.12 * math.sin(math.pi * i / 12)) for i in range(13)]
    garland(bm, gar, 501, 0.1)
    lights_string(bm, [(p[0], p[1] - 0.09, p[2] - 0.02) for p in gar], 2, 0.05)
    snow_top = [(-OPEN_W - 0.32, -HD - 0.05, OPEN_H + 0.1), (-OPEN_W + 0.22, -HD - 0.05, OPEN_H + 0.47),
                (OPEN_W - 0.22, -HD - 0.05, OPEN_H + 0.47), (OPEN_W + 0.32, -HD - 0.05, OPEN_H + 0.1)]
    band(bm, snow_top, 0.47, 0.12, SNOW)
    # snow on the roof: puffy clumps along the ridge, the two roof breaks and the eaves, and
    # along the front / back roof edges (round parts: they never share planes)
    rnd = random.Random(502)
    depth = 2 * HD + 0.5
    for (px, pz) in PROFILE:
        n = 14
        for k in range(n + 1):
            yy = -depth / 2 + 0.1 + (depth - 0.2) * k / n
            r = rnd.uniform(0.17, 0.24)
            ball2(bm, (px * 0.98 + rnd.uniform(-0.05, 0.05), yy, pz + 0.3), r, SNOW, (1.5, 1.2, 0.5), 1, 0.12, 600 + k + int(px * 10) * 20)
    for sy in (-1, 1):
        for i in range(len(PROFILE) - 1):
            (x0, z0), (x1, z1) = PROFILE[i], PROFILE[i + 1]
            for k in range(1, 4):
                t = k / 4
                ball2(bm, (x0 + (x1 - x0) * t, sy * (depth / 2 - 0.05), z0 + (z1 - z0) * t + 0.3), rnd.uniform(0.15, 0.2), SNOW, (1.3, 0.9, 0.55), 1, 0.12, 700 + i * 10 + k + (sy > 0) * 50)
    # snow caps on the side windows, snow drifts at the corners
    for sx in (-1, 1):
        box(bm, (sx * (FACE + 0.079), -0.6, 1.7 + 0.95 / 2 + 0.055), (0.146, 0.89, 0.1), SNOW)   # 6 mm off the wall, 5 mm above the seams
    for sx in (-1, 1):
        for sy in (-1, 1):
            snow_mound(bm, (sx * (HW + 0.25), sy * (HD + 0.25), 0.0), 0.45, 520 + sx + 2 * sy)


def build_barn_christmas():
    _theme(ROOF_P=X_GREEN, ROOF_P2=X_GREEN2, LOFT_WINDOW=False, WIN_PANEL=WARM, DOOR_POST=candy_post,
           GABLE_HOLES=[(-0.75, 0.75, 3.7, 5.2)])
    try:
        return build_barn("SM_Barn_Christmas", -116.0, christmas_extras)
    finally:
        _theme()
