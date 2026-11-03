# Farm entrance gates (sheet 49) in the NewLua pack style (gradient atlas, quads, closed shells).
#   exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/gates.py")).read())
#   build_gates()                  # all, or build_gates(["Name_Sign"])
# SM_Gate_<Name>: pivot at the CENTRE of the opening on the ground, the gate spans x -GATE_HALF ..
# GATE_HALF, front -Y (the side visitors see). In gab it is scaled by GateScale like the fences, and
# the base's fence runs end at its sides. Name_Sign keeps its sign blank: the game writes the
# owner's farm name on it (a billboard in front of SIGN_CENTER).
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/fences2.py")).read())

GATE_HALF = 2.0                 # half width incl. pillars (m, before the game's x1.5)
PX = 1.7                        # pillar centre x
SIGN_CENTER = (0.0, -0.1, 1.95)  # Name_Sign board front centre
STRAW = c0(23, 0.86, 0.9)
BARN_RED = c0(6, 0.88, 0.95)
ROOF_RED = c0(14, 0.9, 0.96)
PETAL_W = c0(18, 0.85, 0.87)


def hang_lantern(bm, x, z, y=0.0, s=0.5, arm=0.32, dirx=1):
    beam(bm, (x, y, z), (x + dirx * arm, y, z), 0.035, 0.035, IRON)
    beam(bm, (x, y, z - 0.18), (x + dirx * arm * 0.7, y, z), 0.025, 0.025, IRON)
    lantern(bm, (x + dirx * (arm - 0.02), y, z), s)


def rope_x(bm, x, z, w, y):
    """Rope lashing: an X of two thin rope beams on the front of a joint."""
    beam(bm, (x - w, y, z - w), (x + w, y, z + w), 0.04, 0.05, ROPE)
    beam(bm, (x - w, y + 0.012, z + w), (x + w, y + 0.012, z - w), 0.034, 0.05, ROPE)   # behind the first: they cross


def base_flowers(bm, x, seed, col=PETAL_W, n=3):
    rnd = random.Random(seed)
    grass(bm, (x, -0.25, 0), 6, seed, 0.26)
    for i in range(n):
        flat_flower(bm, (x + rnd.uniform(-0.3, 0.3), -0.32, 0.08 + rnd.uniform(0, 0.08)), 0.06, col)


def leaf_cover(bm, pts, seed, col=LEAF, r=0.13, step=1):
    """Leafy clumps sitting along a path (vine-covered beams / arches)."""
    rnd = random.Random(seed)
    for i, p in enumerate(pts[::step]):
        ball2(bm, (p[0] + rnd.uniform(-0.04, 0.04), p[1] + rnd.uniform(-0.05, 0.05), p[2] + rnd.uniform(0.0, 0.08)),
              r * rnd.uniform(0.8, 1.15), col if i % 3 else LEAF_DARK, (1.2, 1, 0.8), 1, 0.12, seed + i)


# ---------------- 1. Name sign (the cow sign without the cow: the player's farm name goes on it) -------------
def g_name_sign(bm):
    for sx in (-1, 1):
        x = sx * PX
        stone_blocks_at(bm, x, 0.0, 0.55, 0.52, LIGHT_STONE, 3 + (sx > 0), 2)
        tube(bm, [(x, 0, 0.5), (x, 0, 1.6), (x + sx * 0.02, 0, 2.6)], [0.17, 0.16, 0.15], WOOD, 10, 0.5, 2.6)
        rope_x(bm, x, 2.38, 0.14, -0.17)
        hang_lantern(bm, x + sx * 0.15, 2.0, 0.0, 0.5, 0.3, sx)
        ivy(bm, x - sx * 0.05, -0.15, 0.7, 2.3, 11 + (sx > 0), 7, 0.06)
        base_flowers(bm, x, 20 + (sx > 0))
    beam_pts = [(-2.05 + 4.1 * i / 12, 0.0, 2.42 + 0.08 * math.sin(math.pi * i / 12)) for i in range(13)]
    tube(bm, beam_pts, [0.16] * len(beam_pts), WOOD, 10)
    vine = [(p[0], -0.12, p[2] + 0.1 * math.sin(i * 1.1)) for i, p in enumerate(beam_pts)]
    tube(bm, vine, [0.02] * len(vine), LEAF_DARK, 6)
    for i, p in enumerate(vine[1::2]):
        leaf(bm, (p[0], p[1] - 0.02, p[2]), random.Random(i).uniform(-160, -20), 0.16, 0.1, 30, LEAF, droop=-0.2)
    # the name board: wood plank board with a darker frame, hung on two ropes
    cx, cy, cz = SIGN_CENTER
    box(bm, (cx, cy + 0.06, cz), (1.9, 0.08, 0.62), RUSTIC)            # board  y -0.08..0
    for dz in (-0.33, 0.33):
        box(bm, (cx, cy + 0.05, cz + dz), (2.0, 0.14, 0.07), DARKWOOD)   # top / bottom frame y -0.12..0.02
    for dx in (-0.98, 0.98):
        box(bm, (cx + dx, cy + 0.0515, cz), (0.07, 0.113, 0.72), DARKWOOD)   # side frame y -0.105..0.008
        tube(bm, [(cx + dx * 0.8, cy + 0.06, cz + 0.36), (cx + dx * 0.8, cy + 0.06, 2.42)], [0.018, 0.018], ROPE, 6)


def stone_blocks_at(bm, x, z0, z1, w, col, seed, rows):
    t = bmesh.new()
    stone_blocks(t, z0, z1, w, col, seed, rows)
    bmesh.ops.translate(t, vec=Vector((x, 0, 0)), verts=t.verts)
    merge(bm, t)


# ---------------- 2. Hearts & bows ----------------
def g_heart_bows(bm):
    for sx in (-1, 1):
        x = sx * PX
        t = bmesh.new()
        sq_post(t, 2.3, CREAM, 0.34)
        bmesh.ops.translate(t, vec=Vector((x, 0, 0)), verts=t.verts)
        merge(bm, t)
        bow(bm, (x, -0.22, 2.15), 2.0, HOT_PINK)
        hang_lantern(bm, x - sx * 0.17, 2.05, 0.0, 0.5, 0.3, -sx)
        ivy(bm, x, -0.19, 0.1, 1.7, 30 + (sx > 0), 7, 0.08)
        for k in range(4):
            flat_flower(bm, (x + random.Random(k + sx).uniform(-0.08, 0.08), -0.22, 0.3 + k * 0.38), 0.06, PINK_SOFT)
        heart(bm, (x + sx * 0.45, -0.1, 0.35), 0.24, HOT_PINK, 0.06)
        grass(bm, (x, -0.22, 0), 6, 33 + (sx > 0), 0.24)
    band(bm, arch_pts(-PX - 0.2, PX + 0.2, 2.3, 2.75), 0.36, 0.24, CREAM)
    roof = arch_pts(-PX - 0.45, PX + 0.45, 2.42, 2.9)
    band(bm, [(p[0], p[1], p[2] + 0.06) for p in roof], 0.62, 0.12, PINK_SOFT)
    for i in range(0, 15, 2):   # scalloped edge under the roof, front
        p = roof[i]
        slab(bm, ellipse_pts(0.17, 0.09, 12, (p[0], p[2] - 0.02)), PINK, 0.05, 0.015, at=(0, -0.3, 0))
    hc = (0.0, 3.08)
    holed(bm, ellipse_pts(0.36, 0.3, 24, hc), heart_pts(0.36, (0.0, 3.06), 32), hc, 0.16, CREAM)


# ---------------- 3. Red barn ----------------
def sunflower(bm, x, y, h, s=1.0):
    tube(bm, [(x, y, 0), (x, y, h)], [0.02, 0.02], LEAF_DARK, 6)
    for k in (-1, 1):
        slab(bm, ellipse_pts(0.1, 0.04, 10, (x + k * 0.09, h * 0.5), k * 25), LEAF, 0.02, 0.01, at=(0, y, 0))
    slab(bm, polar(lambda a: 0.15 * s * (0.75 + 0.25 * math.cos(10 * a)), 40, (x, h)), GOLD, 0.03, 0.01, at=(0, y, 0))
    ball2(bm, (x, y - 0.03, h), 0.07 * s, DARKWOOD, (1, 0.5, 1))


def barrel(bm, x, y, h=0.55, r=0.24):
    revolve(bm, [(r * 0.85, 0), (r, h * 0.3), (r, h * 0.7), (r * 0.85, h)], WOOD, (x, y, 0), 12)
    for z in (h * 0.18, h * 0.82):
        torus(bm, (x, y, z), r * 0.95, 0.018, IRON, 'Z', 14, 4)


def hay(bm, c, size=(0.55, 0.35, 0.3)):
    box(bm, c, size, STRAW)
    for dx in (-0.15, 0.15):
        box(bm, (c[0] + dx * size[0] / 0.55, c[1] - size[1] / 2, c[2]), (0.03, 0.02, size[2] + 0.01), ROPE)


def g_red_barn(bm):
    for sx in (-1, 1):
        x = sx * PX
        box(bm, (x, 0, 1.1), (0.38, 0.38, 2.2), BARN_RED)
        for cx in (-1, 1):   # cream corner trims
            box(bm, (x + cx * 0.18, -0.18, 1.09), (0.05, 0.05, 2.18), CREAM)
        hang_lantern(bm, x - sx * 0.19, 1.95, 0.0, 0.5, 0.28, -sx)
    box(bm, (0, 0, 2.27), (2 * PX + 0.5, 0.42, 0.16), CREAM)
    gable = [(-2.0, 2.35), (0.0, 2.35), (2.0, 2.35), (1.92, 2.75), (1.25, 3.2), (0.0, 3.5), (-1.25, 3.2), (-1.92, 2.75)]
    slab(bm, gable, BARN_RED, 0.34, 0.0, 0.6, center=(0.0, 2.8))
    for sgn in (-1, 1):   # gambrel roof slabs + cream gable trim
        pts = [(sgn * 2.15, 0, 2.62), (sgn * 1.32, 0, 3.27), (0.0, 0, 3.58)]
        band(bm, pts, 0.6 + 0.012 * (sgn > 0), 0.1, ROOF_RED)   # the two halves meet: own depths
        band(bm, [(p[0] * 0.97, -0.18 - 0.006 * (sgn > 0), p[2] - 0.06) for p in pts], 0.06, 0.08, CREAM)
    box(bm, (0, -0.195, 2.82), (0.5, 0.04, 0.42), CREAM)
    box(bm, (0, -0.2125, 2.82), (0.42, 0.025, 0.34), BARN_RED)
    beam(bm, (-0.19, -0.235, 2.67), (0.19, -0.235, 2.97), 0.03, 0.05, CREAM)
    beam(bm, (-0.19, -0.243, 2.97), (0.19, -0.243, 2.67), 0.03, 0.05, CREAM)
    for sgn in (-1, 1):   # knee braces
        beam(bm, (sgn * (PX - 0.19), -0.1, 1.85), (sgn * (PX - 0.55), -0.1, 2.2), 0.08, 0.08, CREAM)
    tube(bm, [(0, 0, 3.58), (0, 0, 4.0)], [0.025, 0.025], IRON, 6)
    beam(bm, (-0.22, 0, 3.92), (0.22, 0, 3.92), 0.025, 0.025, IRON)
    rooster = [(-0.12, 4.0), (0.02, 4.0), (0.14, 4.05), (0.17, 4.18), (0.1, 4.28), (0.06, 4.18), (-0.04, 4.12), (-0.16, 4.2), (-0.2, 4.1), (-0.16, 4.04)]
    slab(bm, rooster, GOLD, 0.04, 0.01, center=(0.0, 4.1))
    hay(bm, (-PX - 0.15, -0.35, 0.15))
    hay(bm, (-PX - 0.15, -0.35, 0.45), (0.45, 0.3, 0.28))
    tube(bm, [(-PX + 0.35, -0.32, 0), (-PX + 0.35, -0.32, 0.95)], [0.018, 0.018], WOOD, 6)
    for dx in (-0.06, 0, 0.06):
        tube(bm, [(-PX + 0.35 + dx, -0.32, 0.95), (-PX + 0.35 + dx, -0.32, 1.15)], [0.01, 0.006], IRON, 6)
    box(bm, (-PX + 0.35, -0.32, 0.95), (0.16, 0.02, 0.025), IRON)
    sunflower(bm, PX - 0.05, -0.35, 0.8)
    sunflower(bm, PX + 0.22, -0.4, 0.62, 0.85)
    barrel(bm, PX + 0.4, -0.15)
    grass(bm, (PX, -0.3, 0), 5, 41, 0.22)
    grass(bm, (-PX + 0.4, -0.3, 0), 4, 42, 0.2)


# ---------------- 4. Wisteria stone arch ----------------
def g_wisteria(bm):
    rnd = random.Random(51)
    for sx in (-1, 1):
        x = sx * PX
        for r in range(6):
            box(bm, (x + rnd.uniform(-0.02, 0.02), 0, 0.15 + r * 0.3), (0.5 - (r % 2) * 0.04, 0.48, 0.28), LIGHT_STONE, yaw=rnd.uniform(-3, 3))
        hang_lantern(bm, x + sx * 0.25, 1.55, 0.0, 0.5, 0.28, sx)
        base_flowers(bm, x, 52 + (sx > 0))
    rx, rz, cz = PX, 1.0, 1.8
    n = 11
    pts = []
    for i in range(n):
        a0, a1 = math.pi * i / n, math.pi * (i + 1) / n
        p0 = (rx * math.cos(a0), 0, cz + rz * math.sin(a0))
        p1 = (rx * math.cos(a1), 0, cz + rz * math.sin(a1))
        d = (Vector(p1) - Vector(p0)).normalized() * 0.008   # a hair apart: voussoirs never share faces
        beam(bm, tuple(Vector(p0) + d), tuple(Vector(p1) - d), 0.48 - 0.012 * (i % 2), 0.32, LIGHT_STONE)   # alternate depths
        pts.append(((p0[0] + p1[0]) / 2, 0, (p0[2] + p1[2]) / 2))
    top = [(p[0], p[1], p[2] + 0.16) for p in pts]
    leaf_cover(bm, top, 53, LEAF, 0.16)
    for i, p in enumerate(pts[1:-1]):
        for k in range(6 - i % 2):
                ball2(bm, (p[0], -0.27, p[2] - 0.2 - k * 0.1), 0.09 - k * 0.01, WISTERIA, (1, 1, 1.15), 1, 0.08, 60 + i * 7 + k)


# ---------------- 5. Flower trellis ----------------
def g_trellis(bm):
    for sx in (-1, 1):
        x = sx * PX
        t = bmesh.new()
        sq_post(t, 2.2, CREAM, 0.2)
        bmesh.ops.translate(t, vec=Vector((x, 0, 0)), verts=t.verts)
        merge(bm, t)
        xa, xb = (x + 0.1, x + 0.62) if sx > 0 else (x - 0.62, x - 0.1)
        lattice(bm, xa, xb, 0.12, 0.9, CREAM, 0.18, 0.04, 0.025)
        box(bm, ((xa + xb) / 2, 0, 0.92), (xb - xa, 0.06, 0.06), CREAM)
        box(bm, ((xa + xb) / 2, 0, 0.1), (xb - xa, 0.06, 0.06), CREAM)
        box(bm, (sx * (PX + 0.66), 0, 0.5), (0.1, 0.1, 1.0), CREAM)
        ivy(bm, x, -0.12, 0.2, 2.1, 70 + (sx > 0), 6, 0.06)
        for k in range(3):
            flat_flower(bm, (x + 0.03 * k, -0.14, 0.5 + k * 0.55), 0.07, PINK_SOFT)
        grass(bm, (x + sx * 0.4, -0.15, 0), 6, 72 + (sx > 0), 0.24)
    arch = arch_pts(-PX, PX, 2.2, 3.0, 0.0, 16)
    band(bm, arch, 0.14, 0.14, CREAM)
    leaf_cover(bm, [(p[0], -0.03, p[2] + 0.04) for p in arch], 74, LEAF, 0.13, 1)
    rnd = random.Random(75)
    for i, p in enumerate(arch[1:-1]):
        flat_flower(bm, (p[0], -0.15, p[2] + rnd.uniform(0.0, 0.12)), 0.08 + 0.02 * (i % 2), PINK_SOFT if i % 3 else HOT_PINK)


# ---------------- 6. Paw sign + wagon wheel ----------------
def wheel(bm, c, r=0.38):
    x, y, z = c
    t = bmesh.new()
    torus(t, (0, 0, 0), r, 0.04, WOOD, 'Z', 20, 8)   # 8 sides: no flat top facet for a spoke to lie on
    for k in range(8):
        a = math.pi * k / 4
        beam(t, (0, 0, 0.005 * (k % 4)), (r * math.cos(a), r * math.sin(a), 0.005 * (k % 4)), 0.035, 0.035, WOOD)   # crossing spokes at their own depths
    ball2(t, (0, 0, 0), 0.07, DARKWOOD, (1, 1, 0.7))
    bmesh.ops.rotate(t, cent=Vector(), matrix=Matrix.Rotation(math.radians(90), 3, 'X'), verts=t.verts)
    bmesh.ops.translate(t, vec=Vector(c), verts=t.verts)
    merge(bm, t)


def g_paw_wagon(bm):
    for sx in (-1, 1):
        x = sx * PX
        box(bm, (x, 0, 1.25), (0.3, 0.3, 2.5), WOOD, yaw=sx * 2)
        rope_x(bm, x, 2.3, 0.13, -0.16)
        for z in (2.12, 2.17):
            box(bm, (x, 0, z), (0.345, 0.345, 0.03), ROPE)
        hang_lantern(bm, x + sx * 0.15, 1.95, 0.0, 0.5, 0.3, sx)
    beam(bm, (-2.15, 0, 2.4), (2.15, 0, 2.4), 0.3, 0.24, WOOD)
    for x in (-1.1, 0.0, 1.1):
        rope_x(bm, x, 2.38, 0.11, -0.16)
    box(bm, (0, -0.06, 1.9), (1.0, 0.07, 0.48), RUSTIC)
    box(bm, (0, -0.05, 1.9), (1.08, 0.08, 0.56), DARKWOOD)
    for dx in (-0.4, 0.4):
        tube(bm, [(dx, -0.06, 2.14), (dx, -0.06, 2.27)], [0.016, 0.016], ROPE, 6)
    slab(bm, ellipse_pts(0.09, 0.075, 12, (0.0, 1.86)), DARKWOOD, 0.02, 0.01, at=(0, -0.11, 0))
    for dx, dz in ((-0.11, 1.95), (-0.04, 2.0), (0.04, 2.0), (0.11, 1.95)):
        slab(bm, ellipse_pts(0.03, 0.037, 10, (dx, dz)), DARKWOOD, 0.02, 0.008, at=(0, -0.11, 0))
    wheel(bm, (PX + 0.15, -0.32, 0.4))
    box(bm, (-PX - 0.25, -0.05, 0.35), (0.08, 0.08, 0.7), WOOD)
    box(bm, (-PX + 0.4, -0.05, 0.35), (0.08, 0.08, 0.7), WOOD)
    box(bm, (-PX + 0.07, -0.05, 0.55), (0.75, 0.06, 0.08), WOOD)
    for i in range(4):   # gingham cloth: checker squares hung over the rail
        for j in range(3):
            box(bm, (-PX - 0.12 + i * 0.1, -0.1, 0.52 - j * 0.1), (0.1, 0.02, 0.1), HOT_PINK if (i + j) % 2 else CREAM)
    base_flowers(bm, -PX + 0.3, 81)
    grass(bm, (PX - 0.2, -0.3, 0), 5, 82, 0.22)


# ---------------- 7. Ribbons + bunting ----------------
def rosette(bm, c, col):
    x, y, z = c
    slab(bm, polar(lambda a: 0.17 * (0.85 + 0.15 * math.cos(12 * a)), 24, (x, z)), col, 0.04, 0.015, at=(0, y, 0))
    slab(bm, ellipse_pts(0.08, 0.08, 12, (x, z)), CREAM, 0.03, 0.01, at=(0, y - 0.03, 0))
    for k in (-1, 1):
        slab(bm, [(x + k * 0.02, z - 0.08), (x + k * 0.1, z - 0.08), (x + k * 0.13, z - 0.42), (x + k * 0.07, z - 0.36)], col, 0.025, 0.008, at=(0, y + 0.01, 0))


def pinwheel(bm, x, y, h):
    tube(bm, [(x, y, 0), (x, y, h)], [0.018, 0.018], WOOD, 6)
    for k in range(4):
        a = math.pi / 2 * k
        pts = [(x, h), (x + 0.2 * math.cos(a), h + 0.2 * math.sin(a)), (x + 0.2 * math.cos(a + 0.9), h + 0.2 * math.sin(a + 0.9)), (x + 0.06 * math.cos(a + 1.2), h + 0.06 * math.sin(a + 1.2))]
        slab(bm, pts, PINK_SOFT if k % 2 else STRAW, 0.02, 0.005, at=(0, y - 0.04, 0))
    ball2(bm, (x, y - 0.07, h), 0.03, HOT_PINK)


def g_bunting(bm):
    for sx in (-1, 1):
        x = sx * PX
        box(bm, (x, 0, 1.2), (0.32, 0.32, 2.4), WOOD, yaw=sx * 2)
        rosette(bm, (x, -0.2, 1.95), HOT_PINK if sx < 0 else PINK)
    arch = arch_pts(-PX - 0.35, PX + 0.35, 2.3, 2.75, 0.0, 16)
    band(bm, arch, 0.36, 0.28, WOOD)
    band(bm, [(p[0], -0.19, p[2]) for p in arch[2:-2]], 0.02, 0.05, RUSTIC)
    s = [(-PX + 0.2 + (2 * PX - 0.4) * i / 16, -0.22, 2.3 - 0.28 * math.sin(math.pi * i / 16)) for i in range(17)]
    tube(bm, s, [0.01] * len(s), CREAM, 6)
    cols = [PINK_SOFT, CREAM, STRAW, HOT_PINK]
    for i in range(1, 16, 2):
        x, y, z = s[i]
        slab(bm, [(x - 0.11, z), (x + 0.11, z), (x + 0.01, z - 0.26), (x - 0.05, z - 0.13)], cols[(i // 2) % 4], 0.02, 0.005, at=(0, y - 0.01, 0))
    hay(bm, (-PX - 0.1, -0.3, 0.16), (0.6, 0.4, 0.32))
    hay(bm, (-PX + 0.1, -0.3, 0.46), (0.45, 0.32, 0.28))
    pinwheel(bm, -PX - 0.45, -0.3, 0.95)
    barrel(bm, PX + 0.1, -0.35, 0.5, 0.26)
    for k in range(5):
        a = 2 * math.pi * k / 5
        ball2(bm, (PX + 0.1 + 0.13 * math.cos(a), -0.35 + 0.13 * math.sin(a), 0.6), 0.1, BUBBLE if k % 2 else HOT_PINK, (1, 1, 0.8), 1, 0.12, 90 + k)
    leaf_cover(bm, [(PX + 0.1, -0.35, 0.5)], 95, LEAF, 0.18)
    grass(bm, (-PX, -0.25, 0), 5, 96, 0.22)


# ---------------- 8. Blossom tree arch ----------------
def g_tree_arch(bm):
    for sx in (-1, 1):
        x = sx * PX
        pts = [(x + sx * 0.05, 0, 0), (x, 0, 0.6), (x - sx * 0.05, 0, 1.3), (x - sx * 0.3, 0, 2.0), (x - sx * 0.85, 0, 2.6), (x - sx * 1.5, 0, 2.85), (x - sx * 1.75, 0, 2.88)]
        tube(bm, pts, [0.26, 0.21, 0.19, 0.17, 0.15, 0.12, 0.1], BARK, 10, 0, 2.9)
        for k in range(3):   # roots
            a = math.radians(-60 + k * 60) * (1 if sx > 0 else -1) + (0 if sx > 0 else math.pi)
            tube(bm, [(x, 0, 0.25), (x + 0.35 * math.cos(a), 0.3 * math.sin(a), 0.04)], [0.1, 0.04], BARK, 8)
        hang_lantern(bm, x - sx * 0.12, 2.0, -0.05, 0.5, 0.3, -sx)
        mushroom(bm, (x + sx * 0.35, -0.3, 0), 1.2, 101 + (sx > 0))
        mushroom(bm, (x + sx * 0.12, -0.4, 0), 0.8, 103 + (sx > 0))
        base_flowers(bm, x + sx * 0.1, 105 + (sx > 0))
    canopy = [(1.85 * math.cos(math.pi * i / 14), 0.0, 2.25 + 0.75 * math.sin(math.pi * i / 14)) for i in range(15)]
    rnd = random.Random(107)
    for i, p in enumerate(canopy[1:-1]):
        for dy in (-0.15, 0.15):
            blob(bm, (p[0] + rnd.uniform(-0.08, 0.08), dy, p[2] + 0.12), rnd.uniform(0.3, 0.36), LEAF, 110 + i * 2 + (dy > 0))
    for i, p in enumerate(canopy[1:-1]):
        for k in range(2):
            flat_flower(bm, (p[0] + rnd.uniform(-0.18, 0.18), -0.45, p[2] + rnd.uniform(-0.05, 0.35)), 0.07, PETAL_W if (i + k) % 3 else PINK_SOFT)


# ---------------- 9. Windmill towers ----------------
def g_windmill(bm):
    for sx in (-1, 1):
        x = sx * PX
        revolve(bm, [(0.42, 0), (0.4, 0.15), (0.36, 2.0), (0.38, 2.05)], CREAM, (x, 0, 0), 14)
        revolve(bm, [(0.42, 2.0), (0.42, 2.18), (0.34, 2.38), (0.2, 2.52), (0.04, 2.57)], BARN_RED, (x, 0, 0), 14)
        box(bm, (x, -0.33, 0.45), (0.34, 0.08, 0.7), WOOD)
        beam(bm, (x - 0.14, -0.38, 0.15), (x + 0.14, -0.38, 0.75), 0.03, 0.05, CREAM)
        beam(bm, (x - 0.14, -0.388, 0.75), (x + 0.14, -0.388, 0.15), 0.03, 0.05, CREAM)
        beam(bm, (x - 0.13, -0.38, 1.35), (x + 0.13, -0.38, 1.7), 0.03, 0.05, PINK)
        beam(bm, (x - 0.13, -0.388, 1.7), (x + 0.13, -0.388, 1.35), 0.03, 0.05, PINK)
        box(bm, (x, 0, 2.035), (0.86, 0.86, 0.06), PINK)
        for k in range(5):   # wheat
            wx = x + sx * (0.45 + 0.06 * k)
            tube(bm, [(wx, -0.3, 0), (wx + 0.03 * (k - 2), -0.3, 0.7 + 0.05 * k)], [0.012, 0.01], STRAW, 6)
            ball2(bm, (wx + 0.03 * (k - 2), -0.3, 0.78 + 0.05 * k), 0.04, STRAW, (0.8, 0.8, 2.2), 1, 0.05, k)
        grass(bm, (x + sx * 0.45, -0.3, 0), 4, 120 + (sx > 0), 0.2)
    arch = arch_pts(-PX + 0.3, PX - 0.3, 1.95, 2.45, 0.0, 14)
    band(bm, arch, 0.4, 0.26, WOOD)
    band(bm, [(p[0], -0.21, p[2]) for p in arch[1:-1]], 0.03, 0.06, CREAM)
    box(bm, (0, 0, 2.95), (0.5, 0.45, 0.9), CREAM)
    box(bm, (0, 0, 3.48), (0.62, 0.55, 0.16), BARN_RED, taper=0.55)
    hub = (0.0, -0.3, 3.2)
    ball2(bm, hub, 0.07, BARN_RED)
    for k in range(4):
        a = math.pi / 4 + math.pi / 2 * k
        hub = (0.0, -0.3 - 0.006 * k, 3.2)   # every arm (and its blade) at its own depth
        tip = (hub[0] + 0.85 * math.cos(a), hub[1], hub[2] + 0.85 * math.sin(a))
        beam(bm, hub, tip, 0.04, 0.05, WOOD)
        n = Vector((-math.sin(a), 0, math.cos(a)))
        mid = Vector(hub) + (Vector(tip) - Vector(hub)) * 0.6 + n * 0.12
        beam(bm, tuple(Vector(hub) + (Vector(tip) - Vector(hub)) * 0.25 + n * 0.14), tuple(Vector(tip) + n * 0.14), 0.02, 0.22, CREAM)   # clear of the arm
        beam(bm, tuple(mid - n * 0.11), tuple(mid + n * 0.11), 0.03, 0.03, WOOD)


GATES = [
    ("Name_Sign", g_name_sign),
    ("Ribbon_Bunting", g_bunting),
    ("Flower_Trellis", g_trellis),
    ("Paw_Wagon", g_paw_wagon),
    ("Heart_Bows", g_heart_bows),
    ("Red_Barn", g_red_barn),
    ("Wisteria_Stone", g_wisteria),
    ("Tree_Arch", g_tree_arch),
    ("Windmill", g_windmill),
]


def build_gates(only=None):
    root = bpy.data.collections.get("Gates") or bpy.data.collections.new("Gates")
    if root.name not in [c.name for c in bpy.context.scene.collection.children]:
        bpy.context.scene.collection.children.link(root)
    objs = []
    for row, (name, fn) in enumerate(GATES):
        if only and name not in only:
            continue
        sub = bpy.data.collections.get("Gate_" + name) or bpy.data.collections.new("Gate_" + name)
        if sub.name not in [c.name for c in root.children]:
            root.children.link(sub)
        bm = bmesh.new()
        fn(bm)
        objs.append(finish_lamp(bm, "SM_Gate_" + name, sub, (row * 6.0, -70.0, 0)))
    return check_closed(objs)
