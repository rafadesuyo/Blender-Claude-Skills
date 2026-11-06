# "Barn shop" (sheet 59, no text) on the barn base (barn.py): red plank walls, cream trims, dark
# slate roof, brick chimney, gold bow on the peak, string lights along the gable and eaves, a
# blank arched wooden sign in a gold frame with a little barn emblem, red / white striped awning,
# wall lanterns either side of the opening, a shop counter with jars, back shelves with boxes and
# jars, hanging lanterns inside, a lit front window with a flower box, a barrel, an apple crate
# and a hay bale. Glow (lanterns, lights, windows) = slot 1. check_closed + zfight must be 0.
#   exec(open(r"<skills>/blender-game-props/barn_shop.py").read())
#   build_barn_shop()
# --- skill file finder: works for manual installs (~/.claude/skills) and plugin installs ---
def _skill(rel):
    import os, glob
    roots = [os.environ.get("CLAUDE_BLENDER_SKILLS", ""), os.path.expanduser("~/.claude/skills")]
    roots += sorted(glob.glob(os.path.expanduser("~/.claude/plugins/**/skills"), recursive=True),
                    key=os.path.getmtime, reverse=True)
    for r in roots:
        if r and os.path.exists(os.path.join(r, rel)):
            os.environ["CLAUDE_BLENDER_SKILLS"] = r   # remember it for the next scripts
            return os.path.join(r, rel)
    raise FileNotFoundError("Blender skill file not found: %s (set the CLAUDE_BLENDER_SKILLS env var "
                            "to the folder that holds blender-game-props)" % rel)
# --- end skill file finder ---

import bpy, bmesh, math, random
from mathutils import Vector, Matrix

exec(open(_skill("blender-game-props/barn_set2.py")).read())

SLATE_ROOF = canopy(15, 1200, 1335)
SLATE_ROOF2 = canopy(15, 1130, 1230)
SIGN_WOOD = c0(35, 0.88, 0.95)
JAR = c0(8, 0.9, 0.97)
APPLE_R = c0(6, 0.9, 0.97)
S_SIGN = (0.0, 4.15)          # sign centre on the front gable
DISPLAY_Y, DISPLAY_TOP = -0.9, 0.75
PEDESTAL_X, PEDESTAL_Y, PEDESTAL_TOP = (-0.78, 0.78), 1.3, 1.05
GOLD_T = c0(23, 0.88, 0.97)
SHOP_INTERIOR = False   # display table, pedestals, shelves, hanging lanterns
S_W, S_H = 2.7, 0.95


def sign_outline(cx, cz, w, h, grow=0.0):
    """Board with an arched middle top and scrolled shoulders; even count, star-shaped."""
    hw, hh = w / 2 + grow, h / 2 + grow
    pts = [(-hw, -hh), (0.0, -hh - 0.02 * 0), (hw, -hh), (hw + 0.06, -hh * 0.2), (hw, hh * 0.45), (hw * 0.62, hh * 0.55)]
    arc = [(hw * 0.45 * math.cos(a), hh * 0.55 + (hh * 0.75 + grow) * math.sin(a)) for a in [math.pi * k / 8 for k in range(1, 8)]]
    pts += arc + [(-hw * 0.62, hh * 0.55), (-hw, hh * 0.45), (-hw - 0.06, -hh * 0.2)]
    if len(pts) % 2:
        pts.insert(1, (-hw / 2, -hh))
    return [(cx + x, cz + z) for x, z in pts]


def wall_lantern(bm, x, z):
    y = -FACE
    beam(bm, (x, y, z + 0.1), (x, y - 0.42, z + 0.1), 0.04, 0.04, IRON)
    beam(bm, (x, y, z - 0.18), (x, y - 0.28, z + 0.08), 0.03, 0.03, IRON)
    lantern(bm, (x, y - 0.4, z + 0.1), 0.6)


def string_lights(bm, pts, every=0.42):
    tube(bm, pts, [0.01] * len(pts), IRON, 6)
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        seg = math.dist(a, b)
        t = (every - acc) / seg if seg > 0 else 2
        while t <= 1.0:
            p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)
            glow(ball2)(bm, (p[0], p[1], p[2] - 0.06), 0.05, STAR_Y)
            t += every / seg
        acc = (acc + seg) % every


def jar(bm, x, y, z, s=1.0):
    revolve(bm, [(0.07 * s, z), (0.08 * s, z + 0.03 * s), (0.08 * s, z + 0.15 * s), (0.06 * s, z + 0.18 * s)], JAR, (x, y, 0), 10)
    revolve(bm, [(0.065 * s, z + 0.18 * s), (0.065 * s, z + 0.22 * s)], CREAM, (x, y, 0), 10)


def shop_extras(bm):
    y = -FACE
    # sign: gold frame behind a brown board, a little gold barn emblem on top, wheat sprigs
    slab(bm, sign_outline(*S_SIGN, S_W, S_H, 0.08), GOLD, 0.06, 0.0, 0.7, center=(S_SIGN[0], S_SIGN[1] + 0.05), at=(0, y - 0.04, 0))
    slab(bm, sign_outline(*S_SIGN, S_W, S_H), SIGN_WOOD, 0.05, 0.015, 0.7, center=(S_SIGN[0], S_SIGN[1] + 0.05), at=(0, y - 0.09, 0))
    ex, ez = S_SIGN[0], S_SIGN[1] + 0.72
    slab(bm, [(ex - 0.16, ez - 0.14), (ex + 0.16, ez - 0.14), (ex + 0.16, ez + 0.02), (ex, ez + 0.14), (ex - 0.16, ez + 0.02), (ex - 0.16, ez - 0.06)],
         GOLD, 0.04, 0.012, center=(ex, ez - 0.02), at=(0, y - 0.14, 0))
    for sx in (-1, 1):
        for k in range(3):
            leaf(bm, (S_SIGN[0] + sx * (S_W / 2 - 0.3), y - 0.13, S_SIGN[1] - 0.15 + k * 0.1), -90 + sx * (60 - k * 15), 0.16, 0.06, 55, GOLD, droop=-0.1)
    # gold bow on the peak
    bow(bm, (0.0, y - 0.3, 5.5), 2.4, GOLD)
    # string lights along the front gable edge and both eaves
    edge = [(x, y - 0.3, z - 0.12) for x, z in [(-HW - 0.1, WALL + 0.05), (-HW + 0.72, 4.66), (-0.35, 5.5)]]
    string_lights(bm, edge)
    string_lights(bm, [(-p[0], p[1], p[2]) for p in edge])
    for sx in (-1, 1):
        string_lights(bm, [(sx * (FACE + 0.2), -HD - 0.05 + 6.1 * t / 6, WALL - 0.02 - 0.12 * math.sin(math.pi * t / 6 * 6) * 0) for t in range(7)], 0.5)
    # brick chimney through the left roof slope
    cx, cyy = -1.25, 0.9
    box(bm, (cx, cyy, 5.45), (0.55, 0.55, 1.5), BRICK)
    box(bm, (cx, cyy, 6.25), (0.68, 0.68, 0.14), CREAM)
    box(bm, (cx, cyy, 6.4), (0.48, 0.48, 0.18), BRICK2)
    # striped awning red / cream with a scalloped edge
    n = 10
    x0, x1 = -OPEN_W - 0.35, OPEN_W + 0.35
    zt, zb, d0, d1 = OPEN_H + 0.55, OPEN_H + 0.12, -HD - 0.32, -HD - 1.05
    for i in range(n):
        xa = x0 + (x1 - x0) * i / n
        xb = x0 + (x1 - x0) * (i + 1) / n
        col = XRED if i % 2 == 0 else SNOW
        beam(bm, ((xa + xb) / 2, d0, zt + 0.004 * (i % 2)), ((xa + xb) / 2, d1, zb + 0.004 * (i % 2)), (xb - xa) - 0.004, 0.06, col)
        slab(bm, ellipse_pts((xb - xa) / 2 - 0.01, 0.12, 12, ((xa + xb) / 2, zb - 0.06)), col, 0.04, 0.012, at=(0, d1 - 0.02 - 0.006 * (i % 2), 0))
    # wall lanterns either side of the opening
    for sx in (-1, 1):
        wall_lantern(bm, sx * (OPEN_W + 0.2), 2.45)   # on the door frame posts
    # inside (off since 2026-10-25: Dante places the store items himself, the shop is empty)
    if SHOP_INTERIOR:
        # inside: a long display table for the three cash packs (top at DISPLAY_TOP, centre line
        # DISPLAY_Y) and two gold-topped pedestals behind it for VIP / Auto-Farm (PEDESTAL_*): the
        # store items stand on them (gab places their entities from these numbers)
        box(bm, (0.0, DISPLAY_Y, (DISPLAY_TOP - 0.06) / 2), (4.5, 0.7, DISPLAY_TOP - 0.06), WOOD)
        box(bm, (0.0, DISPLAY_Y, DISPLAY_TOP - 0.03), (4.65, 0.82, 0.06), LIGHT_WOOD)
        for i in range(10):
            box(bm, (-2.025 + i * 0.45, DISPLAY_Y - 0.355, (DISPLAY_TOP - 0.06) / 2), (0.04, 0.02, DISPLAY_TOP - 0.1), DARKWOOD)
        box(bm, (0.0, DISPLAY_Y - 0.395, DISPLAY_TOP - 0.1), (4.6, 0.04, 0.05), GOLD)
        for x in PEDESTAL_X:
            box(bm, (x, PEDESTAL_Y, (PEDESTAL_TOP - 0.08) / 2), (0.5, 0.5, PEDESTAL_TOP - 0.08), WOOD)
            box(bm, (x, PEDESTAL_Y, PEDESTAL_TOP - 0.04), (0.6, 0.6, 0.08), GOLD)
            box(bm, (x, PEDESTAL_Y, 0.27), (0.58, 0.58, 0.06), GOLD_T)
        for z in (1.35, 2.0):
            box(bm, (0.0, 2.55, z), (3.2, 0.36, 0.05), LIGHT_WOOD)
            for sx in (-1, 1):
                beam(bm, (sx * 1.35, 2.72, z - 0.25), (sx * 1.35, 2.42, z - 0.03), 0.05, 0.05, WOOD)
        for k, x in enumerate((-1.2, -0.85, 0.7, 1.05)):
            box(bm, (x, 2.55, 1.49 + 0.002 * k), (0.3, 0.26, 0.23), WOOD)
        for k, x in enumerate((-0.3, -0.1, 0.1, 1.2)):
            jar(bm, x, 2.55, 2.026 + 0.002 * k, 1.2)
        for x in (-0.8, 0.8):
            tube(bm, [(x, -0.3, OPEN_H - 0.05), (x, -0.3, OPEN_H - 0.4)], [0.012, 0.012], IRON, 6)
            lantern(bm, (x, -0.3, OPEN_H - 0.4), 0.45)
    # lit window on the front wall left of the opening, flower box under it
    window(bm, (-2.68, -FACE, 1.75), 0.6, 0.95, 'Y', -1)
    box(bm, (-2.68, -FACE - 0.13, 1.18), (0.72, 0.2, 0.16), WOOD)
    for k in range(4):
        flat_flower(bm, (-2.94 + k * 0.17, -FACE - 0.2, 1.33), 0.065, SNOWW)
    for k in range(3):
        ball2(bm, (-2.88 + k * 0.2, -FACE - 0.15, 1.27), 0.075, LEAF, (1.2, 1, 0.7), 1, 0.1, 950 + k)
    # out front: barrel, apple crate, hay bale
    barrel(bm, -2.85, -HD - 0.55, 0.62, 0.3)
    box(bm, (-1.95, -HD - 0.7, 0.2), (0.6, 0.45, 0.4), WOOD)
    for i in range(3):
        for j in range(2):
            ball2(bm, (-2.13 + i * 0.18, -HD - 0.8 + j * 0.2, 0.47), 0.09, APPLE_R, (1, 1, 0.92), 1, 0.06, 960 + i * 2 + j)
    hay(bm, (2.55, -HD - 0.6, 0.2), (0.85, 0.55, 0.4))


def build_barn_shop():
    _theme(ROOF_P=SLATE_ROOF, ROOF_P2=SLATE_ROOF2, LOFT_WINDOW=False, WIN_PANEL=STAR_Y, FRONT_HOLES=[(-2.98, -2.38, 1.27, 2.23)],
           GABLE_HOLES=[(S_SIGN[0] - S_W / 2 - 0.25, S_SIGN[0] + S_W / 2 + 0.25, S_SIGN[1] - S_H / 2 - 0.15, 5.6)])
    try:
        return build_barn("SM_Barn_Shop", -212.0, shop_extras)
    finally:
        _theme()
