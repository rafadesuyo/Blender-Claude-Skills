# Entrance gates, set 2 (sheet 50): Christmas x3, Halloween x2, blossom, ranch skull, nautical,
# torii. Same rules as gates.py (pivot at the centre of the opening, front -Y, pillars at +-PX).
# The sheet's gates have closed double doors; here the doors stand OPEN, swung back into the base
# (+Y), so players can walk through.
#   exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/gates2.py")).read())
#   build_gates2()
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/gates.py")).read())

SNOW = c0(18, 0.85, 0.87)
XRED = c0(14, 0.93, 0.99)
PINE_G = c0(13, 0.85, 0.99)
ORANGE = c0(8, 0.9, 0.99)
NAVY = c0(21, 0.86, 0.92)
SLATE = c0(30, 0.9, 0.95)
DARK_PURPLE = c0(30, 0.94, 0.998)
LIGHT_WOOD = c1(1, 0.78, 0.83)
GINGER = c1(1, 0.74, 0.79)


def part(fn, *a, rot=0.0, at=(0, 0, 0), pivot=(0, 0, 0), glowing=False, **k):
    """Builds fn into its own mesh, turns it about Z around pivot, moves it, merges it."""
    def g(bm):
        t = bmesh.new()
        fn(t, *a, **k)
        if rot:
            bmesh.ops.rotate(t, cent=Vector(pivot), matrix=Matrix.Rotation(math.radians(rot), 3, 'Z'), verts=t.verts)
        bmesh.ops.translate(t, vec=Vector(at), verts=t.verts)
        if glowing:
            for f in t.faces:
                f.material_index = 1
        merge(bm, t)
    return g


def door_leaf(bm, w, h, col, style='slats', top=0.12, heart_col=None):
    """One gate leaf from x = 0 (hinge) to x = w, standing on z = 0.08, facing -Y."""
    z0 = 0.08
    for z in (z0 + 0.12, z0 + h * 0.55):
        box(bm, (w / 2, 0, z), (w - 0.04, 0.07, 0.11), col)   # rails end inside the stiles (no shared faces)
    box(bm, (0.05, 0, z0 + h / 2), (0.1, 0.08, h), col)
    box(bm, (w - 0.05, 0, z0 + h / 2 + top / 2), (0.1, 0.08, h + top), col)
    n = max(3, int(w / 0.24))
    for i in range(n):
        x = 0.12 + (w - 0.24) * (i + 0.5) / n
        hh = h + top * (x / w)
        if style == 'slats':
            box(bm, (x, 0.0, z0 + hh / 2), (0.1, 0.05, hh), col)
        elif style == 'pickets':
            picket(bm, x, z0 + hh, col, 0.12, 0.05, 0.08)
    pts = [(0.012, 0, z0 + h), (w - 0.012, 0, z0 + h + top)]   # band caps inside the stiles' outer faces
    band(bm, pts, 0.09, 0.1, col)
    if style == 'cross':
        beam(bm, (0.1, -0.03, z0 + 0.18), (w - 0.1, -0.03, z0 + h * 0.5), 0.05, 0.09, col)
        beam(bm, (0.1, -0.03, z0 + h * 0.6), (w - 0.1, -0.03, z0 + h - 0.05), 0.05, 0.09, col)
    if heart_col:
        heart(bm, (w * 0.75, -0.05, z0 + h * 0.75), 0.2, heart_col, 0.05)


def open_doors(bm, half=1.5, h=1.0, col=WOOD, style='slats', angle=72, top=0.12, heart_col=None, extra=None):
    """Two leaves hinged at x = -half and +half, both swung back (+Y) by angle."""
    w = half - 0.04
    for sx in (-1, 1):
        t = bmesh.new()
        door_leaf(t, w, h, col, style, top, heart_col if sx > 0 else None)
        if extra:
            extra(t, w, h)
        if sx > 0:
            bmesh.ops.scale(t, vec=Vector((-1, 1, 1)), verts=t.verts)
            bmesh.ops.reverse_faces(t, faces=t.faces)
        bmesh.ops.rotate(t, cent=Vector(), matrix=Matrix.Rotation(math.radians(-sx * angle), 3, 'Z'), verts=t.verts)
        bmesh.ops.translate(t, vec=Vector((sx * half, 0, 0)), verts=t.verts)
        merge(bm, t)


def snow_on(bm, x0, x1, z, depth, seed, thick=0.1):
    rnd = random.Random(seed)
    box(bm, ((x0 + x1) / 2, 0, z + thick / 2), (x1 - x0 + 0.06, depth + 0.06, thick), SNOW)
    n = max(2, int((x1 - x0) / 0.35))
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n
        ball2(bm, (x + rnd.uniform(-0.05, 0.05), -depth / 2, z + 0.02), rnd.uniform(0.06, 0.1), SNOW, (1.3, 0.8, 0.9), 1, 0.1, seed + i)


def snow_mound(bm, c, r, seed):
    ball2(bm, c, r, SNOW, (1.4, 1.0, 0.35), 2, 0.1, seed)


def lights_string(bm, pts, every=2, r=0.045):
    tube(bm, pts, [0.01] * len(pts), PINE_G, 6)
    for i in range(1, len(pts) - 1, every):
        p = pts[i]
        glow(ball2)(bm, (p[0], p[1] - 0.03, p[2] - 0.05), r, GOLD, (1, 1, 1.2))


def garland(bm, pts, seed, r=0.08):
    rnd = random.Random(seed)
    for i, p in enumerate(pts):
        ball2(bm, (p[0], p[1], p[2]), r * rnd.uniform(0.85, 1.15), PINE_G if i % 2 else LEAF_DARK, (1.3, 1, 1), 1, 0.15, seed + i)


def gift(bm, c, s, col, ribbon=GOLD):
    x, y, z = c
    box(bm, (x, y, z + s / 2), (s, s, s), col)
    box(bm, (x, y, z + s / 2), (s * 1.05, s * 0.2, s * 1.04), ribbon)
    box(bm, (x, y, z + s / 2), (s * 0.23, s * 1.09, s * 1.08), ribbon)   # its own depth: the ribbons cross
    for k in (-1, 1):
        slab(bm, ellipse_pts(s * 0.18, s * 0.1, 10, (x + k * s * 0.14, z + s * 1.06), k * 25), ribbon, 0.03, 0.01, at=(0, y, 0))


def snowman(bm, c, s=1.0):
    x, y, z = c
    ball2(bm, (x, y, z + 0.22 * s), 0.25 * s, SNOW, (1, 1, 0.92), 2)
    ball2(bm, (x, y, z + 0.58 * s), 0.18 * s, SNOW, (1, 1, 0.95), 2)
    torus(bm, (x, y, z + 0.46 * s), 0.13 * s, 0.035 * s, XRED, 'Z', 14, 6)
    box(bm, (x + 0.08 * s, y - 0.1 * s, z + 0.36 * s), (0.07 * s, 0.03 * s, 0.2 * s), XRED)
    revolve(bm, [(0.17 * s, 0.72 * s), (0.17 * s, 0.75 * s), (0.11 * s, 0.75 * s), (0.11 * s, 0.9 * s)], IRON_BLACK, (x, y, z), 12)
    tube(bm, [(x, y - 0.16 * s, z + 0.6 * s), (x, y - 0.28 * s, z + 0.59 * s)], [0.025 * s, 0.006 * s], ORANGE, 6)
    for dx in (-0.06, 0.06):
        ball2(bm, (x + dx * s, y - 0.16 * s, z + 0.66 * s), 0.018 * s, IRON_BLACK)


def bell(bm, c, s=1.0, col=GOLD):
    revolve(bm, [(0.2 * s, 0), (0.17 * s, 0.05 * s), (0.12 * s, 0.18 * s), (0.1 * s, 0.3 * s), (0.04 * s, 0.34 * s)], col, c, 14)
    ball2(bm, (c[0], c[1], c[2] - 0.02 * s), 0.05 * s, col)


def candy_cane(bm, x, h, r=0.16, outward=1, seed=0):
    pts = [(x, 0, 0)] + [(x, 0, h * t / 8) for t in range(1, 9)]
    R = 0.38
    cx = x + outward * R
    for k in range(1, 8):   # the hook curls over and out
        pts.append((cx - outward * R * math.cos(math.pi * k / 7), 0, h + R * math.sin(math.pi * k / 7)))
    for i in range(len(pts) - 1):
        tube(bm, [pts[i], pts[i + 1]], [r, r], XRED if i % 2 else SNOW, 12)
        if 0 < i:
            ball2(bm, pts[i], r * 1.001, XRED if i % 2 else SNOW, (1, 1, 1), 1)


def stocking(bm, c, col=XRED):
    x, y, z = c
    slab(bm, [(x - 0.06, z), (x + 0.06, z), (x + 0.06, z - 0.22), (x + 0.12, z - 0.28), (x + 0.1, z - 0.36), (x - 0.06, z - 0.33)], col, 0.05, 0.015, center=(x, z - 0.17), at=(0, y, 0))
    box(bm, (x, y, z), (0.16, 0.07, 0.06), SNOW)


def mini_tree(bm, c, s=1.0):
    x, y, z = c
    box(bm, (x, y, z + 0.08 * s), (0.08 * s, 0.08 * s, 0.16 * s), DARKWOOD)
    for k, (r, z0, z1) in enumerate(((0.32, 0.14, 0.5), (0.25, 0.4, 0.75), (0.17, 0.65, 0.95))):
        revolve(bm, [(r * s, z0 * s), (0.03 * s, z1 * s)], PINE_G, (x, y, z), 10)
    star5(bm, (x, y - 0.02, z + 1.0 * s), 0.08 * s, GOLD, 0.04)
    for k in range(5):
        a = k * 1.3
        glow(ball2)(bm, (x + 0.2 * s * math.cos(a) * (1 - k * 0.12), y - 0.2 * s * abs(math.sin(a)) - 0.03, z + (0.25 + k * 0.13) * s), 0.03 * s, GOLD)


# ---------------- Christmas ----------------
def g_xmas_bow(bm):
    for sx in (-1, 1):
        x = sx * PX
        box(bm, (x, 0, 1.15), (0.36, 0.36, 2.3), XRED)
        snow_on(bm, x - 0.2, x + 0.2, 2.3, 0.4, 200 + (sx > 0))
    arch = arch_pts(-PX - 0.3, PX + 0.3, 2.2, 2.6, 0.0, 14)
    band(bm, arch, 0.4, 0.26, XRED)
    garland(bm, [(p[0], -0.2, p[2] - 0.05) for p in arch[1:-1]], 210)
    snow = [(p[0], 0.0, p[2] + 0.16) for p in arch]
    band(bm, snow, 0.475, 0.08, SNOW)
    for i, p in enumerate(snow[::2]):
        ball2(bm, (p[0], -0.2, p[2] - 0.02), 0.09, SNOW, (1.4, 0.8, 0.8), 1, 0.1, 220 + i)
    lights_string(bm, [(p[0], -0.24, p[2] - 0.2 - 0.1 * math.sin(i * 0.9)) for i, p in enumerate(arch)], 1)
    bow(bm, (0, -0.25, 2.62), 3.2, XRED)
    bell(bm, (0, -0.22, 2.05), 1.3)
    open_doors(bm, PX - 0.18, 1.0, XRED, 'slats', 72, 0.15)
    snowman(bm, (PX + 0.55, -0.4, 0), 1.2)
    gift(bm, (-PX - 0.4, -0.4, 0), 0.32, XRED)
    gift(bm, (-PX - 0.05, -0.45, 0), 0.24, PINE_G, XRED)
    snow_mound(bm, (-PX, -0.35, 0), 0.5, 230)
    snow_mound(bm, (PX + 0.4, -0.3, 0), 0.5, 231)


def g_candy_cane(bm):
    for sx in (-1, 1):
        candy_cane(bm, sx * PX, 2.3, 0.16, sx)
        snow_mound(bm, (sx * PX, -0.2, 0), 0.5, 240 + (sx > 0))
        gift(bm, (sx * (PX + 0.35), -0.4, 0), 0.3, XRED if sx < 0 else PINE_G, GOLD)
    pts = [(-PX + 0.05 + (2 * PX - 0.1) * i / 12, -0.05, 2.35 - 0.2 * math.sin(math.pi * i / 12)) for i in range(13)]
    garland(bm, pts, 250, 0.09)
    lights_string(bm, [(p[0], -0.14, p[2] - 0.05) for p in pts], 2)
    t = bmesh.new()
    torus(t, (0, 0, 0), 0.42, 0.13, PINE_G, 'Z', 18, 6)
    bmesh.ops.rotate(t, cent=Vector(), matrix=Matrix.Rotation(math.radians(90), 3, 'X'), verts=t.verts)
    bmesh.ops.translate(t, vec=Vector((0, -0.1, 2.25)), verts=t.verts)
    merge(bm, t)
    for k in range(10):
        a = 2 * math.pi * k / 10
        if k % 2:
            ball2(bm, (0.42 * math.cos(a), -0.25, 2.25 + 0.42 * math.sin(a)), 0.05, XRED)
        else:
            glow(ball2)(bm, (0.42 * math.cos(a), -0.25, 2.25 + 0.42 * math.sin(a)), 0.045, GOLD)
    bow(bm, (0, -0.3, 2.62), 2.0, XRED)
    open_doors(bm, PX - 0.18, 1.0, c0(6, 0.86, 0.93), 'slats', 72, 0.15)


def g_ginger_lodge(bm):
    for sx in (-1, 1):
        x = sx * PX
        box(bm, (x, 0, 1.15), (0.36, 0.36, 2.3), WOOD)
        hang_lantern(bm, x - sx * 0.18, 1.95, -0.05, 0.55, 0.28, -sx)
        snow_mound(bm, (x, -0.25, 0), 0.45, 260 + (sx > 0))
    box(bm, (0, 0, 2.38), (2 * PX + 0.5, 0.42, 0.18), WOOD)
    for sgn in (-1, 1):
        band(bm, [(sgn * 2.25, 0, 2.35), (0.0, 0, 3.3)], 0.8 + 0.012 * (sgn > 0), 0.14, DARKWOOD)   # the slopes meet: own depths
        band(bm, [(sgn * 2.25, 0, 2.47), (0.0, 0, 3.42)], 0.86 + 0.012 * (sgn > 0), 0.1, SNOW)
    slab(bm, [(-1.9, 2.47), (0.0, 2.47), (1.9, 2.47), (0.0, 3.25)], WOOD, 0.3, 0.0, 0.6, center=(0.0, 2.75))
    star5(bm, (0, -0.2, 2.8), 0.26, GINGER, 0.07)
    star5(bm, (0, -0.24, 2.8), 0.18, SNOW, 0.02)
    star5(bm, (0, -0.27, 2.8), 0.15, GINGER, 0.02)
    for k in range(3):
        ball2(bm, (0, -0.31, 2.72 + k * 0.08), 0.02, XRED)
    garland(bm, [(-PX + 0.2 + (2 * PX - 0.4) * i / 10, -0.25, 2.3 - 0.2 * math.sin(math.pi * i / 10)) for i in range(11)], 270)
    def socks(t, w, h):
        stocking(t, (w * 0.5, -0.06, 0.08 + h * 0.85))
    open_doors(bm, PX - 0.18, 1.0, DARKWOOD, 'slats', 72, 0.15, extra=socks)
    mini_tree(bm, (-PX - 0.45, -0.3, 0), 1.2)
    mini_tree(bm, (PX + 0.5, -0.1, 0), 0.8)


# ---------------- Halloween ----------------
def bat_wing(bm, x, z, sx, col=SLATE):
    pts = [(0, 0), (0.25, 0.2), (0.6, 0.38), (0.95, 0.42), (0.85, 0.18), (0.7, 0.05), (0.52, 0.12), (0.4, -0.05), (0.24, 0.04), (0.1, -0.12)]
    slab(bm, [(x + sx * px, z + pz) for px, pz in pts], col, 0.06, 0.02, center=(x + sx * 0.4, z + 0.12), at=(0, 0.05, 0))


def curl(bm, c, r0, turns, col, sx=1, y=0.0, rad=0.04):
    pts = [(c[0] + sx * (r0 * (1 - 0.7 * t / 20)) * math.cos(math.pi * turns * 2 * t / 20), y, c[1] + (r0 * (1 - 0.7 * t / 20)) * math.sin(math.pi * turns * 2 * t / 20)) for t in range(21)]
    tube(bm, pts, [rad * (1 - 0.5 * t / 20) for t in range(21)], col, 8)


def cobweb(bm, c, r, y):
    for k in range(5):
        a = math.pi * k / 4
        beam(bm, (c[0], y, c[1]), (c[0] + r * math.cos(a), y, c[1] + r * math.sin(a)), 0.012, 0.012, SNOW)
    for rr in (0.4, 0.7, 1.0):
        pts = [(c[0] + r * rr * math.cos(math.pi * k / 8), y, c[1] + r * rr * math.sin(math.pi * k / 8)) for k in range(9)]
        tube(bm, pts, [0.007] * 9, SNOW, 4)


def g_pumpkin_bat(bm):
    rnd = random.Random(300)
    for sx in (-1, 1):
        x = sx * PX
        for r in range(7):
            box(bm, (x + rnd.uniform(-0.02, 0.02), 0, 0.15 + r * 0.3), (0.52 - (r % 2) * 0.05, 0.46, 0.28), PURPLE_STONE, yaw=rnd.uniform(-3, 3))
        hang_lantern(bm, x - sx * 0.26, 1.6, -0.05, 0.55, 0.26, -sx)
        bat_wing(bm, x + sx * 0.1, 2.35, sx)
        curl(bm, (x + sx * 0.4, 0.5), 0.25, 1.2, LEAF_DARK, sx, -0.25)
    f_jack(bm, (-PX - 0.5, -0.45, 0.28), 0.3, 301)
    for i in range(9):
        a0, a1 = math.pi * i / 9, math.pi * (i + 1) / 9
        beam(bm, (PX * math.cos(a0), 0, 2.0 + 0.55 * math.sin(a0)), (PX * math.cos(a1), 0, 2.0 + 0.55 * math.sin(a1)), 0.44 - 0.012 * (i % 2), 0.34, PURPLE_STONE)
    f_jack(bm, (0, -0.2, 2.65), 0.34, 310)
    cobweb(bm, (-PX + 0.25, 1.95), 0.45, -0.24)
    cobweb(bm, (PX - 0.25, 1.95), -0.45, -0.24)
    open_doors(bm, PX - 0.27, 1.05, DARK_PURPLE, 'slats', 72, 0.12)
    curl(bm, (PX + 0.45, 0.35), 0.22, 1.1, LEAF_DARK, 1, -0.25)


def candle(bm, c, h=0.25, r=0.06):
    revolve(bm, [(r, 0), (r, h)], CREAM, c, 10)
    glow(ball2)(bm, (c[0], c[1], c[2] + h + 0.05), r * 0.5, GOLD, (1, 1, 1.8))


def witch_hat(bm, c, s=1.0):
    revolve(bm, [(0.26 * s, 0), (0.26 * s, 0.025 * s), (0.13 * s, 0.03 * s), (0.04 * s, 0.32 * s), (0.015 * s, 0.4 * s)], SLATE, c, 12)
    torus(bm, (c[0], c[1], c[2] + 0.06 * s), 0.13 * s, 0.025 * s, GOLD, 'Z', 12, 4)


def g_witch_ghost(bm):
    for sx in (-1, 1):
        x = sx * PX
        box(bm, (x, 0, 1.2), (0.34, 0.34, 2.4), DARKWOOD)
        tube(bm, [(x - sx * 0.05, -0.2, 0.2), (x + sx * 0.05, -0.2, 0.8), (x - sx * 0.05, -0.2, 1.4), (x + sx * 0.04, -0.2, 2.0)], [0.035] * 4, SLATE, 8)
        curl(bm, (x + sx * 0.2, 2.6), 0.22, 1.1, SLATE, sx, 0.0, 0.07)
        hang_lantern(bm, x + sx * 0.17, 2.1, -0.05, 0.55, 0.3, sx)
        candle(bm, (x + sx * 0.4, -0.35, 0), 0.32)
        candle(bm, (x + sx * 0.55, -0.25, 0), 0.2)
    beam(bm, (-2.1, 0, 2.45), (2.1, 0, 2.45), 0.32, 0.26, DARKWOOD)
    box(bm, (0, 0, 2.75), (0.22, 0.3, 0.5), DARKWOOD)
    for sgn in (-1, 1):
        pts = [(sgn * (0.2 + 1.5 * t / 8), -0.2, 2.42 - 0.18 * math.sin(math.pi * t / 8)) for t in range(9)]
        tube(bm, pts, [0.06] * 9, SLATE, 8)
    slab(bm, [(-0.38, 2.45), (0.38, 2.45), (0.38, 1.95), (0.2, 1.85), (0.0, 1.95), (-0.2, 1.85), (-0.38, 1.95), (-0.38, 2.2)], SLATE, 0.03, 0.01, center=(0.0, 2.15), at=(0, -0.22, 0))
    slab(bm, [(-0.12, 2.0), (0.12, 2.0), (0.14, 2.2), (0.08, 2.32), (0.0, 2.35), (-0.08, 2.32), (-0.14, 2.2), (-0.13, 2.1)], SNOW, 0.02, 0.008, center=(0.0, 2.17), at=(0, -0.25, 0))
    for dx in (-0.04, 0.04):
        ball2(bm, (dx, -0.27, 2.22), 0.018, IRON_BLACK)
    open_doors(bm, PX - 0.17, 1.0, WOOD, 'slats', 72, 0.12)
    f_jack(bm, (-PX - 0.5, -0.45, 0.25), 0.27, 320)
    witch_hat(bm, (-PX - 0.5, -0.45, 0.47), 1.0)


# ---------------- the rest ----------------
def g_blossom_heart(bm):
    for sx in (-1, 1):
        x = sx * PX
        box(bm, (x, 0, 1.0), (0.34, 0.34, 2.0), CREAM)
        hang_lantern(bm, x - sx * 0.17, 1.85, -0.05, 0.55, 0.26, -sx)
    arch = [(PX * math.cos(math.pi * i / 14), 0, 2.0 + 0.7 * math.sin(math.pi * i / 14)) for i in range(15)]
    band(bm, arch, 0.36, 0.24, CREAM)
    rnd = random.Random(400)
    path = arch + [(sx * PX, 0, z) for sx in (-1, 1) for z in (0.3, 0.7, 1.1, 1.5)]
    for i, p in enumerate(path):
        ball2(bm, (p[0], -0.12, p[2] + 0.05), 0.15, LEAF if i % 3 else LEAF_DARK, (1.2, 0.8, 1), 1, 0.15, 410 + i)
        flat_flower(bm, (p[0] + rnd.uniform(-0.1, 0.1), -0.27, p[2] + rnd.uniform(0.0, 0.15)), 0.1, PINK_SOFT if i % 3 else HOT_PINK)
        if i < len(arch):
            flat_flower(bm, (p[0] + rnd.uniform(-0.1, 0.1), -0.2, p[2] + 0.22), 0.09, BUBBLE)
    open_doors(bm, PX - 0.17, 1.0, CREAM, 'pickets', 72, 0.12, heart_col=XRED)
    for sx in (-1, 1):
        grass(bm, (sx * PX, -0.25, 0), 6, 430 + (sx > 0), 0.24)


def bull_skull(bm, c, s=1.0):
    x, y, z = c
    slab(bm, [(x - 0.2 * s, z + 0.12 * s), (x - 0.1 * s, z + 0.2 * s), (x + 0.1 * s, z + 0.2 * s), (x + 0.2 * s, z + 0.12 * s),
              (x + 0.15 * s, z - 0.08 * s), (x + 0.09 * s, z - 0.25 * s), (x - 0.09 * s, z - 0.25 * s), (x - 0.15 * s, z - 0.08 * s)],
         CREAM, 0.16 * s, 0.05 * s, center=(x, z), at=(0, y, 0))
    for k in (-1, 1):
        slab(bm, ellipse_pts(0.05 * s, 0.045 * s, 10, (x + k * 0.08 * s, z + 0.03 * s)), DARKWOOD, 0.02, 0.008, at=(0, y - 0.11 * s, 0))
        slab(bm, ellipse_pts(0.025 * s, 0.02 * s, 8, (x + k * 0.04 * s, z - 0.2 * s)), DARKWOOD, 0.02, 0.008, at=(0, y - 0.11 * s, 0))
        pts = [(x + k * (0.18 + 0.4 * t / 6) * s, y, z + (0.12 + 0.35 * (t / 6) ** 2) * s) for t in range(7)]
        tube(bm, pts, [0.07 * s * (1 - 0.8 * t / 6) + 0.012 for t in range(7)], CREAM, 8)


def g_ranch_skull(bm):
    for sx in (-1, 1):
        x = sx * PX
        box(bm, (x, 0, 1.15), (0.36, 0.36, 2.3), WOOD, yaw=sx * 2)
        for z in (0.6, 0.66, 1.2, 1.26):
            box(bm, (x, 0, z), (0.39, 0.39, 0.04), ROPE)
        hang_lantern(bm, x - sx * 0.18, 1.95, -0.05, 0.55, 0.28, -sx)
        for z in (0.35, 1.9):
            bolt(bm, (x, -0.19, z), round_head=True)
    arch = arch_pts(-PX - 0.4, PX + 0.4, 2.2, 2.55, 0.0, 14)
    band(bm, arch, 0.36, 0.28, WOOD)
    for x in (-PX, PX):
        rope_x(bm, x, 2.25, 0.16, -0.2)
    bull_skull(bm, (0, -0.22, 2.58), 1.6)
    open_doors(bm, PX - 0.18, 1.05, WOOD, 'cross', 72, 0.0)
    grass(bm, (PX + 0.2, -0.25, 0), 5, 440, 0.22)
    grass(bm, (-PX - 0.2, -0.25, 0), 5, 441, 0.22)


def seagull(bm, c, sx=1):
    x, y, z = c
    ball2(bm, (x, y, z), 0.11, SNOW, (1.5, 0.9, 0.9), 1)
    ball2(bm, (x + sx * 0.13, y, z + 0.08), 0.07, SNOW, (1, 1, 1), 1)
    box(bm, (x + sx * 0.22, y, z + 0.07), (0.07, 0.03, 0.03), GOLD)
    slab(bm, ellipse_pts(0.12, 0.04, 10, (x - sx * 0.02, z + 0.04), sx * 10), GREYBLUE, 0.02, 0.008, at=(0, y - 0.09, 0))
    for k in (-0.04, 0.04):
        tube(bm, [(x + k, y, z - 0.08), (x + k, y, z - 0.14)], [0.012, 0.012], GOLD, 6)


def ship_wheel(bm, c, r=0.42):
    x, y, z = c
    t = bmesh.new()
    torus(t, (0, 0, 0), r, 0.04, WOOD, 'Z', 20, 8)
    torus(t, (0, 0, 0), r * 0.4, 0.03, WOOD, 'Z', 14, 8)
    for k in range(8):
        a = math.pi * k / 4
        beam(t, (0, 0, 0.005 * (k % 4)), ((r + 0.14) * math.cos(a), (r + 0.14) * math.sin(a), 0.005 * (k % 4)), 0.04, 0.04, WOOD)
        ball2(t, ((r + 0.16) * math.cos(a), (r + 0.16) * math.sin(a), 0), 0.035, WOOD)
    ball2(t, (0, 0, 0), 0.07, GOLD, (1, 1, 0.8))
    bmesh.ops.rotate(t, cent=Vector(), matrix=Matrix.Rotation(math.radians(90), 3, 'X'), verts=t.verts)
    bmesh.ops.translate(t, vec=Vector(c), verts=t.verts)
    merge(bm, t)


def anchor(bm, c, s=1.0, col=GOLD):
    x, y, z = c
    box(bm, (x, y, z), (0.05 * s, 0.04 * s, 0.5 * s), col)
    box(bm, (x, y, z + 0.17 * s), (0.22 * s, 0.05 * s, 0.04 * s), col)
    t = bmesh.new()
    torus(t, (0, 0, 0), 0.05 * s, 0.015 * s, col, 'Z', 10, 4)
    bmesh.ops.rotate(t, cent=Vector(), matrix=Matrix.Rotation(math.radians(90), 3, 'X'), verts=t.verts)
    bmesh.ops.translate(t, vec=Vector((x, y, z + 0.3 * s)), verts=t.verts)
    merge(bm, t)
    band(bm, [(x + 0.18 * s * math.cos(a), y, z - 0.08 * s + 0.18 * s * math.sin(a)) for a in [math.pi + math.pi * k / 10 for k in range(11)]], 0.048 * s, 0.05 * s, col)   # deeper than the shaft where they meet


def g_nautical(bm):
    for sx in (-1, 1):
        x = sx * PX
        box(bm, (x, 0, 1.15), (0.36, 0.36, 2.3), WOOD)
        for z in (0.5, 0.56, 1.7, 1.76):
            box(bm, (x, 0, z), (0.39, 0.39, 0.04), ROPE)
    beam(bm, (-2.15, 0, 2.35), (2.15, 0, 2.5), 0.34, 0.26, NAVY)
    beam(bm, (-2.15, -0.18, 2.35), (2.15, -0.18, 2.5), 0.02, 0.06, LIGHT_WOOD)
    for x in (-PX, PX):
        rope_x(bm, x, 2.38, 0.17, -0.21)
    ship_wheel(bm, (0, -0.05, 2.95))
    box(bm, (0, 0, 2.6), (0.12, 0.12, 0.2), WOOD)
    seagull(bm, (-1.0, -0.05, 2.6), 1)
    seagull(bm, (1.05, -0.05, 2.62), -1)
    anchor(bm, (-PX, -0.21, 1.15), 1.5)
    pts = [(-PX + 0.1 + (2 * PX - 0.2) * i / 10, -0.2, 2.22 - 0.25 * math.sin(math.pi * i / 10)) for i in range(11)]
    tube(bm, pts, [0.03] * 11, ROPE, 6)
    open_doors(bm, PX - 0.18, 1.0, NAVY, 'slats', 72, 0.0)
    for sx in (-1, 1):
        rock(bm, (sx * (PX + 0.3), -0.3, 0.05), 0.2, 450 + (sx > 0), SNOW)
        grass(bm, (sx * (PX + 0.1), -0.3, 0), 4, 452 + (sx > 0), 0.2)


def paper_lantern(bm, c, s=1.0):
    x, y, z = c
    tube(bm, [(x, y, z), (x, y, z - 0.08 * s)], [0.012, 0.012], IRON_BLACK, 6)
    revolve(bm, [(0.06 * s, -0.08 * s), (0.06 * s, -0.11 * s)], IRON_BLACK, (x, y, z), 10)
    glow(revolve)(bm, [(0.06 * s, -0.11 * s), (0.15 * s, -0.2 * s), (0.17 * s, -0.3 * s), (0.15 * s, -0.4 * s), (0.06 * s, -0.49 * s)], XRED, (x, y, z), 12)
    revolve(bm, [(0.06 * s, -0.49 * s), (0.06 * s, -0.53 * s)], IRON_BLACK, (x, y, z), 10)
    tube(bm, [(x, y, z - 0.53 * s), (x, y, z - 0.65 * s)], [0.02 * s, 0.005], GOLD, 6)


def g_torii(bm):
    for sx in (-1, 1):
        x = sx * PX
        revolve(bm, [(0.24, 0), (0.24, 0.12), (0.2, 0.14)], CREAM, (x, 0, 0), 12)
        revolve(bm, [(0.18, 0.12), (0.16, 2.55)], XRED, (x, 0, 0), 12)
        paper_lantern(bm, (x + sx * 0.4, -0.05, 2.0), 1.1)
        beam(bm, (x, 0, 2.05), (x + sx * 0.4, 0, 2.05), 0.04, 0.04, IRON_BLACK)
    box(bm, (0, 0, 2.05), (2 * PX + 0.6, 0.24, 0.18), XRED)
    box(bm, (0, 0, 2.48), (2 * PX + 0.9, 0.3, 0.2), XRED)
    box(bm, (0, 0, 2.27), (0.2, 0.16, 0.26), XRED)
    roof = [(x, 0, 2.66 + 0.18 * (abs(x) / 2.4) ** 3) for x in [-2.45 + 4.9 * i / 14 for i in range(15)]]
    band(bm, roof, 0.5, 0.2, SLATE)
    rnd = random.Random(460)
    for i in range(7):
        x = -1.5 + i * 0.5 + rnd.uniform(-0.08, 0.08)
        flat_flower(bm, (x, -0.27, 2.62 + rnd.uniform(-0.04, 0.08) + 0.18 * (abs(x) / 2.4) ** 3), 0.1, PINK_SOFT if i % 2 else BUBBLE)
    open_doors(bm, PX - 0.17, 0.95, XRED, 'slats', 72, 0.0)
    for sx in (-1, 1):
        grass(bm, (sx * PX, -0.3, 0), 5, 470 + (sx > 0), 0.2)


GATES2 = [
    ("Xmas_Bow", g_xmas_bow),
    ("Candy_Cane", g_candy_cane),
    ("Ginger_Lodge", g_ginger_lodge),
    ("Pumpkin_Bat", g_pumpkin_bat),
    ("Witch_Ghost", g_witch_ghost),
    ("Blossom_Heart", g_blossom_heart),
    ("Ranch_Skull", g_ranch_skull),
    ("Nautical", g_nautical),
    ("Torii", g_torii),
]


def build_gates2(only=None):
    root = bpy.data.collections.get("Gates") or bpy.data.collections.new("Gates")
    objs = []
    for row, (name, fn) in enumerate(GATES2):
        if only and name not in only:
            continue
        sub = bpy.data.collections.get("Gate_" + name) or bpy.data.collections.new("Gate_" + name)
        if sub.name not in [c.name for c in root.children]:
            root.children.link(sub)
        bm = bmesh.new()
        fn(bm)
        objs.append(finish_lamp(bm, "SM_Gate_" + name, sub, (row * 6.0, -78.0, 0)))
    return check_closed(objs)
