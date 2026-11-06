# gab house decorations (Dante's 4 decor sheets, 2026-10-29): Bedroom / Bathroom / Living Room /
# Kitchen, 12 items each, cash-unlocked furniture for the barn house (Component/house.verse).
# Cosy Animal-Crossing look: warm wood, cream, sage green, leafy plants. Kept simple but tidy: rounded
# boxes (bevelled, quads), lathed round parts (quads + a pole at each end), rings, capsules, leaves.
# ONE material (M_GradientTexture = the gradient atlas, GradientTexture_v3); each part is UV'd into
# one atlas column (S(row, col, t0, t1)). Every item: pivot at the bottom centre, front -Y.
# Collections: Decor > Decor_Bedroom / Decor_Bathroom / Decor_LivingRoom / Decor_Kitchen.
#   exec(open(r"<skills>/blender-game-props/decor.py").read())
#   build_decor()                 # every item; build_decor(["Bedroom"]) for one area
#   render_decor_previews(dir)    # one framed PNG per item (dir/<area>/<name>.png)
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix, Euler

_ROWS = {"r1": (6, 316), "r2": (330, 630), "r3": (712, 1003), "r4": (1040, 1331)}


def S(row, col, t0=0.0, t1=1.0):
    """(u, v at t=0, v at t=1) of one atlas gradient column."""
    y0, y1 = _ROWS[row]
    v = lambda t: 1 - (y0 + (y1 - y0) * t) / 2048
    return ((28 + 57 * col) / 2048, v(t0), v(t1))


WOOD = S("r2", 1, 0.3, 0.55)
WOOD_L = S("r2", 1, 0.1, 0.3)
WOOD_D = S("r2", 1, 0.6, 0.85)
CREAM = S("r2", 9, 0.15, 0.35)   # cols 6-9 of row 2 start at y 358: keep t >= 0.12
CREAM_D = S("r2", 9, 0.45, 0.7)
SAGE = S("r1", 0, 0.42, 0.56)
SAGE_D = S("r1", 28, 0.25, 0.55)
LEAF = S("r3", 4, 0.0, 0.55)
LEAF_L = S("r1", 1, 0.2, 0.6)
LEAF_D = S("r1", 13, 0.45, 0.9)
WHITE = S("r4", 4, 0.0, 0.12)
YELLOW = S("r4", 0, 0.0, 0.45)
GOLD = S("r4", 22, 0.1, 0.5)
ORANGE = S("r4", 6, 0.05, 0.4)
GLASS = S("r4", 19, 0.15, 0.7)
GLASS_G = S("r1", 0, 0.5, 0.62)
BLACK = S("r2", 7, 0.2, 0.8)
GREY = S("r2", 6, 0.15, 0.45)
METAL = S("r1", 2, 0.0, 0.55)
TERRA = S("r1", 26, 0.35, 0.65)
RED = S("r1", 6, 0.3, 0.75)
PINK = S("r1", 27, 0.0, 0.45)
BLUE = S("r1", 25, 0.0, 0.6)
PURPLE = S("r4", 15, 0.2, 0.7)
BROWN = S("r2", 0, 0.0, 0.6)
SOIL = S("r2", 0, 0.5, 0.9)
WICKER = S("r3", 6, 0.05, 0.6)
WICKER_D = S("r3", 6, 0.55, 0.95)
FLAME = S("r4", 8, 0.0, 0.6)
TOAST = S("r2", 1, 0.0, 0.2)


# ---------- part builders: each makes its own bmesh, UVs it, turns / moves it, merges it ----------
def _uv(b, s, axis=2):
    uvl = b.loops.layers.uv.verify()
    vals = [v.co[axis] for v in b.verts]
    z0, z1 = min(vals), max(vals)
    u, v0, v1 = s
    for f in b.faces:
        for l in f.loops:
            t = (l.vert.co[axis] - z0) / max(z1 - z0, 1e-6)
            l[uvl].uv = (u, v0 + (v1 - v0) * t)


def _merge(bm, b, rot=None, at=(0, 0, 0)):
    if rot:
        bmesh.ops.rotate(b, verts=b.verts, cent=(0, 0, 0), matrix=Euler([math.radians(a) for a in rot], 'XYZ').to_matrix())
    bmesh.ops.translate(b, verts=b.verts, vec=Vector(at))
    me = bpy.data.meshes.new("_decor_part")
    b.to_mesh(me)
    b.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)


def rbox(bm, c, size, s, r=None, rot=None):
    """A box with rounded edges (2-segment bevel: quads, smooth bevels, flat faces)."""
    hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
    if r is None:
        r = min(hx, hy, hz) * 0.45
    r = max(0.0, min(r, hx * 0.95, hy * 0.95, hz * 0.95))
    b = bmesh.new()
    bmesh.ops.create_cube(b, size=1.0)
    for v in b.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    for f in b.faces:
        f.smooth = False
    if r > 0.0005:
        res = bmesh.ops.bevel(b, geom=list(b.edges), offset=r, offset_type='OFFSET', segments=2, profile=0.5, affect='EDGES', clamp_overlap=True)
        for f in res.get("faces", []):
            f.smooth = True
    _uv(b, s)
    _merge(bm, b, rot, c)


def lathe(bm, prof, s, at=(0, 0, 0), rot=None, segs=20, sx=1.0, sy=1.0, smooth=True):
    """A round part from a profile [(radius, z), ...] going from the axis at the bottom (r = 0)
    up to the axis at the top (r = 0); sx / sy squash it into an oval."""
    b = bmesh.new()
    bot = b.verts.new((0, 0, prof[0][1]))
    top = b.verts.new((0, 0, prof[-1][1]))
    rings = []
    for r, z in prof[1:-1]:
        rings.append([b.verts.new((r * sx * math.cos(2 * math.pi * k / segs), r * sy * math.sin(2 * math.pi * k / segs), z)) for k in range(segs)])
    for k in range(segs):
        k2 = (k + 1) % segs
        b.faces.new((bot, rings[0][k2], rings[0][k]))
        for i in range(len(rings) - 1):
            b.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
        b.faces.new((rings[-1][k], rings[-1][k2], top))
    bmesh.ops.recalc_face_normals(b, faces=b.faces)
    for f in b.faces:
        f.smooth = smooth
    _uv(b, s)
    _merge(bm, b, rot, at)


def cyl(bm, c, r, h, s, rot=None, segs=20, bevel=0.3, sx=1.0, sy=1.0):
    """A cylinder standing on c (its bottom centre) with softly rounded rims."""
    e = min(r, h) * bevel * 0.5
    prof = [(0, 0), (r - e, 0), (r, e), (r, h - e), (r - e, h), (0, h)]
    lathe(bm, prof, s, c, rot, segs, sx, sy)


def sphere(bm, c, radii, s, rot=None, segs=(18, 10)):
    prof = [(math.sin(math.pi * i / segs[1]), -math.cos(math.pi * i / segs[1])) for i in range(segs[1] + 1)]
    prof[0] = (0, -1)
    prof[-1] = (0, 1)
    b = bmesh.new()
    lathe(b, prof, s, segs=segs[0])
    for v in b.verts:
        v.co = Vector((v.co.x * radii[0], v.co.y * radii[1], v.co.z * radii[2]))
    _merge(bm, b, rot, c)


def capsule(bm, a, b_, r, s, segs=10):
    """A rod with round ends from a to b_."""
    a, b_ = Vector(a), Vector(b_)
    L = (b_ - a).length
    prof = []
    for i in range(5):
        ang = -math.pi / 2 + (math.pi / 2) * i / 4
        prof.append((r * math.cos(ang), r * math.sin(ang)))
    for i in range(5):
        ang = (math.pi / 2) * i / 4
        prof.append((r * math.cos(ang), L + r * math.sin(ang)))
    prof[0] = (0, -r)
    prof[-1] = (0, L + r)
    b = bmesh.new()
    lathe(b, prof, s, segs=segs)
    q = Vector((0, 0, 1)).rotation_difference((b_ - a).normalized())
    for v in b.verts:
        v.co = q @ v.co + a
    _merge(bm, b)


def ring(bm, c, R, r, s, rot=None, segs=28, rsegs=8, sx=1.0, sy=1.0):
    """A torus (axis Z) of radius R, tube r."""
    b = bmesh.new()
    vs = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        row = []
        for j in range(rsegs):
            t = 2 * math.pi * j / rsegs
            rr = R + r * math.cos(t)
            row.append(b.verts.new((rr * math.cos(a) * sx, rr * math.sin(a) * sy, r * math.sin(t))))
        vs.append(row)
    for i in range(segs):
        for j in range(rsegs):
            b.faces.new((vs[i][j], vs[(i + 1) % segs][j], vs[(i + 1) % segs][(j + 1) % rsegs], vs[i][(j + 1) % rsegs]))
    bmesh.ops.recalc_face_normals(b, faces=b.faces)
    for f in b.faces:
        f.smooth = True
    _uv(b, s)
    _merge(bm, b, rot, c)


def leaf(bm, base, direction, L, W, s, roll=0.0, thick=0.012):
    """A flat leaf from base along direction, L long and W wide."""
    d = Vector(direction).normalized()
    b = bmesh.new()
    sphere(b, (0, 0, L / 2), (W / 2, thick, L / 2), s, segs=(12, 8))
    bmesh.ops.rotate(b, verts=b.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(roll), 3, 'Z'))
    q = Vector((0, 0, 1)).rotation_difference(d)
    for v in b.verts:
        v.co = q @ v.co + Vector(base)
    _merge(bm, b)


def daisy(bm, c, R, petal=WHITE, centre=YELLOW, n=6, h=0.02, face=None):
    """A flat daisy: n round petals and a yellow middle. face: rot to stand it up."""
    b = bmesh.new()
    for k in range(n):
        a = 2 * math.pi * k / n
        sphere(b, (math.cos(a) * R * 0.55, math.sin(a) * R * 0.55, 0), (R * 0.45, R * 0.3, h), petal, rot=(0, 0, math.degrees(a)), segs=(12, 6))
    sphere(b, (0, 0, h * 0.6), (R * 0.32, R * 0.32, h * 1.1), centre, segs=(12, 6))
    _merge(bm, b, face, c)


def pot(bm, c, r, h, top=CREAM, band=SAGE, soil=True):
    """A cream plant pot with a sage lower band."""
    lathe(bm, [(0, 0), (r * 0.78, 0), (r * 0.82, h * 0.42), (0, h * 0.42)], band, c)
    lathe(bm, [(0, h * 0.4), (r * 0.82, h * 0.4), (r, h * 0.92), (r * 1.04, h), (r * 0.92, h), (0, h)], top, c)
    if soil:
        cyl(bm, (c[0], c[1], c[2] + h * 0.93), r * 0.88, h * 0.09, SOIL)


def monstera(bm, c, size=1.0, n=7, seed=1):
    """Big split-leaf plant: stems from the pot fanning out, a broad leaf on each."""
    rnd = random.Random(seed)
    base = Vector(c)
    for k in range(n + 3):
        inner = k >= n
        a = 2 * math.pi * (k if not inner else (k - n) * n / 3 + 0.5) / n + rnd.uniform(-0.2, 0.2)
        reach = (0.08 if inner else rnd.uniform(0.16, 0.24)) * size
        h = (rnd.uniform(0.42, 0.55) if inner else rnd.uniform(0.18, 0.36)) * size
        top = base + Vector((math.cos(a) * reach, math.sin(a) * reach, h))
        capsule(bm, base, top, 0.012 * size, LEAF_D, segs=6)
        out = Vector((math.cos(a), math.sin(a), 0.9 if inner else 0.25))
        L = (0.3 if inner else 0.4) * size
        leaf(bm, top, out, L, L * 0.85, LEAF if k % 2 else LEAF_L, roll=math.degrees(a) + 90, thick=0.016 * size)


def vine(bm, start, step, n, s=LEAF, size=0.08, seed=2):
    """A vine trailing down from start, each leaf step further (a stem joins them)."""
    rnd = random.Random(seed)
    pts = [Vector(start)]
    for k in range(n - 1):
        pts.append(pts[-1] + Vector(step) + Vector((rnd.uniform(-0.015, 0.015), 0, 0)))
    vine_path(bm, pts, size, seed)


def vine_ring(bm, c, R, a0, a1, n, y=-0.04, size=0.08, seed=5):
    """A vine growing along a round frame (centre c, radius R, angles a0..a1 degrees, in the XZ plane)."""
    pts = [Vector((c[0] + R * math.cos(math.radians(a0 + (a1 - a0) * k / (n - 1))), c[1] + y, c[2] + R * math.sin(math.radians(a0 + (a1 - a0) * k / (n - 1))))) for k in range(n)]
    vine_path(bm, pts, size, seed)


def sprig(bm, c, size=0.05, s=SAGE_D):
    """A little leaf sprig painted on a front (-Y) surface: a stem and three leaves."""
    x, y, z = c
    capsule(bm, (x, y, z - size * 0.6), (x, y, z + size * 0.5), size * 0.06, s, segs=6)
    leaf(bm, (x, y, z + size * 0.3), (0, 0, 1), size * 0.7, size * 0.38, s, thick=size * 0.06)
    for sx in (-1, 1):
        leaf(bm, (x, y, z - size * 0.1), (sx * 0.85, 0, 0.55), size * 0.6, size * 0.32, s, thick=size * 0.06)


def vine_path(bm, pts, size=0.07, seed=2):
    """A trailing vine: a thin stem through pts with a leaf at each point."""
    rnd = random.Random(seed)
    for k in range(len(pts) - 1):
        capsule(bm, pts[k], pts[k + 1], size * 0.07, LEAF_D, segs=6)
    for k, p in enumerate(pts):
        side = 1 if k % 2 else -1
        d = Vector((side * 0.7, -0.5, rnd.uniform(-0.4, 0.2)))
        leaf(bm, p, d, size * rnd.uniform(0.9, 1.15), size * 0.75, LEAF if k % 2 else LEAF_L, roll=rnd.uniform(0, 180), thick=size * 0.1)


def books(bm, c, n=2, w=0.2, d=0.15, h=0.035, cols=(SAGE, CREAM, SAGE_D)):
    for k in range(n):
        rbox(bm, (c[0] + (k % 2) * 0.01, c[1], c[2] + h * (k + 0.5)), (w - k * 0.015, d, h * 0.95), cols[k % len(cols)], r=0.006)


def knob(bm, c, r=0.025, s=WOOD_D):
    sphere(bm, c, (r, r * 0.8, r), s, segs=(10, 6))


def legs4(bm, hx, hy, h, s=WOOD_D, r=0.03, taper=True):
    for sx in (-1, 1):
        for sy in (-1, 1):
            if taper:
                lathe(bm, [(0, 0), (r * 0.7, 0), (r, h), (0, h)], s, (sx * hx, sy * hy, 0), segs=10)
            else:
                cyl(bm, (sx * hx, sy * hy, 0), r, h, s, segs=10)


def drawers(bm, w, d, z0, z1, n, cols=1, front=WOOD_L, knob_s=WOOD_D):
    gap = 0.02
    h = (z1 - z0 - gap * (n + 1)) / n
    for i in range(n):
        z = z0 + gap + h / 2 + i * (h + gap)
        rbox(bm, (0, -d / 2 - 0.008, z), (w - 0.06, 0.02, h), front, r=0.008)
        for k in range(cols):
            x = 0 if cols == 1 else (-0.25 + 0.5 * k) * w
            knob(bm, (x, -d / 2 - 0.03, z), s=knob_s)


# ---------- Bedroom ----------
def bedside_table(bm):
    legs4(bm, 0.2, 0.15, 0.09)
    rbox(bm, (0, 0, 0.32), (0.5, 0.4, 0.46), WOOD, r=0.02)
    rbox(bm, (0, 0, 0.57), (0.54, 0.44, 0.04), WOOD_D, r=0.012)
    drawers(bm, 0.5, 0.4, 0.09, 0.55, 2)
    books(bm, (0.1, 0.02, 0.59), 2, 0.2, 0.14)
    pot(bm, (-0.12, 0.03, 0.59), 0.07, 0.1)
    monstera(bm, (-0.12, 0.03, 0.68), 0.35, 5, seed=3)
    vine(bm, (-0.22, -0.12, 0.6), (0, -0.002, -0.07), 5, size=0.06)


def table_lamp(bm):
    lathe(bm, [(0, 0), (0.08, 0), (0.12, 0.06), (0.12, 0.12), (0.06, 0.18), (0, 0.18)], WOOD)
    cyl(bm, (0, 0, 0.17), 0.018, 0.12, WOOD_D)
    lathe(bm, [(0, 0.27), (0.17, 0.27), (0.16, 0.29), (0.1, 0.48), (0, 0.48)], CREAM)
    for x in (-0.06, 0.06):
        sprig(bm, (x, -0.148 + abs(x) * 0.15, 0.37), 0.06, SAGE)
    capsule(bm, (0.08, -0.04, 0.27), (0.08, -0.04, 0.2), 0.004, BROWN, segs=6)
    sphere(bm, (0.08, -0.04, 0.19), (0.012, 0.012, 0.012), WOOD_D, segs=(8, 6))


def alarm_clock(bm):
    for sx in (-1, 1):
        capsule(bm, (sx * 0.07, 0.0, 0.06), (sx * 0.1, 0.0, 0.015), 0.014, SAGE_D, segs=8)
    cyl(bm, (0, 0.04, 0.17), 0.13, 0.08, SAGE, rot=(90, 0, 0), segs=28)
    cyl(bm, (0, -0.045, 0.17), 0.105, 0.012, CREAM, rot=(90, 0, 0), segs=28)
    for k in range(12):
        a = 2 * math.pi * k / 12
        rbox(bm, (0.085 * math.sin(a), -0.052, 0.17 + 0.085 * math.cos(a)), (0.008, 0.004, 0.018), BROWN, r=0.002, rot=(0, -math.degrees(a), 0))
    rbox(bm, (-0.02, -0.056, 0.19), (0.012, 0.004, 0.06), BROWN, r=0.003, rot=(0, -40, 0))
    rbox(bm, (0.025, -0.056, 0.185), (0.01, 0.004, 0.075), BROWN, r=0.003, rot=(0, 55, 0))
    sphere(bm, (0, -0.058, 0.17), (0.012, 0.006, 0.012), BROWN, segs=(8, 6))
    for sx in (-1, 1):
        sphere(bm, (sx * 0.085, 0, 0.3), (0.06, 0.05, 0.045), SAGE, rot=(0, sx * 25, 0))
    for p, q in (((-0.06, 0, 0.33), (-0.04, 0, 0.38)), ((-0.04, 0, 0.38), (0.04, 0, 0.38)), ((0.04, 0, 0.38), (0.06, 0, 0.33))):
        capsule(bm, p, q, 0.012, SAGE_D, segs=8)


def cozy_bed(bm):
    for sx in (-1, 1):
        for sy in (-1, 1):
            rbox(bm, (sx * 0.72, sy * 0.92, 0.09), (0.1, 0.1, 0.18), WOOD_D, r=0.02)
    rbox(bm, (0, 0.98, 0.5), (1.56, 0.12, 0.8), WOOD, r=0.05)
    lathe(bm, [(0, 0), (0.78, 0), (0.78, 0.04), (0, 0.04)], WOOD, (0, 0.98, 0.86), rot=(90, 0, 0), segs=24, sx=1.0, sy=0.25)
    for sx in (-1, 1):
        cyl(bm, (sx * 0.78, 0.98, 0.0), 0.07, 1.0, WOOD_D, segs=12)
        sphere(bm, (sx * 0.78, 0.98, 1.02), (0.075, 0.075, 0.06), WOOD_D)
    rbox(bm, (0, -0.97, 0.3), (1.5, 0.1, 0.42), WOOD, r=0.04)
    for sx in (-1, 1):
        rbox(bm, (sx * 0.71, 0, 0.27), (0.08, 1.86, 0.16), WOOD, r=0.025)
    rbox(bm, (0, 0, 0.41), (1.38, 1.86, 0.22), CREAM, r=0.07)
    rbox(bm, (0, -0.25, 0.47), (1.44, 1.3, 0.13), SAGE, r=0.06)
    rbox(bm, (0, 0.38, 0.505), (1.42, 0.14, 0.07), CREAM, r=0.03)
    for sx in (-1, 1):
        rbox(bm, (sx * 0.33, 0.72, 0.6), (0.56, 0.3, 0.15), WHITE, r=0.07, rot=(-12, 0, 0))
    rbox(bm, (0.05, 0.55, 0.63), (0.32, 0.12, 0.25), SAGE_D, r=0.06, rot=(-20, 0, 0))
    daisy(bm, (0.05, 0.48, 0.65), 0.07, face=(70, 0, 0))
    rbox(bm, (0.42, -0.55, 0.555), (0.42, 0.7, 0.05), CREAM, r=0.02)
    for y in (-0.76, -0.68):
        rbox(bm, (0.42, y, 0.585), (0.43, 0.03, 0.012), SAGE_D, r=0.004)


def dresser(bm):
    legs4(bm, 0.42, 0.17, 0.09)
    rbox(bm, (0, 0, 0.42), (1.0, 0.44, 0.66), WOOD, r=0.025)
    rbox(bm, (0, 0, 0.765), (1.04, 0.48, 0.04), WOOD_D, r=0.012)
    drawers(bm, 1.0, 0.44, 0.09, 0.75, 3, cols=2)
    pot(bm, (-0.36, 0.03, 0.785), 0.08, 0.11)
    monstera(bm, (-0.36, 0.03, 0.88), 0.38, 5, seed=4)
    vine(bm, (-0.48, -0.15, 0.78), (0, -0.002, -0.08), 5, size=0.06)
    books(bm, (-0.05, 0.05, 0.785), 2, 0.22, 0.15)
    lathe(bm, [(0, 0), (0.05, 0), (0.055, 0.06), (0.03, 0.1), (0, 0.1)], GLASS_G, (0.3, 0.05, 0.785))
    for a in (-12, 0, 14):
        capsule(bm, (0.3, 0.05, 0.86), (0.3 + 0.12 * math.sin(math.radians(a)), 0.05, 0.86 + 0.18), 0.004, BROWN, segs=6)


def wardrobe(bm):
    legs4(bm, 0.43, 0.22, 0.08)
    rbox(bm, (0, 0, 1.02), (1.0, 0.55, 1.88), WOOD, r=0.03)
    rbox(bm, (0, 0, 1.99), (1.08, 0.6, 0.08), WOOD_D, r=0.025)
    lathe(bm, [(0, 0), (0.5, 0), (0.5, 0.03), (0, 0.03)], WOOD_D, (0, 0.2, 2.02), rot=(90, 0, 0), segs=24, sy=0.12)
    for sx in (-1, 1):
        rbox(bm, (sx * 0.235, -0.283, 1.22), (0.43, 0.02, 1.32), WOOD_L, r=0.015)
        rbox(bm, (sx * 0.235, -0.296, 1.22), (0.31, 0.012, 1.15), WOOD, r=0.02)
        knob(bm, (sx * 0.06, -0.31, 1.15))
    rbox(bm, (0, -0.283, 0.33), (0.88, 0.02, 0.24), WOOD_L, r=0.015)
    knob(bm, (0, -0.31, 0.33))


def wall_mirror(bm, vine_side=-1):
    ring(bm, (0, 0, 0.42), 0.36, 0.045, WOOD, rot=(90, 0, 0), segs=36)
    cyl(bm, (0, 0.01, 0.42), 0.34, 0.02, GLASS, rot=(90, 0, 0), segs=36)
    rbox(bm, (-0.1, -0.012, 0.52), (0.04, 0.004, 0.22), WHITE, r=0.002, rot=(0, -35, 0))
    a0, a1 = (100, 215) if vine_side < 0 else (-35, 80)
    vine_ring(bm, (0, 0, 0.42), 0.37, a0, a1, 8, size=0.085, seed=5)


def clothes_hamper(bm):
    lathe(bm, [(0, 0), (0.23, 0), (0.26, 0.05), (0.29, 0.42), (0, 0.42)], WICKER, segs=28)
    for z in (0.1, 0.18, 0.26, 0.34):
        ring(bm, (0, 0, z), 0.258 + z * 0.075, 0.007, WICKER_D, segs=28, rsegs=6)
    ring(bm, (0, 0, 0.45), 0.29, 0.035, CREAM, segs=28)
    cyl(bm, (0, 0, 0.4), 0.27, 0.03, CREAM_D, segs=28)
    rbox(bm, (0.18, -0.2, 0.33), (0.2, 0.05, 0.36), SAGE, r=0.02, rot=(0, 0, 40))
    rbox(bm, (0.18, -0.21, 0.24), (0.21, 0.052, 0.025), CREAM, r=0.008, rot=(0, 0, 40))
    for sx in (-1, 1):
        sphere(bm, (sx * 0.07, -0.29, 0.43), (0.05, 0.02, 0.03), CREAM)


def plush_rug(bm):
    daisy(bm, (0, 0, 0.035), 0.75, petal=WHITE, centre=YELLOW, n=6, h=0.035)


def potted_plant(bm, seed=7, size=1.0):
    pot(bm, (0, 0, 0), 0.17 * size, 0.28 * size)
    monstera(bm, (0, 0, 0.26 * size), 1.15 * size, 8, seed=seed)


def cushion_chair(bm):
    """Papasan chair: a rattan bowl tipped back on a little stand, a big cream cushion in it."""
    for a in range(4):
        ang = math.radians(45 + 90 * a)
        capsule(bm, (0.3 * math.cos(ang), 0.3 * math.sin(ang), 0.03), (0.14 * math.cos(ang), 0.14 * math.sin(ang), 0.3), 0.025, WOOD_D, segs=8)
    ring(bm, (0, 0, 0.3), 0.16, 0.025, WOOD_D)
    lathe(bm, [(0, 0), (0.25, 0), (0.48, 0.16), (0.52, 0.22), (0, 0.22)], WICKER, (0, 0.02, 0.3), rot=(-18, 0, 0), segs=32)
    b = bmesh.new()
    ring(b, (0, 0, 0.215), 0.5, 0.04, WOOD, segs=36)
    _merge(bm, b, (-18, 0, 0), (0, 0.02, 0.3))
    b = bmesh.new()
    sphere(b, (0, 0, 0.24), (0.47, 0.47, 0.13), CREAM, segs=(28, 12))
    for k in range(7):
        a = math.radians(20 + 140 * k / 6)
        sphere(b, (0.4 * math.cos(a), 0.4 * math.sin(a), 0.3), (0.13, 0.13, 0.12), CREAM_D if k % 2 else CREAM)
    _merge(bm, b, (-18, 0, 0), (0, 0.02, 0.3))
    rbox(bm, (0.02, -0.02, 0.68), (0.3, 0.12, 0.26), SAGE, r=0.07, rot=(-28, 0, 6))


def picture_frame(bm):
    rbox(bm, (0, 0, 0.24), (0.36, 0.04, 0.46), WOOD, r=0.012, rot=(-10, 0, 0))
    rbox(bm, (0, -0.015, 0.245), (0.27, 0.02, 0.36), CREAM, r=0.004, rot=(-10, 0, 0))
    capsule(bm, (0.0, 0.04, 0.0), (0.0, 0.14, 0.0), 0.012, WOOD_D, segs=6)
    capsule(bm, (0, 0.05, 0.02), (0, 0.04, 0.32), 0.012, WOOD_D, segs=6)
    capsule(bm, (0, -0.04, 0.12), (0, -0.06, 0.33), 0.005, LEAF, segs=6)
    for z, a in ((0.18, 1), (0.24, -1), (0.29, 1)):
        leaf(bm, (0, -0.045, z), (a * 0.8, -0.1, 0.6), 0.06, 0.03, SAGE_D, thick=0.004)
    for p in ((-0.02, -0.07, 0.34), (0.05, -0.065, 0.3)):
        daisy(bm, p, 0.03, face=(90 - 10, 0, 0), h=0.006)


# ---------- Bathroom ----------
def round_wall_mirror(bm):
    wall_mirror(bm, vine_side=-1)


def towel_rack(bm):
    for sx in (-1, 1):
        rbox(bm, (sx * 0.3, 0.06, 0.62), (0.07, 0.05, 0.12), WOOD_D, r=0.015)
        cyl(bm, (sx * 0.3, 0.03, 0.62), 0.03, 0.05, WOOD, rot=(90, 0, 0))
    capsule(bm, (-0.3, 0.0, 0.62), (0.3, 0.0, 0.62), 0.025, WOOD, segs=12)
    for x, a, b in ((-0.11, CREAM, SAGE), (0.1, SAGE, CREAM)):
        rbox(bm, (x, -0.02, 0.37), (0.22, 0.035, 0.5), a, r=0.012, rot=(0, 0, 4 if x > 0 else -3))
        rbox(bm, (x, 0.02, 0.5), (0.22, 0.035, 0.24), a, r=0.012)
        for z in (0.2, 0.24):
            rbox(bm, (x, -0.04, z), (0.222, 0.012, 0.018), b, r=0.004)


def soap_dispenser(bm):
    lathe(bm, [(0, 0), (0.065, 0), (0.07, 0.06), (0, 0.06)], SAGE)
    lathe(bm, [(0, 0.058), (0.07, 0.058), (0.068, 0.14), (0.05, 0.17), (0, 0.17)], CREAM)
    sprig(bm, (0.0, -0.071, 0.1), 0.05)
    cyl(bm, (0, 0, 0.165), 0.025, 0.04, WOOD_D, segs=12)
    cyl(bm, (0, 0, 0.2), 0.012, 0.04, WOOD, segs=10)
    rbox(bm, (-0.02, 0, 0.245), (0.07, 0.03, 0.025), WOOD, r=0.008)
    capsule(bm, (-0.055, 0, 0.245), (-0.07, 0, 0.23), 0.008, WOOD, segs=6)


def toothbrush_cup(bm):
    lathe(bm, [(0, 0), (0.06, 0), (0.062, 0.05), (0, 0.05)], SAGE)
    lathe(bm, [(0, 0.048), (0.062, 0.048), (0.068, 0.13), (0.063, 0.13), (0, 0.13)], CREAM)
    sprig(bm, (0.0, -0.066, 0.085), 0.045)
    for x, col, tilt in ((-0.02, BLUE, -10), (0.022, PINK, 12)):
        top = (x + 0.04 * math.sin(math.radians(tilt)), 0, 0.26)
        capsule(bm, (x, 0, 0.05), top, 0.009, col, segs=8)
        rbox(bm, (top[0], -0.008, top[2] + 0.02), (0.016, 0.018, 0.035), WHITE, r=0.004, rot=(0, tilt, 0))


def scented_candle(bm):
    lathe(bm, [(0, 0), (0.085, 0), (0.09, 0.02), (0.09, 0.14), (0, 0.14)], GLASS)
    cyl(bm, (0, 0, 0.1), 0.08, 0.035, CREAM, segs=24)
    rbox(bm, (0, -0.087, 0.07), (0.09, 0.01, 0.06), CREAM_D, r=0.004)
    daisy(bm, (0, -0.093, 0.07), 0.025, face=(90, 0, 0), h=0.004)
    capsule(bm, (0, 0, 0.13), (0, 0, 0.16), 0.003, BROWN, segs=6)
    lathe(bm, [(0, 0.15), (0.012, 0.16), (0.008, 0.19), (0, 0.205)], FLAME, segs=10)


def bath_mat(bm):
    rbox(bm, (0, 0, 0.015), (0.9, 0.6, 0.03), SAGE, r=0.012)
    daisy(bm, (0, 0, 0.035), 0.17, h=0.012)


def wicker_laundry_basket(bm):
    lathe(bm, [(0, 0), (0.24, 0), (0.27, 0.04), (0.29, 0.3), (0, 0.3)], WICKER, segs=28, sx=1.35)
    for z in (0.09, 0.16, 0.23):
        ring(bm, (0, 0, z), 0.275 + z * 0.05, 0.011, WICKER_D, segs=28, rsegs=6, sx=1.35)
    ring(bm, (0, 0, 0.32), 0.29, 0.03, CREAM, segs=28, sx=1.35)
    cyl(bm, (0, 0, 0.28), 0.27, 0.03, CREAM_D, segs=28, sx=1.35)
    for sx in (-1, 1):
        ring(bm, (sx * 0.38, 0, 0.35), 0.07, 0.016, WOOD, rot=(90, 0, 0), segs=14, rsegs=6)
    rbox(bm, (0.12, -0.18, 0.28), (0.2, 0.05, 0.2), WHITE, r=0.02, rot=(0, 0, 20))


def toilet_paper_holder(bm):
    rbox(bm, (-0.15, 0.06, 0.25), (0.08, 0.04, 0.12), WOOD_D, r=0.015)
    capsule(bm, (-0.15, 0.03, 0.25), (-0.15, -0.08, 0.25), 0.02, WOOD, segs=10)
    capsule(bm, (-0.16, 0.0, 0.25), (0.14, 0.0, 0.25), 0.015, WOOD, segs=10)
    sphere(bm, (0.15, 0, 0.25), (0.03, 0.03, 0.03), WOOD_D)
    cyl(bm, (-0.11, 0, 0.25), 0.1, 0.22, WHITE, rot=(0, 90, 0), segs=24)
    rbox(bm, (0.0, -0.1, 0.11), (0.2, 0.012, 0.22), WHITE, r=0.004)
    sprig(bm, (0.0, -0.108, 0.1), 0.05, SAGE)


def potted_bathroom_plant(bm):
    potted_plant(bm, seed=11, size=0.8)


def wall_shelf_bottles(bm):
    rbox(bm, (0, 0, 0.12), (0.8, 0.2, 0.035), WOOD, r=0.01)
    for sx in (-1, 1):
        rbox(bm, (sx * 0.28, 0.07, 0.05), (0.035, 0.06, 0.12), WOOD_D, r=0.01)
    lathe(bm, [(0, 0.137), (0.05, 0.137), (0.05, 0.3), (0.03, 0.33), (0, 0.33)], SAGE_D, (-0.28, 0, 0))
    cyl(bm, (-0.28, 0, 0.325), 0.012, 0.04, BLACK, segs=8)
    rbox(bm, (-0.3, 0, 0.375), (0.05, 0.02, 0.015), BLACK, r=0.004)
    sprig(bm, (-0.28, -0.052, 0.22), 0.05, CREAM)
    lathe(bm, [(0, 0.137), (0.04, 0.137), (0.04, 0.27), (0.02, 0.29), (0, 0.29)], GLASS_G, (-0.15, 0, 0))
    cyl(bm, (-0.15, 0, 0.285), 0.022, 0.03, GOLD, segs=10)
    cyl(bm, (-0.04, 0, 0.137), 0.05, 0.06, CREAM, segs=16)
    cyl(bm, (-0.04, 0, 0.195), 0.052, 0.02, WOOD_L, segs=16)
    pot(bm, (0.18, 0, 0.137), 0.07, 0.1)
    monstera(bm, (0.18, 0, 0.23), 0.3, 5, seed=13)
    vine(bm, (0.26, -0.06, 0.13), (0.005, 0, -0.08), 6, size=0.06, seed=14)


def small_stool(bm):
    for a in range(4):
        ang = math.radians(45 + 90 * a)
        capsule(bm, (0.17 * math.cos(ang), 0.17 * math.sin(ang), 0.02), (0.11 * math.cos(ang), 0.11 * math.sin(ang), 0.38), 0.028, WOOD_D, segs=10)
    cyl(bm, (0, 0, 0.38), 0.21, 0.06, WOOD, segs=24)
    for x in (-0.07, 0.07):
        rbox(bm, (x, 0, 0.441), (0.005, 0.38, 0.003), WOOD_D, r=0.001)


def rubber_duck(bm):
    sphere(bm, (0, 0.02, 0.1), (0.13, 0.16, 0.1), YELLOW)
    sphere(bm, (0, 0.12, 0.17), (0.06, 0.05, 0.06), YELLOW, rot=(30, 0, 0))
    sphere(bm, (0, -0.07, 0.24), (0.085, 0.08, 0.08), YELLOW)
    sphere(bm, (0, -0.155, 0.225), (0.05, 0.04, 0.018), ORANGE)
    for sx in (-1, 1):
        sphere(bm, (sx * 0.042, -0.135, 0.265), (0.014, 0.01, 0.016), BLACK, segs=(10, 6))
        sphere(bm, (sx * 0.12, 0.03, 0.13), (0.03, 0.08, 0.05), YELLOW, rot=(10, 0, 0))


# ---------- Living room ----------
def cozy_armchair(bm):
    for sx in (-1, 1):
        for sy in (-1, 1):
            lathe(bm, [(0, 0), (0.02, 0), (0.03, 0.09), (0, 0.09)], WOOD_D, (sx * 0.32, sy * 0.28, 0), segs=10)
    rbox(bm, (0, 0, 0.24), (0.86, 0.78, 0.3), CREAM, r=0.1)
    rbox(bm, (0, 0.3, 0.6), (0.82, 0.22, 0.6), CREAM, r=0.1)
    for sx in (-1, 1):
        rbox(bm, (sx * 0.38, -0.02, 0.45), (0.2, 0.74, 0.28), CREAM, r=0.09)
    rbox(bm, (0, -0.05, 0.44), (0.56, 0.6, 0.12), CREAM_D, r=0.05)
    rbox(bm, (0.12, 0.12, 0.62), (0.32, 0.12, 0.28), YELLOW, r=0.06, rot=(-15, 0, -10))
    rbox(bm, (-0.42, -0.05, 0.42), (0.26, 0.45, 0.42), SAGE, r=0.03, rot=(0, 8, 0))
    for y in (-0.22, -0.15, -0.08, -0.01, 0.06, 0.13):
        capsule(bm, (-0.47, y, 0.2), (-0.47, y, 0.13), 0.008, CREAM, segs=6)


def throw_pillow(bm):
    rbox(bm, (0, 0, 0.23), (0.44, 0.16, 0.42), CREAM, r=0.075)
    daisy(bm, (0, -0.075, 0.23), 0.13, face=(90, 0, 0), h=0.015)
    for sx in (-1, 1):
        sprig(bm, (sx * 0.13, -0.079, 0.23), 0.07, SAGE_D)
    # tassels on the four corners: soft drops pointing out diagonally
    for sx in (-1, 1):
        for sz in (-1, 1):
            base = Vector((sx * 0.2, 0, 0.23 + sz * 0.19))
            d = Vector((sx, 0, sz)).normalized()
            capsule(bm, base, base + d * 0.035, 0.012, GOLD, segs=8)
            sphere(bm, tuple(base + d * 0.06), (0.024, 0.024, 0.024), GOLD, segs=(10, 6))


def floor_lamp(bm):
    for a in range(3):
        ang = math.radians(90 + 120 * a)
        capsule(bm, (0.25 * math.cos(ang), 0.25 * math.sin(ang), 0.02), (0.02 * math.cos(ang), 0.02 * math.sin(ang), 1.2), 0.022, WOOD, segs=10)
    cyl(bm, (0, 0, 1.15), 0.035, 0.08, WOOD_D, segs=12)
    lathe(bm, [(0, 1.18), (0.24, 1.18), (0.23, 1.2), (0.19, 1.48), (0, 1.48)], CREAM, segs=28)
    capsule(bm, (0.1, -0.08, 1.18), (0.1, -0.08, 1.05), 0.004, BROWN, segs=6)
    sphere(bm, (0.1, -0.08, 1.04), (0.015, 0.015, 0.015), WOOD_D, segs=(8, 6))


def coffee_table(bm):
    for a in range(4):
        ang = math.radians(45 + 90 * a)
        lathe(bm, [(0, 0), (0.03, 0), (0.04, 0.3), (0, 0.3)], WOOD_D, (0.32 * math.cos(ang), 0.32 * math.sin(ang), 0), segs=10)
    cyl(bm, (0, 0, 0.3), 0.5, 0.06, WOOD, segs=32, sx=1.25)
    pot(bm, (-0.25, 0.05, 0.36), 0.07, 0.1)
    monstera(bm, (-0.25, 0.05, 0.45), 0.33, 5, seed=21)
    vine(bm, (-0.34, -0.1, 0.36), (0, -0.002, -0.07), 4, size=0.06, seed=22)
    books(bm, (0.2, 0.0, 0.36), 1, 0.22, 0.16, 0.04, (SAGE,))
    lathe(bm, [(0, 0.4), (0.04, 0.4), (0.045, 0.49), (0, 0.49)], CREAM, (0.22, 0.0, 0), segs=14)
    ring(bm, (0.27, 0.0, 0.445), 0.025, 0.008, CREAM, rot=(90, 0, 0), segs=12, rsegs=6)
    sprig(bm, (0.22, -0.046, 0.445), 0.03)


def bookshelf(bm):
    for sx in (-1, 1):
        rbox(bm, (sx * 0.42, 0, 0.55), (0.05, 0.32, 1.1), WOOD, r=0.012)
    rbox(bm, (0, 0.15, 0.55), (0.8, 0.02, 1.06), WOOD_D, r=0.005)
    for z in (0.03, 0.38, 0.73, 1.09):
        rbox(bm, (0, 0, z), (0.84, 0.32, 0.04), WOOD, r=0.01)
    rnd = random.Random(31)
    x = -0.36
    cols = (CREAM, SAGE, SAGE_D, TERRA, CREAM_D)
    while x < -0.02:
        w = rnd.uniform(0.04, 0.06)
        h = rnd.uniform(0.2, 0.26)
        rbox(bm, (x + w / 2, 0, 0.75 + h / 2), (w * 0.9, 0.22, h), cols[rnd.randrange(len(cols))], r=0.006)
        x += w
    rbox(bm, (0.18, 0.05, 0.86), (0.16, 0.03, 0.2), WOOD_L, r=0.008, rot=(-8, 0, 0))
    rbox(bm, (0.18, 0.035, 0.865), (0.11, 0.02, 0.14), CREAM, r=0.004, rot=(-8, 0, 0))
    x = -0.36
    while x < -0.08:
        w = rnd.uniform(0.04, 0.06)
        rbox(bm, (x + w / 2, 0, 0.4 + 0.11), (w * 0.9, 0.22, 0.22), cols[rnd.randrange(len(cols))], r=0.006)
        x += w
    books(bm, (0.08, 0, 0.4), 2, 0.18, 0.18, 0.04, (CREAM_D, SAGE))
    lathe(bm, [(0, 0.4), (0.05, 0.4), (0.07, 0.46), (0.03, 0.54), (0.025, 0.58), (0, 0.58)], CREAM, (0.27, 0, 0))
    rbox(bm, (0, 0, 0.17), (0.6, 0.26, 0.24), WICKER, r=0.02)
    for z in (0.1, 0.17, 0.24):
        rbox(bm, (0, -0.131, z), (0.6, 0.004, 0.015), WICKER_D, r=0.002)
    pot(bm, (-0.26, 0.02, 1.11), 0.07, 0.1)
    monstera(bm, (-0.26, 0.02, 1.2), 0.32, 5, seed=33)
    vine(bm, (-0.42, -0.16, 1.1), (0.005, -0.002, -0.09), 7, size=0.07, seed=34)


def living_potted_plant(bm):
    potted_plant(bm, seed=41, size=1.0)


def wall_clock(bm):
    ring(bm, (0, 0, 0.4), 0.33, 0.05, WOOD, rot=(90, 0, 0), segs=36)
    cyl(bm, (0, 0.03, 0.4), 0.32, 0.04, CREAM, rot=(90, 0, 0), segs=36)
    for k in range(12):
        a = 2 * math.pi * k / 12
        big = k % 3 == 0
        rbox(bm, (0.25 * math.sin(a), -0.015, 0.4 + 0.25 * math.cos(a)), (0.012, 0.006, 0.05 if big else 0.03), BROWN, r=0.003, rot=(0, -math.degrees(a), 0))
    rbox(bm, (-0.05, -0.02, 0.43), (0.022, 0.006, 0.15), BROWN, r=0.006, rot=(0, -45, 0))
    rbox(bm, (0.06, -0.02, 0.45), (0.018, 0.006, 0.2), BROWN, r=0.006, rot=(0, 40, 0))
    sphere(bm, (0, -0.025, 0.4), (0.02, 0.01, 0.02), BROWN, segs=(10, 6))
    vine_ring(bm, (0, 0, 0.4), 0.34, 95, 200, 7, y=-0.05, size=0.085, seed=43)


def framed_art(bm):
    rbox(bm, (0, 0, 0.35), (0.6, 0.05, 0.7), WOOD, r=0.015)
    rbox(bm, (0, -0.02, 0.35), (0.5, 0.02, 0.6), CREAM, r=0.004)
    rbox(bm, (0, -0.03, 0.33), (0.4, 0.004, 0.5), CREAM_D, r=0.002)
    sphere(bm, (0.1, -0.035, 0.5), (0.06, 0.004, 0.06), GOLD, segs=(16, 6))
    capsule(bm, (-0.05, -0.04, 0.12), (0.02, -0.04, 0.48), 0.006, SAGE_D, segs=6)
    for k in range(6):
        z = 0.18 + k * 0.05
        side = 1 if k % 2 else -1
        leaf(bm, (-0.05 + 0.07 * (z - 0.12) / 0.36, -0.04, z), (side * 0.9, 0, 0.5), 0.1, 0.045, SAGE, thick=0.004)


def woven_rug(bm):
    rbox(bm, (0, 0, 0.01), (1.4, 0.9, 0.02), CREAM, r=0.006)
    for sx in (-1, 1):
        for k in (0.5, 0.58):
            rbox(bm, (sx * k, 0, 0.021), (0.04, 0.9, 0.006), SAGE_D, r=0.002)
        for y in [i * 0.06 - 0.42 for i in range(15)]:
            capsule(bm, (sx * 0.7, y, 0.01), (sx * 0.78, y, 0.008), 0.008, CREAM, segs=6)
    capsule(bm, (-0.3, 0, 0.025), (0.3, 0, 0.025), 0.01, SAGE_D, segs=6)
    for k in range(5):
        x = -0.24 + k * 0.12
        for sy in (-1, 1):
            leaf(bm, (x, 0, 0.026), (0.5, sy, 0.0), 0.16, 0.08, SAGE, thick=0.005)


def tv_stand(bm):
    for sx in (-1, 1):
        for sy in (-1, 1):
            lathe(bm, [(0, 0), (0.02, 0), (0.03, 0.12), (0, 0.12)], WOOD_D, (sx * 0.6, sy * 0.15, 0), segs=10)
    rbox(bm, (0, 0, 0.37), (1.4, 0.42, 0.5), WOOD, r=0.025)
    for sx in (-1, 1):
        rbox(bm, (sx * 0.47, -0.21, 0.37), (0.38, 0.02, 0.4), WICKER, r=0.01)
        rbox(bm, (sx * 0.47, -0.22, 0.37), (0.3, 0.008, 0.32), WICKER_D, r=0.004)
    rbox(bm, (0, -0.15, 0.37), (0.5, 0.2, 0.42), WOOD_D, r=0.01)
    rbox(bm, (0, -0.2, 0.3), (0.3, 0.1, 0.07), BLACK, r=0.01)
    for sx in (-1, 1):
        rbox(bm, (sx * 0.3, 0, 0.635), (0.06, 0.15, 0.03), BLACK, r=0.008)
    rbox(bm, (0, 0, 0.98), (1.1, 0.06, 0.64), BLACK, r=0.02)
    rbox(bm, (0, -0.032, 0.98), (1.04, 0.004, 0.58), GREY, r=0.002)
    pot(bm, (0.58, 0, 0.62), 0.07, 0.1)
    monstera(bm, (0.58, 0, 0.71), 0.32, 5, seed=51)
    vine(bm, (0.66, -0.12, 0.62), (0.003, -0.002, -0.09), 5, size=0.07, seed=52)


def table_vase(bm):
    lathe(bm, [(0, 0), (0.07, 0), (0.12, 0.08), (0.1, 0.15), (0, 0.15)], SAGE)
    lathe(bm, [(0, 0.145), (0.1, 0.145), (0.09, 0.2), (0.045, 0.27), (0.05, 0.3), (0, 0.3)], CREAM)
    sprig(bm, (0.0, -0.1, 0.19), 0.05)
    rnd = random.Random(61)
    for k in range(7):
        a = 2 * math.pi * k / 7
        tip = (0.16 * math.cos(a) * rnd.uniform(0.6, 1), 0.16 * math.sin(a) * rnd.uniform(0.6, 1), 0.5 + rnd.uniform(0, 0.1))
        capsule(bm, (0, 0, 0.28), tip, 0.006, LEAF_D, segs=6)
        if k % 2:
            leaf(bm, ((tip[0]) * 0.5, tip[1] * 0.5, 0.4), (math.cos(a), math.sin(a), 0.4), 0.08, 0.05, LEAF, thick=0.006)
        else:
            daisy(bm, tip, 0.06, h=0.01, face=(rnd.uniform(-30, 30), rnd.uniform(-30, 30), 0))


def pouf_ottoman(bm):
    for k in range(10):
        a = 2 * math.pi * k / 10
        sphere(bm, (0.17 * math.cos(a), 0.17 * math.sin(a), 0.2), (0.15, 0.11, 0.19), TERRA, rot=(0, 0, math.degrees(a)))
    sphere(bm, (0, 0, 0.21), (0.27, 0.27, 0.2), TERRA)
    sphere(bm, (0, 0, 0.405), (0.04, 0.04, 0.015), BROWN, segs=(10, 6))


# ---------- Kitchen ----------
def tea_kettle(bm):
    lathe(bm, [(0, 0), (0.13, 0), (0.17, 0.06), (0, 0.06)], SAGE)
    lathe(bm, [(0, 0.055), (0.17, 0.055), (0.17, 0.12), (0.12, 0.2), (0.06, 0.23), (0, 0.23)], CREAM)
    sprig(bm, (0, -0.172, 0.105), 0.06)
    cyl(bm, (0, 0, 0.225), 0.065, 0.02, SAGE, segs=16)
    sphere(bm, (0, 0, 0.26), (0.03, 0.03, 0.025), WOOD, segs=(12, 6))
    capsule(bm, (-0.13, 0, 0.1), (-0.22, 0, 0.18), 0.032, CREAM, segs=10)
    cyl(bm, (-0.225, 0, 0.185), 0.024, 0.014, BLACK, rot=(0, -50, 0), segs=10)
    for p, q in (((-0.08, 0, 0.21), (-0.07, 0, 0.32)), ((0.08, 0, 0.21), (0.07, 0, 0.32))):
        capsule(bm, p, q, 0.012, SAGE_D, segs=8)
    capsule(bm, (-0.09, 0, 0.33), (0.09, 0, 0.33), 0.025, WOOD, segs=10)


def toaster(bm):
    for sx in (-1, 1):
        for sy in (-1, 1):
            sphere(bm, (sx * 0.14, sy * 0.08, 0.012), (0.02, 0.02, 0.014), WOOD_D, segs=(8, 5))
    rbox(bm, (0, 0, 0.06), (0.36, 0.22, 0.09), SAGE, r=0.035)
    rbox(bm, (0, 0, 0.17), (0.36, 0.22, 0.17), CREAM, r=0.05)
    sprig(bm, (0, -0.112, 0.17), 0.06)
    for x in (-0.05, 0.05):
        rbox(bm, (x, 0, 0.255), (0.04, 0.16, 0.02), CREAM_D, r=0.008)
        rbox(bm, (x, 0, 0.3), (0.025, 0.13, 0.12), TOAST, r=0.025, rot=(0, (8 if x > 0 else -6), 0))
    rbox(bm, (0.19, 0, 0.17), (0.02, 0.03, 0.05), SAGE_D, r=0.006)
    cyl(bm, (0.18, 0, 0.17), 0.025, 0.03, WOOD, rot=(0, 90, 0), segs=12)
    rbox(bm, (0.19, -0.04, 0.22), (0.03, 0.03, 0.02), WOOD, r=0.006)


def cutting_board(bm):
    rbox(bm, (0, 0, 0.2), (0.3, 0.03, 0.4), WOOD, r=0.04)
    rbox(bm, (0, 0, 0.45), (0.11, 0.03, 0.12), WOOD, r=0.03)
    cyl(bm, (0, 0.02, 0.48), 0.02, 0.04, WOOD_D, rot=(90, 0, 0), segs=12)
    capsule(bm, (0.05, -0.017, 0.06), (0.08, -0.017, 0.22), 0.004, SAGE_D, segs=6)
    for k in range(4):
        z = 0.09 + k * 0.035
        side = 1 if k % 2 else -1
        leaf(bm, (0.05 + 0.03 * (z - 0.06) / 0.16, -0.018, z), (side * 0.8, 0, 0.6), 0.05, 0.025, SAGE, thick=0.003)


def fruit_bowl(bm):
    lathe(bm, [(0, 0), (0.1, 0), (0.12, 0.03), (0.22, 0.08), (0, 0.08)], SAGE, segs=28)
    lathe(bm, [(0, 0.075), (0.22, 0.075), (0.26, 0.15), (0, 0.15)], CREAM, segs=28)
    sprig(bm, (0, -0.25, 0.11), 0.05)
    sphere(bm, (-0.1, 0, 0.19), (0.075, 0.075, 0.07), RED)
    capsule(bm, (-0.1, 0, 0.26), (-0.095, 0, 0.29), 0.006, BROWN, segs=6)
    leaf(bm, (-0.095, 0, 0.27), (1, 0, 0.5), 0.04, 0.02, LEAF, thick=0.004)
    sphere(bm, (0.04, -0.06, 0.19), (0.07, 0.07, 0.065), ORANGE)
    # a bunch of three curved bananas
    for k in range(3):
        pts = []
        for t in range(5):
            a = math.radians(-70 + t * 35)
            pts.append(Vector((0.02 + 0.13 * math.sin(a), 0.07 + 0.035 * k, 0.17 + 0.13 * (1 - math.cos(a)) * 0.6 + 0.02 * k)))
        for t in range(4):
            capsule(bm, pts[t], pts[t + 1], 0.024 - 0.004 * abs(t - 1.5), YELLOW, segs=10)
        sphere(bm, pts[-1], (0.01, 0.01, 0.01), BROWN, segs=(8, 5))
    for k, p in enumerate(((0.12, 0.04, 0.17), (0.15, 0.06, 0.17), (0.13, 0.08, 0.2), (0.16, 0.04, 0.2), (0.14, 0.06, 0.23))):
        sphere(bm, p, (0.025, 0.025, 0.025), PURPLE, segs=(10, 6))


def spice_rack(bm):
    for sx in (-1, 1):
        rbox(bm, (sx * 0.26, 0, 0.18), (0.03, 0.14, 0.36), WOOD, r=0.008)
    rbox(bm, (0, 0.06, 0.18), (0.5, 0.02, 0.34), WOOD_D, r=0.004)
    for z in (0.02, 0.19):
        rbox(bm, (0, 0, z), (0.5, 0.14, 0.03), WOOD, r=0.008)
        rbox(bm, (0, -0.065, z + 0.06), (0.5, 0.012, 0.03), WOOD_L, r=0.004)
    fills = (LEAF_D, RED, ORANGE, WHITE, LEAF, RED)
    for i in range(6):
        x = -0.15 + (i % 3) * 0.15
        z = 0.035 if i >= 3 else 0.205
        cyl(bm, (x, 0, z), 0.045, 0.1, GLASS, segs=14)
        cyl(bm, (x, 0, z + 0.01), 0.038, 0.06, fills[i], segs=14)
        cyl(bm, (x, 0, z + 0.1), 0.047, 0.035, WOOD_L, segs=14)


def kitchen_scale(bm):
    lathe(bm, [(0, 0), (0.15, 0), (0.12, 0.26), (0.06, 0.28), (0, 0.28)], SAGE, segs=4, sx=1.0, sy=0.7, smooth=False)
    cyl(bm, (0, -0.07, 0.13), 0.08, 0.02, CREAM, rot=(90 + 8, 0, 0), segs=24)
    ring(bm, (0, -0.075, 0.13), 0.082, 0.01, SAGE_D, rot=(98, 0, 0), segs=24)
    rbox(bm, (0.01, -0.095, 0.15), (0.008, 0.004, 0.06), RED, r=0.002, rot=(0, 15, 0))
    cyl(bm, (0, 0, 0.28), 0.03, 0.03, METAL, segs=12)
    lathe(bm, [(0, 0.3), (0.08, 0.3), (0.19, 0.35), (0.2, 0.36), (0, 0.33)], METAL, segs=28)


def utensil_jar(bm):
    lathe(bm, [(0, 0), (0.08, 0), (0.085, 0.07), (0, 0.07)], SAGE)
    lathe(bm, [(0, 0.068), (0.085, 0.068), (0.085, 0.17), (0.075, 0.19), (0, 0.19)], CREAM)
    sprig(bm, (0, -0.087, 0.12), 0.05)
    capsule(bm, (-0.04, 0, 0.12), (-0.07, 0, 0.36), 0.012, WOOD, segs=8)
    sphere(bm, (-0.075, 0, 0.4), (0.035, 0.015, 0.05), WOOD, rot=(0, -8, 0))
    capsule(bm, (0.0, 0, 0.12), (0.0, 0, 0.36), 0.012, WOOD_D, segs=8)
    rbox(bm, (0, 0, 0.41), (0.06, 0.012, 0.09), WOOD_D, r=0.008)
    capsule(bm, (0.04, 0, 0.12), (0.06, 0, 0.32), 0.01, METAL, segs=8)
    for a in (0, 60, 120):
        ring(bm, (0.065, 0, 0.38), 0.035, 0.004, METAL, rot=(90, 0, a), segs=16, rsegs=4, sx=0.6)


def mixing_bowl(bm):
    lathe(bm, [(0, 0), (0.12, 0), (0.18, 0.05), (0, 0.05)], SAGE, segs=28)
    prof = [(0, 0.045), (0.18, 0.045), (0.25, 0.14), (0.26, 0.15), (0.24, 0.15), (0.17, 0.08), (0, 0.06)]
    lathe(bm, prof, CREAM, segs=28)
    sprig(bm, (0, -0.22, 0.1), 0.05)
    capsule(bm, (-0.05, 0.03, 0.07), (0.22, 0.05, 0.32), 0.012, WOOD, segs=8)
    sphere(bm, (-0.07, 0.03, 0.065), (0.04, 0.03, 0.012), WOOD, rot=(0, 40, 0))


def dish_rack(bm):
    rbox(bm, (0, 0, 0.02), (0.5, 0.3, 0.04), WOOD, r=0.01)
    for sy in (-1, 1):
        capsule(bm, (-0.24, sy * 0.13, 0.13), (0.24, sy * 0.13, 0.13), 0.012, WOOD, segs=8)
        for k in range(9):
            x = -0.22 + k * 0.055
            capsule(bm, (x, sy * 0.13, 0.04), (x, sy * 0.13, 0.15), 0.008, WOOD_D, segs=6)
    for k, col in enumerate((CREAM, CREAM, SAGE)):
        x = -0.15 + k * 0.06
        cyl(bm, (x, 0, 0.13), 0.11, 0.015, col, rot=(0, 90, 0), segs=24)
    lathe(bm, [(0, 0.04), (0.045, 0.04), (0.05, 0.14), (0, 0.14)], SAGE, (0.15, 0.0, 0), segs=14)
    ring(bm, (0.2, 0.0, 0.09), 0.025, 0.008, SAGE, rot=(90, 0, 0), segs=12, rsegs=6)
    lathe(bm, [(0, 0.04), (0.04, 0.04), (0.045, 0.12), (0, 0.12)], CREAM, (0.15, -0.09, 0), segs=14)


def apron_hook(bm):
    rbox(bm, (0, 0.03, 0.75), (0.6, 0.04, 0.09), WOOD, r=0.015)
    for x in (-0.18, 0.0, 0.18):
        capsule(bm, (x, 0.01, 0.75), (x, -0.05, 0.76), 0.018, WOOD_D, segs=8)
        sphere(bm, (x, -0.055, 0.762), (0.025, 0.02, 0.025), WOOD_D, segs=(10, 6))
    # apron: sage / cream check rows hanging from the left peg
    capsule(bm, (-0.18, -0.04, 0.74), (-0.25, -0.03, 0.55), 0.008, SAGE_D, segs=6)
    capsule(bm, (-0.18, -0.04, 0.74), (-0.11, -0.03, 0.55), 0.008, SAGE_D, segs=6)
    for r in range(6):
        for k in range(4):
            col = SAGE if (r + k) % 2 else CREAM
            rbox(bm, (-0.245 + k * 0.045, -0.03, 0.53 - r * 0.07), (0.045, 0.02, 0.07), col, r=0.003)
    # towel on the right peg
    rbox(bm, (0.18, -0.035, 0.5), (0.18, 0.025, 0.46), CREAM, r=0.012)
    for z in (0.34, 0.38):
        rbox(bm, (0.18, -0.049, z), (0.182, 0.006, 0.014), SAGE_D, r=0.003)
    sprig(bm, (0.18, -0.05, 0.52), 0.06, SAGE_D)


def bar_stool(bm):
    for a in range(4):
        ang = math.radians(45 + 90 * a)
        capsule(bm, (0.17 * math.cos(ang), 0.17 * math.sin(ang), 0.02), (0.12 * math.cos(ang), 0.12 * math.sin(ang), 0.62), 0.025, WOOD, segs=10)
    ring(bm, (0, 0, 0.25), 0.15, 0.015, WOOD_D, segs=24, rsegs=6)
    cyl(bm, (0, 0, 0.62), 0.19, 0.04, WOOD, segs=24)
    lathe(bm, [(0, 0.65), (0.18, 0.65), (0.19, 0.7), (0.15, 0.73), (0, 0.735)], SAGE, segs=24)


def potted_herb_plant(bm):
    pot(bm, (0, 0, 0), 0.15, 0.2)
    rnd = random.Random(71)
    for layer, (h, reach, n) in enumerate(((0.2, 0.05, 8), (0.27, 0.03, 6), (0.33, 0.0, 4))):
        for k in range(n):
            a = 2 * math.pi * (k + layer * 0.5) / n
            base = (reach * math.cos(a) - 0.03, reach * math.sin(a), h)
            capsule(bm, (-0.03, 0, 0.19), base, 0.006, LEAF_D, segs=6)
            d = (math.cos(a) * 0.8, math.sin(a) * 0.8, 0.7)
            leaf(bm, base, d, rnd.uniform(0.09, 0.11), 0.08, LEAF if (k + layer) % 2 else LEAF_L, roll=math.degrees(a) + 90, thick=0.01)
    for k in range(6):
        x = 0.07 + rnd.uniform(-0.03, 0.03)
        y = rnd.uniform(-0.05, 0.05)
        top = (x + rnd.uniform(-0.04, 0.04), y + rnd.uniform(-0.03, 0.03), 0.38 + rnd.uniform(0, 0.06))
        capsule(bm, (x, y, 0.19), top, 0.007, LEAF_D, segs=6)
        for t in (0.35, 0.55, 0.75, 0.92):
            p = Vector((x, y, 0.19)).lerp(Vector(top), t)
            for sx in (-1, 1):
                leaf(bm, p, (sx, 0.2, 0.9), 0.035, 0.012, LEAF_D, roll=0, thick=0.006)


AREAS = {
    "Bedroom": [("BedsideTable", bedside_table), ("TableLamp", table_lamp), ("AlarmClock", alarm_clock), ("CozyBed", cozy_bed),
                ("Dresser", dresser), ("Wardrobe", wardrobe), ("WallMirror", wall_mirror), ("ClothesHamper", clothes_hamper),
                ("PlushRug", plush_rug), ("PottedPlant", potted_plant), ("CushionChair", cushion_chair), ("PictureFrame", picture_frame)],
    "Bathroom": [("RoundWallMirror", round_wall_mirror), ("TowelRack", towel_rack), ("SoapDispenser", soap_dispenser), ("ToothbrushCup", toothbrush_cup),
                 ("ScentedCandle", scented_candle), ("BathMat", bath_mat), ("WickerLaundryBasket", wicker_laundry_basket), ("ToiletPaperHolder", toilet_paper_holder),
                 ("PottedBathroomPlant", potted_bathroom_plant), ("WallShelfBottles", wall_shelf_bottles), ("SmallStool", small_stool), ("RubberDuck", rubber_duck)],
    "LivingRoom": [("CozyArmchair", cozy_armchair), ("ThrowPillow", throw_pillow), ("FloorLamp", floor_lamp), ("CoffeeTable", coffee_table),
                   ("Bookshelf", bookshelf), ("PottedPlantLiving", living_potted_plant), ("WallClock", wall_clock), ("FramedArt", framed_art),
                   ("WovenRug", woven_rug), ("TVStand", tv_stand), ("TableVase", table_vase), ("PoufOttoman", pouf_ottoman)],
    "Kitchen": [("TeaKettle", tea_kettle), ("Toaster", toaster), ("CuttingBoard", cutting_board), ("FruitBowl", fruit_bowl),
                ("SpiceRack", spice_rack), ("KitchenScale", kitchen_scale), ("UtensilJar", utensil_jar), ("MixingBowl", mixing_bowl),
                ("DishRack", dish_rack), ("ApronHook", apron_hook), ("BarStool", bar_stool), ("PottedHerbPlant", potted_herb_plant)],
}


def _open_edges(o):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    n = sum(1 for e in bm.edges if len(e.link_faces) != 2)
    bm.free()
    return n


def build_decor(only=None, areas=None, prefix="SM_Decor_", root_name="Decor", coll_prefix="Decor_", y0=-260.0):
    areas = areas or AREAS
    mat = bpy.data.materials["M_GradientTexture"]
    root = bpy.data.collections.get(root_name) or bpy.data.collections.new(root_name)
    if root.name not in [c.name for c in bpy.context.scene.collection.children]:
        bpy.context.scene.collection.children.link(root)
    res = {}
    for ai, (area, items) in enumerate(areas.items()):
        if only and area not in only:
            continue
        cname = coll_prefix + area
        coll = bpy.data.collections.get(cname) or bpy.data.collections.new(cname)
        if coll.name not in [c.name for c in root.children]:
            root.children.link(coll)
        for i, (name, fn) in enumerate(items):
            full = prefix + name
            old = bpy.data.objects.get(full)
            if old:
                bpy.data.objects.remove(old, do_unlink=True)
            bm = bmesh.new()
            fn(bm)
            me = bpy.data.meshes.new(full)
            bm.to_mesh(me)
            bm.free()
            me.materials.append(mat)
            o = bpy.data.objects.new(full, me)
            coll.objects.link(o)
            o.location = (i * 3.0, y0 - ai * 4.0, 0.0)
            res[full] = {"faces": len(me.polygons), "open": _open_edges(o), "dims": [round(d, 2) for d in o.dimensions]}
    return res


def render_decor_previews(out_dir, only=None, size=360, areas=None, prefix="SM_Decor_"):
    areas = areas or AREAS
    """One PNG per item, framed from the front-right and a little above."""
    sc = bpy.context.scene
    cam = bpy.data.objects.new("_DecorCam", bpy.data.cameras.new("_DecorCam"))
    sc.collection.objects.link(cam)
    cam.data.type = 'ORTHO'
    sun = bpy.data.objects.new("_DecorSun", bpy.data.lights.new("_DecorSun", 'SUN'))
    sc.collection.objects.link(sun)
    sun.data.energy = 2.6
    sun.rotation_euler = (math.radians(45), math.radians(10), math.radians(30))
    sc.camera = cam
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x = sc.render.resolution_y = size
    sc.render.film_transparent = True
    try:
        sc.view_settings.view_transform = 'Standard'
    except Exception:
        pass
    if sc.world is None:
        sc.world = bpy.data.worlds.new("_decor_world")
    sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.95, 0.93, 0.9, 1)
        bg.inputs[1].default_value = 0.9
    all_obs = [ob for ob in sc.objects if ob not in (cam, sun)]
    was = {ob.name: ob.hide_render for ob in all_obs}
    # EEVEE's first frames after loading come out empty: warm it up
    sc.render.filepath = os.path.join(out_dir, "_warmup.png")
    for _ in range(2):
        bpy.ops.render.render(write_still=True)
    for area, items in areas.items():
        if only and area not in only:
            continue
        os.makedirs(os.path.join(out_dir, area), exist_ok=True)
        for name, _ in items:
            o = bpy.data.objects.get(prefix + name)
            if not o:
                continue
            for ob in all_obs:
                ob.hide_render = ob != o
            ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
            mn = Vector((min(p.x for p in ws), min(p.y for p in ws), min(p.z for p in ws)))
            mx = Vector((max(p.x for p in ws), max(p.y for p in ws), max(p.z for p in ws)))
            centre = (mn + mx) / 2
            diag = (mx - mn).length
            d = Vector((0.55, -1.0, 0.5)).normalized()
            cam.location = centre + d * diag * 3
            cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
            cam.data.ortho_scale = diag * 1.05
            cam.data.clip_end = diag * 10
            path = os.path.join(out_dir, area, name + ".png")
            sc.render.filepath = path
            for attempt in range(3):
                bpy.ops.render.render(write_still=True)
                img = bpy.data.images.load(path)
                import array
                buf = array.array('f', [0.0]) * len(img.pixels)
                img.pixels.foreach_get(buf)
                alpha = max(buf[3::4]) if len(buf) else 0.0
                bpy.data.images.remove(img)
                if alpha > 0:
                    break
    for ob in all_obs:
        ob.hide_render = was.get(ob.name, False)
    bpy.data.objects.remove(cam)
    bpy.data.objects.remove(sun)
