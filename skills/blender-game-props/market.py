# The Market building on the barn base (barn.py) so it matches the player barns: blue plank walls,
# orange shingle roof, cream trims, a striped awning over the opening, a wooden sign board on the
# gable (gab's MARKET title sits on it) and produce crates either side of the door.
# Pivot at the bottom centre, front -Y. Runs check_closed + zfight (must be 0).
#   exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/market.py")).read())
#   build_market()
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/barn_set2.py")).read())

M_BLUE = canopy(19, 1200, 1330)
M_BLUE_DARK = canopy(19, 1060, 1150)
M_ROOF = c0(8, 0.88, 0.95)
M_ROOF2 = c0(8, 0.9, 0.97)
SIGN_C = (0.0, 4.3)          # the sign board's centre on the front gable (x, z)
SIGN_W, SIGN_H = 2.5, 0.78
APPLE = c0(6, 0.9, 0.97)
ORANGE_F = c0(8, 0.92, 0.99)
GREEN_F = c0(9, 0.9, 0.99)


def produce_crate(bm, c, fruit_col, seed):
    x, y, z = c
    w, d, h = 0.62, 0.48, 0.42
    box(bm, (x, y, z + h / 2), (w - 0.04, d - 0.04, h - 0.04), WOOD)
    for sx in (-1, 1):
        box(bm, (x + sx * (w / 2 - 0.03), y, z + h / 2), (0.06, d, h), LIGHT_WOOD)
    for zz in (z + 0.1, z + h - 0.1):
        box(bm, (x, y - d / 2 + 0.01, zz), (w - 0.12, 0.03, 0.08), LIGHT_WOOD)
    rnd = random.Random(seed)
    for i in range(3):
        for j in range(2):
            ball2(bm, (x - 0.18 + i * 0.18 + rnd.uniform(-0.02, 0.02), y - 0.1 + j * 0.2, z + h + 0.03 + rnd.uniform(0, 0.03)),
                  0.1, fruit_col, (1, 1, 0.92), 1, 0.06, seed * 10 + i * 3 + j)


def market_extras(bm):
    y = -FACE
    # sign board on the gable: plank board in a darker frame (frame bars butt, own depths)
    cx, cz = SIGN_C
    box(bm, (cx, y - 0.04, cz), (SIGN_W, 0.06, SIGN_H), RUSTIC)
    for dz in (-1, 1):
        box(bm, (cx, y - 0.05, cz + dz * (SIGN_H / 2 + 0.04)), (SIGN_W + 0.16, 0.1, 0.08), DARKWOOD)
    for dx in (-1, 1):
        box(bm, (cx + dx * (SIGN_W / 2 + 0.04), y - 0.048, cz), (0.08, 0.094, SIGN_H), DARKWOOD)
    # striped awning over the opening: slats sloping out, alternating red / cream, a scalloped edge
    n = 10
    x0, x1 = -OPEN_W - 0.35, OPEN_W + 0.35
    zt, zb, d0, d1 = OPEN_H + 0.55, OPEN_H + 0.12, -HD - 0.32, -HD - 1.05
    for i in range(n):
        xa = x0 + (x1 - x0) * i / n
        xb = x0 + (x1 - x0) * (i + 1) / n
        col = XRED if i % 2 == 0 else SNOW
        beam(bm, ((xa + xb) / 2, d0, zt + 0.004 * (i % 2)), ((xa + xb) / 2, d1, zb + 0.004 * (i % 2)), (xb - xa) - 0.004, 0.06, col)
        slab(bm, ellipse_pts((xb - xa) / 2 - 0.01, 0.12, 12, ((xa + xb) / 2, zb - 0.06)), col, 0.04, 0.012, at=(0, d1 - 0.02 - 0.006 * (i % 2), 0))
    for sx in (-1, 1):   # brackets holding the awning
        beam(bm, (sx * (OPEN_W + 0.3), -HD - 0.3, OPEN_H - 0.15), (sx * (OPEN_W + 0.3), d1 + 0.12, zb - 0.01), 0.06, 0.06, DARKWOOD)
    # produce crates either side of the door
    for i, (x, yy, col) in enumerate(((-2.62, -HD - 0.6, APPLE), (-2.78, -HD - 1.2, ORANGE_F), (2.62, -HD - 0.6, GREEN_F), (2.78, -HD - 1.2, APPLE))):
        produce_crate(bm, (x, yy, 0.0), col, 900 + i)


def build_market():
    _theme(RED=M_BLUE, RED_DARK=M_BLUE_DARK, ROOF_P=M_ROOF, ROOF_P2=M_ROOF2, LOFT_WINDOW=False,
           GABLE_HOLES=[(SIGN_C[0] - SIGN_W / 2 - 0.12, SIGN_C[0] + SIGN_W / 2 + 0.12, SIGN_C[1] - SIGN_H / 2 - 0.1, SIGN_C[1] + SIGN_H / 2 + 0.1)])
    try:
        return build_barn("SM_Market_Barn", -175.0, market_extras)
    finally:
        _theme()
