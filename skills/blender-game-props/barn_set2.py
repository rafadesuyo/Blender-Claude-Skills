# Six more player barns (sheet 60) on the default barn's base (barn.py), recoloured and decorated:
# Horseshoe (rooster vane, hay inside), Sunflower, Night (moon + stars), Bow (hearts), Autumn
# (maple leaves, pumpkins), Rainbow (cloud, stars, scalloped awning). Extra colours come from the
# daily-reward trees' bands in the atlas (canopy rows 1040-1340, fruit rows 712-1012, one column
# per tree), which are already in the game's atlas. Every build runs check_closed + zfight (0).
#   exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/barn_set2.py")).read())
#   build_barn_set2()            # or build_barn_set2(["Night"])
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/barn_events.py")).read())


def canopy(col, r0, r1):
    return ((col + 0.5) * CW, r0 / 2048, r1 / 2048)


def fruitb(col, r0, r1):
    return ((col + 0.5) * CW, r0 / 2048, r1 / 2048)


NAVY = canopy(21, 1190, 1330)
NAVY_DARK = canopy(21, 1060, 1150)
INDIGO = canopy(9, 1200, 1330)
INDIGO2 = canopy(9, 1150, 1250)
PINK_W = canopy(20, 1200, 1330)
PINK_W_DARK = canopy(20, 1060, 1150)
PINK_ROOF = canopy(1, 1200, 1330)
PINK_ROOF2 = canopy(1, 1140, 1240)
PINK_PALE = canopy(14, 1220, 1330)
LILAC_W = canopy(12, 1150, 1240)
LILAC_W_DARK = canopy(12, 1060, 1130)
LILAC_ROOF = canopy(12, 1250, 1335)
LILAC_ROOF2 = canopy(12, 1200, 1280)
BLUSH = canopy(27, 1220, 1335)
BROWN_ROOF = c0(35, 0.86, 0.92)
BROWN_ROOF2 = c0(35, 0.89, 0.95)
RUST_ROOF = canopy(22, 1180, 1320)
RUST_ROOF2 = canopy(22, 1100, 1220)
SUN_WOOD = c0(17, 0.88, 0.96)
SUN_SEAM = c0(17, 0.86, 0.875)
YELLOW_TRIM = c0(16, 0.86, 0.91)
MAPLE_RED = fruitb(18, 730, 1000)
LEAF_ORANGE = c0(8, 0.9, 0.99)
STAR_Y = c0(23, 0.93, 0.995)
SNOWW = c0(18, 0.85, 0.87)

GY = -FACE      # the front gable's face


def rooster_vane(bm):
    top = 5.95 + 0.08
    tube(bm, [(0, 0, top), (0, 0, top + 0.6)], [0.04, 0.04], IRON, 6)
    beam(bm, (-0.45, 0, top + 0.42), (0.45, 0, top + 0.42), 0.04, 0.04, IRON)
    box(bm, (0.5, 0, top + 0.42), (0.12, 0.03, 0.12), IRON, taper=0.2)
    r = [(-0.16, 0.0), (0.03, 0.0), (0.19, 0.07), (0.23, 0.24), (0.13, 0.37), (0.08, 0.24), (-0.05, 0.16), (-0.21, 0.27), (-0.27, 0.13), (-0.21, 0.05)]
    slab(bm, [(x * 2.4, top + 0.58 + z * 2.4) for x, z in r], GOLD, 0.09, 0.02, center=(0.0, top + 0.58 + 0.15 * 2.4))


def x_horseshoe(bm):
    pts = [(0.5 * math.cos(math.radians(a)), GY - 0.07, 4.3 + 0.5 * math.sin(math.radians(a))) for a in range(-40, 225, 12)]
    band(bm, pts, 0.12, 0.18, GOLD)
    for a in (-10, 40, 90, 140, 190):
        ball2(bm, (0.5 * math.cos(math.radians(a)), GY - 0.14, 4.3 + 0.5 * math.sin(math.radians(a))), 0.035, IRON, (1, 0.6, 1))
    rooster_vane(bm)
    for c, s in (((0.55, 1.9, 0.39), (0.55, 0.35, 0.3)), ((1.13, 1.9, 0.39), (0.55, 0.35, 0.3)), ((0.84, 1.9, 0.69), (0.5, 0.33, 0.28))):
        hay(bm, c, s)


def x_sunflower(bm):
    c = (0.0, 4.3)
    slab(bm, polar(lambda a: 0.72 * (0.72 + 0.28 * math.cos(12 * a)), 48, c), GOLD, 0.06, 0.025, center=c, at=(0, GY - 0.06, 0))
    ball2(bm, (c[0], GY - 0.13, c[1]), 0.3, DARKWOOD, (1, 0.45, 1), 2)
    for sx in (-1, 1):
        flat_flower(bm, (sx * 1.25, GY - 0.06, 4.0), 0.2, STAR_Y)
        for k in range(2):
            leaf(bm, (sx * (1.25 + 0.15 * k), GY - 0.06, 3.65 - 0.12 * k), -90 + sx * (40 + 30 * k), 0.3, 0.17, 50, LEAF, droop=-0.2)
    # vines up the door posts
    rnd = random.Random(801)
    for sx in (-1, 1):
        x = sx * (OPEN_W + 0.1)
        pts = [(x + 0.08 * math.sin(i * 1.2), -HD - 0.3, 0.3 + i * 0.32) for i in range(10)]
        tube(bm, pts, [0.025] * len(pts), LEAF_DARK, 6)
        for i in range(1, 10, 2):
            p = pts[i]
            leaf(bm, (p[0], p[1] - 0.02, p[2]), rnd.uniform(-160, -20), 0.18, 0.12, 30, LEAF, droop=-0.25)
        for i in (2, 6):
            p = pts[i]
            flat_flower(bm, (p[0] + 0.06, p[1] - 0.06, p[2]), 0.07, STAR_Y)
    # flower boxes under the side windows
    for sx in (-1, 1):
        box(bm, (sx * (FACE + 0.125), -0.6, 1.11), (0.18, 0.86, 0.16), WOOD)
        for k in range(4):
            flat_flower(bm, (sx * (FACE + 0.16), -0.6 - 0.3 + k * 0.2, 1.28), 0.07, STAR_Y)
        for k in range(3):
            ball2(bm, (sx * (FACE + 0.13), -0.6 - 0.22 + k * 0.22, 1.21), 0.08, LEAF, (1, 1.2, 0.7), 1, 0.1, 810 + k + (sx > 0) * 5)


def x_night(bm):
    pts = [(0.62 + 0.55 * math.cos(math.radians(a)), GY - 0.17, 4.35 + 0.55 * math.sin(math.radians(a))) for a in range(110, 330, 15)]
    n = len(pts)
    tube(bm, pts, [0.03 + 0.16 * math.sin(math.pi * i / (n - 1)) for i in range(n)], GOLD, 8)
    for (x, z, r) in ((-0.6, 4.6, 0.17), (-1.1, 4.0, 0.13), (-0.2, 5.0, 0.1), (0.0, 3.85, 0.11), (1.45, 4.0, 0.1), (-1.55, 3.6, 0.09)):
        star5(bm, (x, GY - 0.05, z), r, GOLD, 0.06)


def x_bow(bm):
    bow(bm, (0.0, GY - 0.2, 4.72), 4.6, PINK_PALE)
    heart(bm, (0.0, GY - 0.07, 3.78), 0.6, PINK_ROOF, 0.08)
    heart(bm, (0.0, GY - 0.14, 3.8), 0.38, PINK_PALE, 0.05)
    for sx in (-1, 1):
        heart(bm, (sx * 2.55, -FACE - 0.05, 1.55), 0.38, PINK_PALE, 0.06)


def maple(bm, c, r, col, y, rot=0.0):
    pts = polar(lambda a: r * (0.5 + 0.5 * abs(math.cos(2.5 * (a - math.pi / 2 - math.radians(rot))))), 30, (c[0], c[1]))
    slab(bm, pts, col, 0.04, 0.015, center=(c[0], c[1]), at=(0, y, 0))


def x_autumn(bm):
    maple(bm, (0.0, 4.35), 0.72, LEAF_ORANGE, GY - 0.05)
    box(bm, (0.0, GY - 0.05, 3.55), (0.07, 0.03, 0.3), DARKWOOD)
    for i, (x, z, r, col) in enumerate(((-1.2, 4.0, 0.3, MAPLE_RED), (1.25, 3.95, 0.32, STAR_Y), (-0.75, 4.9, 0.2, STAR_Y), (0.8, 4.95, 0.2, MAPLE_RED))):
        maple(bm, (x, z), r, col, GY - 0.05 - 0.008 * i, 20 * i - 30)
    for i, (x, z, col) in enumerate(((-OPEN_W - 0.15, OPEN_H + 0.2, MAPLE_RED), (OPEN_W + 0.2, OPEN_H + 0.15, LEAF_ORANGE), (OPEN_W + 0.05, OPEN_H - 0.4, STAR_Y), (-OPEN_W + 0.1, OPEN_H - 0.35, LEAF_ORANGE))):
        maple(bm, (x, z), 0.2, col, -HD - 0.3 - 0.008 * i, 35 * i)
    for (x, y, r) in ((-HW - 0.35, -HD - 0.45, 0.42), (-HW + 0.25, -HD - 0.6, 0.3)):
        ball2(bm, (x, y, r * 0.85), r, LEAF_ORANGE, (1.1, 1.1, 0.85), 2, 0.05, int(r * 100))
        tube(bm, [(x, y, r * 1.6), (x + 0.05, y, r * 1.85)], [0.04, 0.025], DARKWOOD, 6)


def x_rainbow(bm):
    for k, col in enumerate(RAINBOW):
        rr = 0.9 - k * 0.118
        pts = [(0.35 + rr * math.cos(math.pi * i / 16), GY - 0.06, 3.85 + rr * math.sin(math.pi * i / 16)) for i in range(17)]
        band(bm, pts, 0.09, 0.115, col)
    circles = [(-0.85, 3.85, 0.28), (-0.45, 4.02, 0.36), (-0.05, 3.85, 0.28)]
    slab(bm, cloud_pts(circles, (-1.08, 0.2, 3.65, 3.85), (-0.45, 3.85)), SNOWW, 0.24, 0.05, 0.7, center=(-0.45, 3.85), at=(0, GY - 0.18, 0))
    star5(bm, (1.45, GY - 0.08, 3.9), 0.25, GOLD, 0.07)
    # scalloped awning hanging under the door frame
    n = 9
    for i in range(n):
        x = -OPEN_W + 0.05 + (2 * OPEN_W - 0.1) * (i + 0.5) / n
        slab(bm, ellipse_pts(0.23, 0.13, 12, (x, OPEN_H - 0.08)), BLUSH, 0.05, 0.015, at=(0, -HD - 0.3 - 0.007 * (i % 2), 0))
    for sx in (-1, 1):
        star5(bm, (sx * 2.55, -FACE - 0.06, 1.35), 0.17, GOLD, 0.05)


BARNS2 = {
    "Horseshoe": (dict(ROOF_P=BROWN_ROOF, ROOF_P2=BROWN_ROOF2, LOFT_WINDOW=False,
                       GABLE_HOLES=[(-0.68, 0.68, 3.7, 4.92)]), x_horseshoe),
    "Sunflower": (dict(RED=SUN_WOOD, RED_DARK=SUN_SEAM, ROOF_P=X_GREEN, ROOF_P2=X_GREEN2, TRIM=YELLOW_TRIM, LOFT_WINDOW=False,
                       GABLE_HOLES=[(-1.6, 1.6, 3.45, 5.1)], WIN_PANEL=STAR_Y), x_sunflower),
    "Night": (dict(RED=NAVY, RED_DARK=NAVY_DARK, ROOF_P=INDIGO, ROOF_P2=INDIGO2, FLOOR=NAVY, LOFT_WINDOW=False, WIN_PANEL=STAR_Y,
                   GABLE_HOLES=[(-1.7, 1.6, 3.45, 5.15)]), x_night),
    "Bow": (dict(RED=PINK_W, RED_DARK=PINK_W_DARK, ROOF_P=PINK_ROOF, ROOF_P2=PINK_ROOF2, FLOOR=PINK_PALE, LOFT_WINDOW=False,
                 GABLE_HOLES=[(-1.45, 1.45, 3.4, 5.2)]), x_bow),
    "Autumn": (dict(ROOF_P=RUST_ROOF, ROOF_P2=RUST_ROOF2, TRIM=YELLOW_TRIM, LOFT_WINDOW=False,
                    GABLE_HOLES=[(-1.6, 1.65, 3.4, 5.2)]), x_autumn),
    "Rainbow": (dict(RED=LILAC_W, RED_DARK=LILAC_W_DARK, ROOF_P=LILAC_ROOF, ROOF_P2=LILAC_ROOF2, TRIM=BLUSH, FLOOR=LILAC_ROOF,
                     LOFT_WINDOW=False, WIN_PANEL=STAR_Y, GABLE_HOLES=[(-1.2, 1.75, 3.5, 4.85)]), x_rainbow),
}


def build_barn_set2(only=None):
    out = {}
    for i, (name, (theme, extras)) in enumerate(BARNS2.items()):
        if only and name not in only:
            continue
        _theme(**theme)
        try:
            res = build_barn("SM_Barn_" + name, -124.0 - 8 * i, extras)
        finally:
            _theme()
        out[name] = (res[0]["SM_Barn_" + name], len(res[1]), res[1][:6], res[2])
    return out
