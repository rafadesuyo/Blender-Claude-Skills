# Premium store as a barn (barn.py base, like the Market): royal purple plank walls, gold trims,
# gold shingle roof, a gold crown on the ridge, a big glowing diamond on the gable, a gold sign
# board (gab's PREMIUM STORE title sits on it) with gem studs, a purple / gold striped awning,
# gold lamp posts with glowing globes, a red carpet out of the door and gold coin piles.
# Glowing parts: slot 1 = M_GradientGlow (atlas colours). Runs check_closed + zfight (must be 0).
#   exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/premium_barn.py")).read())
#   build_premium_barn()
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/premium.py")).read())

P_WALL = canopy(5, 1235, 1335)
P_SEAM = canopy(5, 1120, 1210)
P_ROOF = c0(23, 0.88, 0.95)
P_ROOF2 = c0(23, 0.9, 0.97)
P_TRIM = c0(23, 0.86, 0.92)
P_SIGN_C = (0.0, 4.3)
P_SIGN_W, P_SIGN_H = 2.6, 0.82


def premium_extras(bm):
    y = -FACE
    # crown on the ridge
    crown(bm, (0, 0, 6.05), 1.5)
    # diamond above the sign, gems along the gable trim
    gem(bm, (0, y - 0.36, 5.05), 0.33, GEM_CYAN)
    for i, (x, z) in enumerate(((-1.5, 4.35), (1.5, 4.35), (-2.5, 3.65), (2.5, 3.65))):
        glow(ball2)(bm, (x, y - 0.3 - 0.006 * i, z), 0.1, (GEM_PINK, GEM_GREEN, GEM_VIOLET, GEM_CYAN)[i], (1, 0.55, 1))
    # gold sign board for the title: dark purple board in a gold frame (bars butt, own depths)
    cx, cz = P_SIGN_C
    box(bm, (cx, y - 0.04, cz), (P_SIGN_W, 0.06, P_SIGN_H), P_SEAM)
    for dz in (-1, 1):
        box(bm, (cx, y - 0.05, cz + dz * (P_SIGN_H / 2 + 0.05)), (P_SIGN_W + 0.2, 0.1, 0.1), GOLD)
    for dx in (-1, 1):
        box(bm, (cx + dx * (P_SIGN_W / 2 + 0.05), y - 0.048, cz), (0.1, 0.094, P_SIGN_H), GOLD)
        glow(ball2)(bm, (cx + dx * (P_SIGN_W / 2 + 0.05), y - 0.12, cz), 0.07, GEM_PINK, (1, 0.6, 1))
    # striped awning, purple / gold, scalloped edge, gold brackets
    n = 10
    x0, x1 = -OPEN_W - 0.35, OPEN_W + 0.35
    zt, zb, d0, d1 = OPEN_H + 0.55, OPEN_H + 0.12, -HD - 0.32, -HD - 1.05
    for i in range(n):
        xa = x0 + (x1 - x0) * i / n
        xb = x0 + (x1 - x0) * (i + 1) / n
        col = P_WALL if i % 2 == 0 else GOLD
        beam(bm, ((xa + xb) / 2, d0, zt + 0.004 * (i % 2)), ((xa + xb) / 2, d1, zb + 0.004 * (i % 2)), (xb - xa) - 0.004, 0.06, col)
        slab(bm, ellipse_pts((xb - xa) / 2 - 0.01, 0.12, 12, ((xa + xb) / 2, zb - 0.06)), col, 0.04, 0.012, at=(0, d1 - 0.02 - 0.006 * (i % 2), 0))
    for sx in (-1, 1):
        beam(bm, (sx * (OPEN_W + 0.3), -HD - 0.3, OPEN_H - 0.15), (sx * (OPEN_W + 0.3), d1 + 0.12, zb - 0.01), 0.06, 0.06, GOLD)
    # glowing light strip under the eaves on the front
    glow(box)(bm, (0, -HD - 0.33, OPEN_H + 0.62), (2 * OPEN_W + 0.6, 0.04, 0.05), STAR_Y)
    # red carpet out of the door with gold edges, lamp posts, coins
    box(bm, (0, -HD - 1.6, 0.02), (2.4, 2.8, 0.04), CARPET)
    for sx in (-1, 1):
        box(bm, (sx * 1.23, -HD - 1.6, 0.025), (0.06, 2.8, 0.05), GOLD_T)
        lamp_post(bm, sx * 2.0, -HD - 2.6)
        coins(bm, (sx * 2.6, -HD - 0.55, 0.0), 6, 50 + (sx > 0))
        coins(bm, (sx * 2.9, -HD - 0.75, 0.0), 4, 60 + (sx > 0))
        coins(bm, (sx * 2.45, -HD - 0.9, 0.0), 3, 70 + (sx > 0))


def build_premium_barn():
    _theme(RED=P_WALL, RED_DARK=P_SEAM, ROOF_P=P_ROOF, ROOF_P2=P_ROOF2, TRIM=P_TRIM, FLOOR=CARPET,
           LOFT_WINDOW=False, WIN_PANEL=STAR_Y,
           GABLE_HOLES=[(P_SIGN_C[0] - P_SIGN_W / 2 - 0.15, P_SIGN_C[0] + P_SIGN_W / 2 + 0.15, P_SIGN_C[1] - P_SIGN_H / 2 - 0.12, 5.45),
                        (-2.7, -2.3, 3.45, 3.85), (2.3, 2.7, 3.45, 3.85)])
    try:
        res = build_barn("SM_Premium_Barn", -200.0, premium_extras)
    finally:
        _theme()
    o = bpy.data.objects["SM_Premium_Barn"]
    o.data.materials[1] = bpy.data.materials["M_GradientGlow"]
    return res
