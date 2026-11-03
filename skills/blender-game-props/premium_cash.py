# Premium store cash items (gab store_item models) in the pack style: bright green bill stacks
# with gold paper bands, gold coin piles, gold bars, glowing gems and a crown on the biggest one.
# Pivot at the bottom centre (the items spin around it in game). check_closed + zfight = 0.
#   exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/premium_cash.py")).read())
#   build_premium_cash()
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/premium.py")).read())

BILL = c0(19, 0.86, 0.97)
BILL_EDGE = SNOWW
BAND = GOLD
BAR = GOLD_T
SW, SD, SH = 0.46, 0.22, 0.13      # one bill stack (x, y, z)


def stack(bm, c, yaw=0.0, k=0):
    """A bill stack: green block with a lighter paper edge layer and a gold band round the middle.
    k varies its height a little, so neighbouring stacks never share a top plane."""
    x, y, z = c
    h = SH + 0.007 * (k % 3)
    t = bmesh.new()
    box(t, (0, 0, h / 2), (SW, SD, h), BILL)
    box(t, (0, 0, h / 2), (SW - 0.03, SD + 0.012, h - 0.05), BILL_EDGE)      # paper edges peeking out
    box(t, (0, 0, h / 2), (0.08, SD + 0.03, h + 0.014), BAND)
    bmesh.ops.rotate(t, cent=Vector(), matrix=Matrix.Rotation(math.radians(yaw), 3, 'Z'), verts=t.verts)
    bmesh.ops.translate(t, vec=Vector((x, y, z)), verts=t.verts)
    merge(bm, t)


def coin_pile(bm, c, n, seed, r=0.08):
    rnd = random.Random(seed)
    x, y, z = c
    for i in range(n):
        revolve(bm, [(r, z + i * 0.026), (r * 1.02, z + i * 0.026 + 0.012), (r, z + i * 0.026 + 0.024)], GOLD,
                (x + rnd.uniform(-0.012, 0.012), y + rnd.uniform(-0.012, 0.012), 0), 12)


def gold_bar(bm, c, yaw=0.0):
    box(bm, (c[0], c[1], c[2] + 0.05), (0.3, 0.13, 0.1), BAR, yaw=yaw, taper=0.78)


def sparkle(bm, c, r):
    glow(star5)(bm, c, r, STAR_Y, 0.03)


def cash_small(bm):
    stack(bm, (0.0, -0.125, 0.0), 3, 0)
    stack(bm, (0.02, 0.125, 0.0), -3, 1)
    stack(bm, (0.0, 0.0, SH + 0.02), 84, 2)
    coin_pile(bm, (0.36, -0.16, 0.0), 5, 1)
    coin_pile(bm, (0.42, 0.04, 0.0), 3, 2)
    sparkle(bm, (-0.3, -0.12, 0.42), 0.07)


def cash_medium(bm):
    rnd = random.Random(7)
    for i, (x, y) in enumerate(((-0.25, -0.135), (0.25, -0.135), (-0.25, 0.135), (0.25, 0.135))):
        stack(bm, (x, y, 0.0), rnd.uniform(-2, 2), i)
    for i, (x, y) in enumerate(((-0.125, 0.0), (0.125, 0.0))):
        stack(bm, (x, y, SH + 0.02), 90 + rnd.uniform(-2, 2), i)
    stack(bm, (0.0, 0.0, 2 * SH + 0.04), rnd.uniform(-8, 8), 2)
    gold_bar(bm, (-0.55, 0.05, 0.0), 80)
    gold_bar(bm, (0.56, -0.05, 0.0), 95)
    coin_pile(bm, (0.42, -0.36, 0.0), 6, 11)
    coin_pile(bm, (-0.45, -0.34, 0.0), 4, 12)
    coin_pile(bm, (0.0, -0.38, 0.0), 3, 13)
    for k, (x, z) in enumerate(((-0.4, 0.6), (0.42, 0.5))):
        sparkle(bm, (x, -0.2, z), 0.08)


def cash_large(bm):
    rnd = random.Random(21)
    # (x, y, yaw) per layer: stacks laid in rows with gaps, each layer crossing the one below
    layers = [
        [(x, y, 0) for x in (-0.5, 0.0, 0.5) for y in (-0.27, 0.0, 0.27)],
        [(x, y, 90) for x in (-0.27, 0.0, 0.27) for y in (-0.25, 0.25)],
        [(x, y, 0) for x in (-0.25, 0.25) for y in (-0.125, 0.125)],
        [(0.0, y, 90) for y in (0.0,)],
    ]
    for li, layer in enumerate(layers):
        for k, (x, y, yaw) in enumerate(layer):
            stack(bm, (x, y, li * (SH + 0.03)), yaw + rnd.uniform(-2, 2), k + li)
    for k, (x, y, yaw) in enumerate(((-0.75, -0.3, 70), (0.78, -0.25, 110), (-0.72, 0.3, 95), (0.74, 0.32, 80))):
        gold_bar(bm, (x, y, 0.0), yaw)
    gold_bar(bm, (-0.74, -0.3, 0.1), 85)
    for k, (x, y, n) in enumerate(((0.5, -0.5, 7), (-0.5, -0.52, 5), (0.0, -0.55, 4), (0.85, 0.05, 6), (-0.86, 0.02, 4))):
        coin_pile(bm, (x, y, 0.0), n, 30 + k)
    for k, (x, y, col) in enumerate(((0.28, -0.52, GEM_PINK), (-0.25, -0.52, GEM_CYAN), (0.62, -0.42, GEM_GREEN))):
        gem(bm, (x, y, 0.1), 0.09, col)
    crown(bm, (0.0, 0.0, 3 * (SH + 0.03) + SH + 0.03), 0.42)
    for k, (x, z) in enumerate(((-0.6, 0.85), (0.6, 0.75), (0.15, 1.2))):
        sparkle(bm, (x, -0.3, z), 0.09)


CASH = [("SM_PremiumCash_Small", cash_small), ("SM_PremiumCash_Medium", cash_medium), ("SM_PremiumCash_Large", cash_large)]


def build_premium_cash():
    root = bpy.data.collections.get("PremiumItems") or bpy.data.collections.new("PremiumItems")
    if root.name not in [c.name for c in bpy.context.scene.collection.children]:
        bpy.context.scene.collection.children.link(root)
    out = {}
    for i, (name, fn) in enumerate(CASH):
        bm = bmesh.new()
        fn(bm)
        o = finish_lamp(bm, name, root, (i * 3.0, -240.0, 0))
        o.data.materials[1] = bpy.data.materials["M_GradientGlow"]
        out[name] = (check_closed([o])[name], zfight(o)[:6], [round(d, 2) for d in o.dimensions])
    return out
