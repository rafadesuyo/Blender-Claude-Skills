# Modular, seamless fences in the NewLua stylized farm pack style (gradient atlas, quads only,
# closed shells). Run inside the pack .blend:
#   exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/fences.py")).read())
#   build_fences()                 # all, or build_fences(["Picket_White"])
#
# CONNECTION RULE (so players can swap fence types on the same spots):
#   SM_Fence_<Name>       = one 2 m segment: its post at x = 0, rails / wall from x = 0 to x = SEG.
#                           Chain segments at x = 0, 2, 4 ... (rotate 90 deg around a post for corners).
#   SM_Fence_<Name>_Post  = a lone post to close the last segment (place it at the end, x = n * SEG).
#   Pivot at the start post's base centre, fence runs along +X, front faces -Y, ground at z = 0.
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/lamp_posts.py")).read())

SEG = 2.0
# Extra atlas strips added 2026-10-23 in empty space of the second row (v 0.680-0.830):
# col 6 grey stone, col 7 black iron, col 8 light warm stone, col 9 cream paint.
GREY_STONE = ((6 + 0.5) * CW, 0.685, 0.825)
IRON_BLACK = ((7 + 0.5) * CW, 0.685, 0.825)
LIGHT_STONE = ((8 + 0.5) * CW, 0.685, 0.825)
PAINT_CREAM = ((9 + 0.5) * CW, 0.685, 0.825)
CREAM = PAINT_CREAM
DARKWOOD = c1(2, 0.69, 0.74)
RUSTIC = c1(1, 0.69, 0.75)
BRICK = c0(6, 0.86, 0.93)
BRICK2 = c0(14, 0.93, 0.99)
BLACK = IRON_BLACK
HEDGE = c0(9, 0.85, 0.99)
HEDGE_DARK = c0(13, 0.85, 0.97)
FSTONE = GREY_STONE


def bolt(bm, c, r=0.025, round_head=False):
    if round_head:
        b = quad_sphere(r, 1, (1, 0.6, 1), 0, 0)
        bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
        uv_part(b, IRON)
        merge(bm, b)
    else:
        box(bm, c, (r * 1.4, r, r * 1.4), IRON)


def wood_post(bm, h, col, w=0.17, bolts=(), round_bolts=False, seed=0):
    rnd = random.Random(seed)
    box(bm, (0, 0, h / 2), (w, w, h), col, yaw=rnd.uniform(-1.5, 1.5))
    box(bm, (0, 0, h + 0.015), (w * 0.8, w * 0.8, 0.03), col)   # little bevelled cap
    for z in bolts:
        bolt(bm, (0, -w / 2 - 0.008, z), round_head=round_bolts)


def rails(bm, zs, col, h=0.13, d=0.06, x0=0.0, x1=SEG, sag=0.0, seed=0):
    rnd = random.Random(seed)
    for z in zs:
        if sag:   # slightly uneven rustic planks
            beam(bm, (x0, -0.01, z + rnd.uniform(-sag, sag)), (x1, -0.01, z + rnd.uniform(-sag, sag)), d, h, col)
        else:
            box(bm, ((x0 + x1) / 2, -0.01, z), (x1 - x0, d, h), col)


def picket(bm, x, h, col, w=0.14, d=0.04, tip=0.13):
    """Pointed picket from quads only: a pentagon-ish outline (tiny flat tip) extruded."""
    b = bmesh.new()
    hw = w / 2
    pts = [(-hw, 0), (hw, 0), (hw, h - tip), (0.012, h), (-0.012, h), (-hw, h - tip)]
    front = [b.verts.new((x + px, -d / 2, pz)) for px, pz in pts]
    back = [b.verts.new((x + px, d / 2, pz)) for px, pz in pts]
    b.faces.new((front[0], front[1], front[2], front[5]))
    b.faces.new((front[5], front[2], front[3], front[4]))
    b.faces.new((back[5], back[2], back[1], back[0]))
    b.faces.new((back[4], back[3], back[2], back[5]))
    n = len(pts)
    for i in range(n):
        b.faces.new((front[i], back[i], back[(i + 1) % n], front[(i + 1) % n]))
    uv_part(b, col)
    merge(bm, b)


def stone_pillar(bm, h, w, col, cap_col=None, seed=0, rows=4):
    rnd = random.Random(seed)
    rh = h / rows
    for r in range(rows):
        ww = w * rnd.uniform(0.97, 1.0)
        if r % 2 == 0:
            box(bm, (-ww / 4, 0, rh * (r + 0.5)), (ww / 2 - 0.012, ww, rh - 0.012), col, yaw=rnd.uniform(-2, 2))
            box(bm, (ww / 4, 0, rh * (r + 0.5)), (ww / 2 - 0.012, ww, rh - 0.012), col, yaw=rnd.uniform(-2, 2))
        else:
            box(bm, (0, -ww / 4, rh * (r + 0.5)), (ww, ww / 2 - 0.012, rh - 0.012), col, yaw=rnd.uniform(-2, 2))
            box(bm, (0, ww / 4, rh * (r + 0.5)), (ww, ww / 2 - 0.012, rh - 0.012), col, yaw=rnd.uniform(-2, 2))
    if cap_col:
        box(bm, (0, 0, h + 0.05), (w * 1.12, w * 1.12, 0.1), cap_col)


def stone_courses(bm, x0, x1, z0, z1, depth, col, seed=0, rows=3, gap=0.014):
    """Wall of stone blocks filling exactly x0..x1 (so segments meet flush), random block lengths."""
    rnd = random.Random(seed)
    rh = (z1 - z0) / rows
    for r in range(rows):
        x = x0
        while x < x1 - 1e-4:
            ln = min(rnd.uniform(0.32, 0.55), x1 - x)
            if x1 - (x + ln) < 0.15:   # no slivers at the end
                ln = x1 - x
            s0 = gap / 2 + (0.008 if x <= x0 + 1e-6 else 0.0)   # first block a little further from the post
            box(bm, (x + s0 + (ln - gap / 2 - s0) / 2, 0, z0 + rh * (r + 0.5)), (ln - gap / 2 - s0, depth * rnd.uniform(0.96, 1.0), rh - gap), col,
                yaw=rnd.uniform(-1, 1))
            x += ln


def bricks(bm, x0, x1, z0, z1, depth, seed=0):
    """Brick courses on a cream mortar core, filling exactly x0..x1."""
    rnd = random.Random(seed)
    box(bm, ((x0 + x1) / 2, 0, (z0 + z1) / 2), (x1 - x0, depth * 0.92, z1 - z0), CREAM)
    bh, bl = 0.1, 0.26
    rows = int(round((z1 - z0) / bh))
    for r in range(rows):
        x = x0 - (bl / 2 if r % 2 else 0)
        while x < x1 - 1e-4:
            a, b_ = max(x, x0), min(x + bl, x1)
            if b_ - a > 0.03:
                # end bricks stop 12 mm short of the segment end: the post bricks own that plane
                a2, b2 = a + (0.0125 if a <= x0 + 1e-6 else 0.0075), b_ - (0.0125 if b_ >= x1 - 1e-6 else 0.0075)
                box(bm, ((a2 + b2) / 2, 0, z0 + bh * (r + 0.5)), (b2 - a2, depth, bh - 0.015), BRICK if rnd.random() > 0.3 else BRICK2)
            x += bl


def ball(bm, c, r, col):
    b = quad_sphere(r, 2, (1, 1, 1), 0, 0)
    bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
    uv_part(b, col)
    merge(bm, b)


def leafy(bm, x0, x1, z0, z1, depth, seed=0):
    """Hedge: a green core + overlapping leaf clumps, kept inside x0..x1."""
    rnd = random.Random(seed)
    box(bm, ((x0 + x1) / 2, 0, (z0 + z1) / 2), (x1 - x0, depth, z1 - z0), HEDGE_DARK)
    for side in (-1, 1):
        for i in range(10):
            for j in range(3):
                r = rnd.uniform(0.13, 0.17)
                x = min(max(x0 + r, x0 + (i + 0.5) * (x1 - x0) / 10 + rnd.uniform(-0.04, 0.04)), x1 - r)
                c = (x, side * depth * 0.42, z0 + (j + 0.5) * (z1 - z0) / 3 + rnd.uniform(-0.03, 0.03))
                b = quad_sphere(r, 1, (1, 0.7, 1), 0.12, i * 7 + j + (side > 0) * 50)
                bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
                uv_part(b, HEDGE)
                merge(bm, b)
    for i in range(9):
        r = rnd.uniform(0.14, 0.18)
        x = min(max(x0 + r, x0 + (i + 0.5) * (x1 - x0) / 9), x1 - r)
        b = quad_sphere(r, 1, (1, 1, 0.7), 0.12, 200 + i)
        bmesh.ops.translate(b, vec=Vector((x, 0, z1)), verts=b.verts)
        uv_part(b, HEDGE)
        merge(bm, b)


# ---------------- fence designs: (post builder, panel builder) ----------------
def wood2_post(bm): wood_post(bm, 1.05, WOOD, bolts=(0.38, 0.78))
def wood2_panel(bm): rails(bm, (0.38, 0.78), WOOD)

def rustic_post(bm): wood_post(bm, 1.05, RUSTIC, bolts=(0.38, 0.78), seed=3)
def rustic_panel(bm): rails(bm, (0.36, 0.8), RUSTIC, h=0.15, sag=0.025, seed=4)

def white_post(bm): wood_post(bm, 1.05, CREAM, bolts=(0.38, 0.78))
def white_panel(bm): rails(bm, (0.38, 0.78), CREAM)

def cross_post(bm): wood_post(bm, 1.05, WOOD, bolts=(0.2, 0.9))
def cross_panel(bm):
    rails(bm, (0.2, 0.9), WOOD)
    beam(bm, (0.15, -0.01, 0.24), (SEG - 0.15, -0.01, 0.86), 0.05, 0.11, WOOD)
    beam(bm, (0.15, 0.0, 0.86), (SEG - 0.15, 0.0, 0.24), 0.05, 0.11, WOOD)   # behind the first and the rails: they cross

def dark_post(bm): wood_post(bm, 1.05, DARKWOOD, w=0.18, bolts=(0.38, 0.78), round_bolts=True, seed=5)
def dark_panel(bm): rails(bm, (0.38, 0.78), DARKWOOD, h=0.14, sag=0.012, seed=6)

def picket_post(col):
    def f(bm):
        picket(bm, 0, 1.12, col, w=0.17, d=0.07, tip=0.15)
        bolt(bm, (0, -0.045, 0.3)); bolt(bm, (0, -0.045, 0.75))
    return f

def picket_panel(col):
    def f(bm):
        rails(bm, (0.3, 0.75), col, h=0.1, d=0.04, x0=0.0, x1=SEG)
        n = 5
        for i in range(n):
            x = (i + 1) * SEG / (n + 1)
            picket(bm, x, 1.0, col)
            bolt(bm, (x, -0.03, 0.3)); bolt(bm, (x, -0.03, 0.75))
    return f

def stonerail_post(bm): stone_pillar(bm, 1.1, 0.38, FSTONE, FSTONE, seed=7)
def stonerail_panel(bm): rails(bm, (0.38, 0.78), WOOD, x0=0.1, x1=SEG + 0.1)

def stonewall_post(bm): stone_pillar(bm, 0.95, 0.42, FSTONE, FSTONE, seed=8, rows=3)
def stonewall_panel(bm): stone_courses(bm, 0.0, SEG, 0.0, 0.8, 0.36, FSTONE, seed=9, rows=4)

def brick_post(bm):
    box(bm, (0, 0, 0.08), (0.48, 0.48, 0.16), LIGHT_STONE)
    for r in range(8):
        for k in range(2):
            if r % 2 == 0:
                box(bm, (-0.1 + k * 0.2, 0, 0.21 + r * 0.1), (0.185, 0.4, 0.085), BRICK if (r + k) % 3 else BRICK2)
            else:
                box(bm, (0, -0.1 + k * 0.2, 0.21 + r * 0.1), (0.4, 0.185, 0.085), BRICK if (r + k) % 3 else BRICK2)
    box(bm, (0, 0, 1.03), (0.5, 0.5, 0.12), LIGHT_STONE)
def brick_panel(bm):
    box(bm, (SEG / 2, 0, 0.06), (SEG, 0.34, 0.12), LIGHT_STONE)
    bricks(bm, 0.0, SEG, 0.12, 0.82, 0.28, seed=10)
    box(bm, (SEG / 2, 0, 0.87), (SEG, 0.34, 0.1), LIGHT_STONE)

def stonelow_post(bm): stone_pillar(bm, 1.1, 0.4, FSTONE, FSTONE, seed=11)
def stonelow_panel(bm):
    stone_courses(bm, 0.0, SEG, 0.0, 0.42, 0.34, FSTONE, seed=12, rows=2)
    rails(bm, (0.82,), WOOD, h=0.14, x0=0.1, x1=SEG + 0.1)

def hedge_post(bm): wood_post(bm, 1.15, WOOD, w=0.18, bolts=(0.3, 0.85))
def hedge_panel(bm): leafy(bm, 0.12, SEG - 0.12, 0.05, 1.0, 0.42, seed=13)

def iron_post(bm):
    box(bm, (0, 0, 0.06), (0.2, 0.2, 0.12), BLACK)
    tube(bm, [(0, 0, 0.12), (0, 0, 1.05)], [0.06, 0.055], BLACK, 8)
    box(bm, (0, 0, 1.08), (0.15, 0.15, 0.06), BLACK)
    ball(bm, (0, 0, 1.18), 0.08, BLACK)
def iron_panel(bm):
    rails(bm, (0.2, 0.85), BLACK, h=0.05, d=0.04)
    n = 9
    for i in range(n):
        x = (i + 0.5) * SEG / n
        box(bm, (x, -0.01, 0.55), (0.035, 0.028, 0.9), BLACK)
        if i % 2 == 0:
            box(bm, (x, -0.01, 1.04), (0.07, 0.04, 0.09), BLACK, taper=0.12)   # spear tip

def ironstone_post(bm):
    stone_pillar(bm, 1.2, 0.36, LIGHT_STONE, LIGHT_STONE, seed=14, rows=5)
    ball(bm, (0, 0, 1.4), 0.12, LIGHT_STONE)
    for i in range(5):   # a little climbing ivy
        leaf(bm, (0.19, -0.19 + (i % 2) * 0.05, 0.2 + i * 0.2), -60 + i * 25, 0.15, 0.08, -10, GRASS, droop=-0.2)
def ironstone_panel(bm):
    stone_courses(bm, 0.0, SEG, 0.0, 0.3, 0.32, LIGHT_STONE, seed=15, rows=2)
    rails(bm, (0.42, 1.0), BLACK, h=0.04, d=0.035)
    n = 10
    for i in range(n):
        x = (i + 0.5) * SEG / n
        box(bm, (x, 0, 0.7), (0.03, 0.03, 0.8), BLACK)
        box(bm, (x, 0, 1.12), (0.05, 0.035, 0.06), BLACK, taper=0.15)


FENCES = [  # name, post, panel   (no rope designs)
    ("Wood_TwoRail", wood2_post, wood2_panel),
    ("Wood_Rustic", rustic_post, rustic_panel),
    ("White_TwoRail", white_post, white_panel),
    ("Wood_Cross", cross_post, cross_panel),
    ("Wood_Dark", dark_post, dark_panel),
    ("Picket_White", picket_post(CREAM), picket_panel(CREAM)),
    ("Picket_Brown", picket_post(DARKWOOD), picket_panel(DARKWOOD)),
    ("Stone_Rail", stonerail_post, stonerail_panel),
    ("Stone_Wall", stonewall_post, stonewall_panel),
    ("Brick_Wall", brick_post, brick_panel),
    ("Stone_LowRail", stonelow_post, stonelow_panel),
    ("Hedge", hedge_post, hedge_panel),
    ("Iron_Spike", iron_post, iron_panel),
    ("Iron_Stone", ironstone_post, ironstone_panel),
]


def build_fences(only=None):
    root = bpy.data.collections.get("Fences") or bpy.data.collections.new("Fences")
    if root.name not in [c.name for c in bpy.context.scene.collection.children]:
        bpy.context.scene.collection.children.link(root)
    objs = []
    for row, (name, post, panel) in enumerate(FENCES):
        if only and name not in only:
            continue
        sub = bpy.data.collections.get("Fence_" + name) or bpy.data.collections.new("Fence_" + name)
        if sub.name not in [c.name for c in root.children]:
            root.children.link(sub)
        y = -14 - row * 2.0
        bm = bmesh.new()
        post(bm)
        panel(bm)
        objs.append(finish_lamp(bm, "SM_Fence_" + name, sub, (0, y, 0)))
        bm = bmesh.new()
        post(bm)
        objs.append(finish_lamp(bm, "SM_Fence_%s_Post" % name, sub, (SEG, y, 0)))   # closes the segment
    return check_closed(objs)
