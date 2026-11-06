# Cute fences, set 2 (from Dante's sheet 48: hearts, bows, flowers, stars, clouds...), same rules as
# fences.py (2 m segment with its post at x = 0, SM_Fence_<Name>_Post closes the run, pivot at the
# start post base, runs +X, front -Y; quads only, closed shells, gradient atlas; slot 1 = glow).
#   exec(open(r"<skills>/blender-game-props/fences2.py").read())
#   build_fences2()                # all, or build_fences2(["Heart_Rail"])
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

exec(open(_skill("blender-game-props/fences.py")).read())

PINK = c0(27, 0.86, 0.90)          # rosy rails
PINK_SOFT = c1(4, 0.80, 0.83)      # pale pink paint
HOT_PINK = c0(34, 0.92, 0.99)      # roses, hearts
BUBBLE = c0(29, 0.86, 0.91)        # bows, hydrangea
LILAC = c1(3, 0.78, 0.825)         # deep purple (butterfly body, rainbow)
LAVENDER = c0(29, 0.965, 0.995)    # soft purple paint
LILAC_PALE = c0(29, 0.95, 0.995)
GOLD = c0(23, 0.9, 0.995)
WISTERIA = c1(3, 0.70, 0.80)
GREYBLUE = c0(15, 0.955, 0.99)       # pale blue-grey
CLOUD = c0(18, 0.85, 0.875)
ROPE = c1(2, 0.77, 0.825)
LOG_END = c1(2, 0.80, 0.83)
TERRACOTTA = DARKWOOD
MUSH_RED = c0(6, 0.90, 0.97)
LEAF = GRASS
LEAF_DARK = HEDGE_DARK
FLOWER_MID = c0(10, 0.9, 0.99)
RAINBOW = [c0(14, 0.95, 0.99), c0(8, 0.92, 0.99), c0(23, 0.95, 0.995), c0(9, 0.92, 0.99), c0(21, 0.92, 0.99), LILAC]


# ---------------- shape helpers ----------------
def slab(bm, outline, col, thick=0.1, bulge=0.03, inner=0.5, center=None, at=(0, 0, 0), glowing=False):
    """Chunky 2D shape (outline of (x, z) points, even count, star-shaped around its centre) extruded
    along Y, front/back domed (rim -> inner ring -> quad fan). All quads, closed."""
    n = len(outline)
    assert n % 2 == 0
    cx, cz = center if center else (sum(p[0] for p in outline) / n, sum(p[1] for p in outline) / n)
    b = bmesh.new()

    def side(sign):
        ring = [b.verts.new((x, sign * thick / 2, z)) for x, z in outline]
        inn = [b.verts.new((cx + (x - cx) * inner, sign * (thick / 2 + bulge * 0.7), cz + (z - cz) * inner)) for x, z in outline]
        mid = b.verts.new((cx, sign * (thick / 2 + bulge), cz))
        return ring, inn, mid
    fr, fi, fm = side(-1)
    br, bi, bmid = side(1)
    for i in range(n):
        j = (i + 1) % n
        b.faces.new((fr[i], fr[j], br[j], br[i]))
        b.faces.new((fr[i], fi[i], fi[j], fr[j]))
        b.faces.new((br[j], bi[j], bi[i], br[i]))
    for i in range(0, n, 2):
        b.faces.new((fm, fi[(i + 2) % n], fi[i + 1], fi[i]))
        b.faces.new((bmid, bi[i], bi[i + 1], bi[(i + 2) % n]))
    uv_part(b, col)
    bmesh.ops.translate(b, vec=Vector(at), verts=b.verts)
    for f in b.faces:
        f.material_index = 1 if glowing else 0
    merge(bm, b)


def polar(fn, n, c=(0, 0)):
    return [(c[0] + fn(2 * math.pi * i / n) * math.cos(2 * math.pi * i / n),
             c[1] + fn(2 * math.pi * i / n) * math.sin(2 * math.pi * i / n)) for i in range(n)]


def ellipse_pts(rx, rz, n=12, c=(0, 0), rot=0.0):
    a0 = math.radians(rot)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x, z = rx * math.cos(a), rz * math.sin(a)
        pts.append((c[0] + x * math.cos(a0) - z * math.sin(a0), c[1] + x * math.sin(a0) + z * math.cos(a0)))
    return pts


def heart_pts(w, c=(0, 0), n=20):
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x = 16 * math.sin(t) ** 3
        z = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((c[0] + x * w / 32, c[1] + (z + 2) * w / 32))
    return pts


def star_pts(r, c=(0, 0), inner=0.48):
    return [(c[0] + (r if i % 2 == 0 else r * inner) * math.cos(math.pi / 2 + math.pi * i / 5),
             c[1] + (r if i % 2 == 0 else r * inner) * math.sin(math.pi / 2 + math.pi * i / 5)) for i in range(10)]


def heart(bm, c, w, col, thick=0.07):
    slab(bm, heart_pts(w, (c[0], c[2])), col, thick, w * 0.12, at=(0, c[1], 0))


def star5(bm, c, r, col, thick=0.06, glowing=False):
    slab(bm, star_pts(r, (c[0], c[2])), col, thick, r * 0.25, center=(c[0], c[2]), at=(0, c[1], 0), glowing=glowing)


def flat_flower(bm, c, r, col, mid=FLOWER_MID):
    """Five-petal flower facing the front (-Y)."""
    # each flower at its own depth (hash of its position): overlapping flowers never share a plane
    c = (c[0], c[1] - 0.006 * (int(abs(c[0]) * 997 + abs(c[2]) * 571 + abs(c[1]) * 313) % 11), c[2])
    slab(bm, polar(lambda a: r * (0.62 + 0.38 * math.cos(5 * a)), 20, (c[0], c[2])), col, r * 0.25, r * 0.1,
         center=(c[0], c[2]), at=(0, c[1], 0))
    b = quad_sphere(r * 0.32, 1, (1, 0.6, 1), 0, 0)
    bmesh.ops.translate(b, vec=Vector((c[0], c[1] - r * 0.15, c[2])), verts=b.verts)
    uv_part(b, mid)
    merge(bm, b)


def ray_hit(poly, c, d):
    """Distance along d from c (inside poly) to the polygon edge."""
    best = 1e9
    n = len(poly)
    for i in range(n):
        ax, az = poly[i]
        bx, bz = poly[(i + 1) % n]
        ex, ez = bx - ax, bz - az
        den = d[0] * ez - d[1] * ex
        if abs(den) < 1e-12:
            continue
        t = ((ax - c[0]) * ez - (az - c[1]) * ex) / den
        s = ((ax - c[0]) * d[1] - (az - c[1]) * d[0]) / den
        if t > 1e-9 and -1e-9 <= s <= 1 + 1e-9:
            best = min(best, t)
    return best


def holed(bm, outer, hole, hc, thick, col, y=0.0, n=40):
    """Flat plate (outer outline) with a hole (outline star-shaped around hc) cut through it: rays
    from hc pair each hole point with the outer edge, plus the outer corners. All quads, closed."""
    angs = [2 * math.pi * i / n for i in range(n)]
    angs += [math.atan2(p[1] - hc[1], p[0] - hc[0]) % (2 * math.pi) for p in outer]
    angs = sorted(set(round(a, 6) for a in angs))
    b = bmesh.new()
    rings = []
    for a in angs:
        d = (math.cos(a), math.sin(a))
        to, ti = ray_hit(outer, hc, d), ray_hit(hole, hc, d)
        o = (hc[0] + d[0] * to, hc[1] + d[1] * to)
        h = (hc[0] + d[0] * ti, hc[1] + d[1] * ti)
        rings.append([b.verts.new((o[0], y - thick / 2, o[1])), b.verts.new((h[0], y - thick / 2, h[1])),
                      b.verts.new((h[0], y + thick / 2, h[1])), b.verts.new((o[0], y + thick / 2, o[1]))])
    m = len(rings)
    for i in range(m):
        a, nx = rings[i], rings[(i + 1) % m]
        for k in range(4):
            b.faces.new((a[k], nx[k], nx[(k + 1) % 4], a[(k + 1) % 4]))
    uv_part(b, col)
    merge(bm, b)


def band(bm, pts, w, h, col):
    """Rectangular bar swept along a path in the XZ plane (h across the path, w deep along Y), capped."""
    b = bmesh.new()
    rings = []
    for i, p in enumerate(pts):
        p = Vector(p)
        t = (Vector(pts[min(i + 1, len(pts) - 1)]) - Vector(pts[max(i - 1, 0)])).normalized()
        yv = Vector((0, 1, 0))
        nv = t.cross(yv).normalized()
        rings.append([b.verts.new(p + nv * sh * h / 2 + yv * sw * w / 2) for sh, sw in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    for i in range(len(rings) - 1):
        a, nx = rings[i], rings[i + 1]
        for k in range(4):
            b.faces.new((a[k], nx[k], nx[(k + 1) % 4], a[(k + 1) % 4]))
    b.faces.new(rings[0])
    b.faces.new(rings[-1])
    uv_part(b, col)
    merge(bm, b)


def arch_pts(x0, x1, zb, zt, y=0.0, n=14):
    return [(x0 + (x1 - x0) * i / n, y, zb + (zt - zb) * math.sin(math.pi * i / n)) for i in range(n + 1)]


def arch_z(x, x0, x1, zb, zt):
    return zb + (zt - zb) * math.sin(math.pi * (x - x0) / (x1 - x0))


def spiral_pts(c, r0, r1, a0, a1, n=16, y=0.0):
    return [(c[0] + (r0 + (r1 - r0) * i / n) * math.cos(a0 + (a1 - a0) * i / n), y,
             c[1] + (r0 + (r1 - r0) * i / n) * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def revolve(bm, prof, col, at=(0, 0, 0), sides=12):
    """Quad surface of revolution from (radius, z) rows, both ends capped with quads."""
    sides += sides % 2
    b = bmesh.new()
    rings = [[b.verts.new((at[0] + r * math.cos(2 * math.pi * k / sides), at[1] + r * math.sin(2 * math.pi * k / sides), at[2] + z))
              for k in range(sides)] for r, z in prof]
    for j in range(len(rings) - 1):
        for k in range(sides):
            b.faces.new((rings[j][k], rings[j][(k + 1) % sides], rings[j + 1][(k + 1) % sides], rings[j + 1][k]))
    quad_cap(b, rings[0])
    quad_cap(b, rings[-1])
    uv_part(b, col)
    merge(bm, b)


def torus(bm, c, R, r, col, axis='Z', n=14, m=6):
    b = bmesh.new()
    g = [[b.verts.new(((R + r * math.cos(2 * math.pi * j / m)) * math.cos(2 * math.pi * i / n),
                       (R + r * math.cos(2 * math.pi * j / m)) * math.sin(2 * math.pi * i / n),
                       r * math.sin(2 * math.pi * j / m))) for j in range(m)] for i in range(n)]
    for i in range(n):
        for j in range(m):
            b.faces.new((g[i][j], g[(i + 1) % n][j], g[(i + 1) % n][(j + 1) % m], g[i][(j + 1) % m]))
    if axis == 'X':
        bmesh.ops.rotate(b, cent=Vector(), matrix=Matrix.Rotation(math.radians(90), 3, 'Y'), verts=b.verts)
    uv_part(b, col)
    bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
    merge(bm, b)


def ball2(bm, c, r, col, scale=(1, 1, 1), cuts=1, jitter=0.0, seed=0):
    b = quad_sphere(r, cuts, scale, jitter, seed)
    bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
    uv_part(b, col)
    merge(bm, b)


def ivy(bm, x, y, z0, z1, seed, n=6, spread=0.05):
    rnd = random.Random(seed)
    for i in range(n):
        z = z0 + (z1 - z0) * (i + rnd.uniform(0, 0.6)) / n
        leaf(bm, (x + rnd.uniform(-spread, spread), y, z), rnd.uniform(-160, -20), rnd.uniform(0.09, 0.13),
             0.075, rnd.uniform(25, 55), LEAF if i % 3 else LEAF_DARK, droop=-0.2)


def vine_rail(bm, x0, x1, z, y, seed, flowers=None, amp=0.05):
    rnd = random.Random(seed)
    pts = [(x0 + (x1 - x0) * i / 12, y, z + amp * math.sin(i * 1.3 + seed)) for i in range(13)]
    tube(bm, pts, [0.012] * len(pts), LEAF_DARK, 6)
    for i in range(1, 12, 2):
        p = pts[i]
        leaf(bm, (p[0], p[1] - 0.01, p[2]), rnd.uniform(-160, -20), 0.1, 0.07, rnd.uniform(15, 45), LEAF, droop=-0.2)
    if flowers:
        for i in (3, 7, 10):
            p = pts[i]
            flat_flower(bm, (p[0], p[1] - 0.03, p[2] + 0.03), 0.04, flowers)


def lattice(bm, x0, x1, z0, z1, col, step=0.28, w=0.05, d=0.03):
    """Diagonal lattice slats clipped to the rectangle, one direction in front, the other behind."""
    for sgn, y in ((1, -d / 2), (-1, d / 2 - 0.012)):
        k = -(x1 - x0) - (z1 - z0)
        while k < (x1 - x0) + (z1 - z0):
            # line: z - z0 = sgn * (x - x0) + k
            pts = []
            for x in (x0, x1):
                z = z0 + sgn * (x - x0) + k
                if z0 - 1e-6 <= z <= z1 + 1e-6:
                    pts.append((x, z))
            for z in (z0, z1):
                x = x0 + (z - z0 - k) * sgn
                if x0 - 1e-6 <= x <= x1 + 1e-6:
                    pts.append((x, z))
            pts = sorted(set((round(px, 5), round(pz, 5)) for px, pz in pts))
            if len(pts) >= 2 and math.dist(pts[0], pts[-1]) > 0.08:
                beam(bm, (pts[0][0], y, pts[0][1]), (pts[-1][0], y, pts[-1][1]), d, w, col)
            k += step


def sq_post(bm, h, col, w=0.2, cap=None, cap_col=None, base=True):
    if base:
        box(bm, (0, 0, 0.05), (w * 1.2, w * 1.2, 0.1), cap_col or col)
    box(bm, (0, 0, h / 2), (w, w, h), col)
    box(bm, (0, 0, h + 0.04), (w * 1.25, w * 1.25, 0.08), cap_col or col, taper=0.85)
    return h + 0.08


def rose(bm, c, r=0.065):
    ball2(bm, c, r, HOT_PINK, (1, 0.75, 1), 1, 0.08, int(c[0] * 100 + c[2] * 37))
    ball2(bm, (c[0], c[1] - r * 0.55, c[2] + r * 0.1), r * 0.5, c0(34, 0.86, 0.9), (1, 0.6, 1), 1, 0.05, 3)
    for k in (-1, 1):
        leaf(bm, (c[0] + k * r * 0.8, c[1], c[2] - r * 0.5), -90 + k * 50, 0.09, 0.06, 20, LEAF, droop=-0.2)


def glow(fn):
    """Builds a part with fn into its own mesh and marks it glowing (slot 1)."""
    def g(bm, *a, **k):
        t = bmesh.new()
        fn(t, *a, **k)
        for f in t.faces:
            f.material_index = 1
        merge(bm, t)
    return g


def mushroom(bm, c, s, seed=0):
    revolve(bm, [(0.06 * s, 0), (0.07 * s, 0.03 * s), (0.055 * s, 0.14 * s), (0.05 * s, 0.17 * s)], CREAM, c, 8)
    revolve(bm, [(0.03 * s, 0.14 * s), (0.13 * s, 0.15 * s), (0.12 * s, 0.2 * s), (0.08 * s, 0.25 * s), (0.02 * s, 0.27 * s)],
            MUSH_RED, c, 10)
    rnd = random.Random(seed)
    for k in range(3):
        a = math.radians(-90 + (k - 1) * 55)
        ball2(bm, (c[0] + 0.1 * s * math.cos(a), c[1] + 0.1 * s * math.sin(a), c[2] + 0.21 * s), 0.022 * s, CREAM, (1, 1, 0.5))


# ---------------- the 20 designs ----------------
def roses_post(bm):
    picket_post(CREAM)(bm)
    ivy(bm, 0.04, -0.06, 0.1, 0.6, 31, 4)
def roses_panel(bm):
    picket_panel(CREAM)(bm)
    tube(bm, [(0.42, -0.05, 0.0), (0.5, -0.06, 0.25), (0.45, -0.06, 0.45), (0.58, -0.06, 0.62)], [0.014] * 4, LEAF_DARK, 6)
    tube(bm, [(1.3, -0.05, 0.0), (1.38, -0.06, 0.3), (1.48, -0.06, 0.55), (1.42, -0.06, 0.8)], [0.014] * 4, LEAF_DARK, 6)
    ivy(bm, 0.5, -0.07, 0.05, 0.6, 32, 5)
    ivy(bm, 1.4, -0.07, 0.05, 0.8, 33, 6)
    for c in ((0.58, -0.09, 0.66), (0.44, -0.09, 0.44), (1.44, -0.09, 0.82), (1.5, -0.09, 0.56), (1.34, -0.09, 0.32)):
        rose(bm, c)
    for x in (0.15, 0.9, 1.75):
        grass(bm, (x, -0.06, 0), 5, int(x * 10), 0.22)


def heartrail_post(bm):
    top = sq_post(bm, 0.95, CREAM)
    heart(bm, (0, 0, top + 0.13), 0.26, HOT_PINK, 0.08)
def heartrail_panel(bm):
    for z in (0.33, 0.75):
        tube(bm, [(0.0, -0.01, z), (SEG, -0.01, z)], [0.06, 0.06], PINK, 10)
    heart(bm, (1.0, -0.04, 0.53), 0.46, PINK, 0.1)
    heart(bm, (1.0, -0.115, 0.55), 0.28, PINK_SOFT, 0.04)


def scroll_post(bm):
    sq_post(bm, 1.0, CREAM, 0.2)
def scroll_panel(bm):
    box(bm, (SEG / 2, 0, 0.2), (SEG, 0.07, 0.1), CREAM)
    band(bm, arch_pts(0.0, SEG, 0.85, 1.05), 0.07, 0.09, CREAM)
    for sx in (1, -1):
        cx = 1.0 - sx * 0.42
        band(bm, spiral_pts((cx, 0.52), 0.25, 0.05, math.pi / 2 if sx > 0 else math.pi / 2, (math.pi / 2 + 3.2 * math.pi) * 1 if sx > 0 else math.pi / 2 - 3.2 * math.pi, 22), 0.045, 0.05, CREAM)
        band(bm, spiral_pts((1.0 - sx * 0.17, 0.82), 0.12, 0.03, -math.pi / 2, -math.pi / 2 + sx * 2.6 * math.pi, 14), 0.045, 0.045, CREAM)
    band(bm, [(1.0, 0, 0.25), (1.0, 0, 1.0)], 0.05, 0.05, CREAM)
    heart(bm, (1.0, -0.02, 1.13), 0.16, PINK, 0.05)


def wisteria_post(bm):
    wood_post(bm, 1.3, WOOD, w=0.2, bolts=(0.15, 1.1), seed=41)
    ivy(bm, 0.05, -0.1, 0.9, 1.3, 42, 3)
def wisteria_panel(bm):
    box(bm, (SEG / 2, -0.01, 0.12), (SEG, 0.08, 0.12), WOOD)
    band(bm, arch_pts(0.0, SEG, 1.08, 1.24, -0.01), 0.1, 0.12, WOOD)
    lattice(bm, 0.1, SEG - 0.1, 0.18, 1.05, WOOD, 0.3)
    rnd = random.Random(43)
    for i, x in enumerate((0.25, 0.55, 0.85, 1.15, 1.45, 1.75)):
        top = arch_z(x, 0.0, SEG, 1.08, 1.24) - 0.06
        n = 5 + i % 2
        for k in range(n):
            r = 0.065 - k * 0.007
            ball2(bm, (x + rnd.uniform(-0.02, 0.02), -0.09, top - k * 0.075), r, WISTERIA, (1, 1, 1.15), 1, 0.08, i * 10 + k)
        leaf(bm, (x, -0.08, top + 0.07), rnd.uniform(-150, -30), 0.12, 0.08, 20, LEAF, droop=-0.15)
        leaf(bm, (x + 0.08, -0.06, top + 0.1), rnd.uniform(-150, -30), 0.11, 0.07, 30, LEAF_DARK, droop=-0.15)


def bow(bm, c, s, col):
    x, y, z = c
    for k in (-1, 1):
        slab(bm, ellipse_pts(0.11 * s, 0.07 * s, 12, (x + k * 0.1 * s, z + 0.02 * s), k * 20), col, 0.05 * s, 0.025 * s, at=(0, y, 0))
        slab(bm, [(x + k * 0.02 * s, z), (x + k * 0.05 * s, z - 0.02 * s), (x + k * 0.12 * s, z - 0.17 * s), (x + k * 0.07 * s, z - 0.15 * s)],
             col, 0.035 * s, 0.01 * s, at=(0, y + 0.01, 0))
    ball2(bm, (x, y - 0.01 * s, z + 0.01 * s), 0.05 * s, col, (1, 0.8, 1))
def bow_post(bm):
    top = sq_post(bm, 1.05, CREAM, 0.2)
    box(bm, (0, 0, top + 0.06), (0.18, 0.18, 0.12), CREAM, taper=0.7)
    bow(bm, (0, -0.13, 0.93), 1.4, BUBBLE)
def bow_panel(bm):
    for z in (0.25, 0.6):
        box(bm, (SEG / 2, 0, z), (SEG, 0.07, 0.11), CREAM)
    for k, (sag, r, dz) in enumerate(((0.28, 0.05, 0.0), (0.22, 0.04, 0.05), (0.33, 0.035, -0.06))):
        pts = [(0.1 + 1.8 * i / 12, -0.07 - k * 0.012, 0.93 + dz * math.sin(math.pi * i / 12) - sag * math.sin(math.pi * i / 12)) for i in range(13)]
        tube(bm, pts, [r] * len(pts), PINK_SOFT, 8)


def logstar_post(bm):
    tube(bm, [(0, 0, 0), (0, 0, 0.6), (0, 0, 1.05)], [0.11, 0.105, 0.1], WOOD, 10, 0, 1.05)
    revolve(bm, [(0.085, 1.04), (0.07, 1.06)], LOG_END, (0, 0, 0), 10)
    for z in (0.26, 0.31, 0.75, 0.8):
        torus(bm, (0, 0, z), 0.11, 0.022, ROPE, 'Z', 12, 6)
def logstar_panel(bm):
    for z in (0.3, 0.78):
        tube(bm, [(0.0, -0.01, z), (SEG, -0.01, z)], [0.075, 0.075], WOOD, 10)
        for x in (0.17, 0.22, 1.78, 1.83):
            torus(bm, (x, -0.01, z), 0.078, 0.02, ROPE, 'X', 12, 6)
    pts = [(0.08 + 1.84 * i / 16, -0.1, 0.9 - 0.2 * math.sin(math.pi * i / 16)) for i in range(17)]
    tube(bm, pts, [0.009] * len(pts), IRON, 6)
    for i in (4, 8, 12):
        p = pts[i]
        tube(bm, [(p[0], p[1], p[2]), (p[0], p[1], p[2] - 0.06)], [0.008, 0.008], IRON, 6)
        glow(star5)(bm, (p[0], p[1], p[2] - 0.12), 0.07, GOLD, 0.045)


def tall_picket(bm, x, h, col, w=0.26, d=0.05, tip=0.13):
    picket(bm, x, h, col, w, d, tip)
def tulip(bm, x, y, z, col):
    tube(bm, [(x, y, z - 0.3), (x, y, z - 0.05)], [0.012, 0.012], LEAF_DARK, 6)
    for k in (-1, 1):
        slab(bm, ellipse_pts(0.07, 0.025, 10, (x + k * 0.06, z - 0.22), k * 50), LEAF, 0.02, 0.01, at=(0, y, 0))
    slab(bm, [(x - 0.06, z + 0.06), (x - 0.03, z + 0.02), (x, z + 0.07), (x + 0.03, z + 0.02), (x + 0.06, z + 0.06),
              (x + 0.055, z - 0.02), (x + 0.02, z - 0.06), (x - 0.02, z - 0.06), (x - 0.055, z - 0.02), (x - 0.06, z + 0.02)],
         col, 0.025, 0.012, at=(0, y, 0))
def tulip_post(bm):
    picket(bm, 0, 1.12, CREAM, w=0.2, d=0.07, tip=0.15)
    bolt(bm, (0, -0.045, 0.3)); bolt(bm, (0, -0.045, 0.75))
def tulip_panel(bm):
    rails(bm, (0.3, 0.75), CREAM, h=0.1, d=0.04, x0=0.0, x1=SEG)
    for i in range(5):
        x = (i + 1) * SEG / 6
        tall_picket(bm, x, 1.04 + (0.04 if i % 2 else 0), CREAM)
        tulip(bm, x, -0.04, 0.55, PINK if i % 2 else HOT_PINK)
        grass(bm, (x, -0.06, 0), 4, i + 50, 0.16)


def starp_post(bm):
    top = sq_post(bm, 1.0, LAVENDER, 0.22)
    box(bm, (0, 0, 0.9), (0.235, 0.235, 0.05), GOLD)
    box(bm, (0, -0.115, 0.5), (0.05, 0.02, 0.05), GOLD, roll=0, yaw=45)
    star5(bm, (0, 0, top + 0.14), 0.14, GOLD, 0.07)
def starp_panel(bm):
    box(bm, (SEG / 2, 0, 0.2), (SEG, 0.08, 0.12), LAVENDER)
    box(bm, (SEG / 2, 0, 0.88), (SEG, 0.08, 0.14), LAVENDER)
    box(bm, (SEG / 2, 0, 0.98), (0.6, 0.08, 0.12), LAVENDER, taper=0.85)
    for x in (0.3, 0.62, 1.38, 1.7):
        box(bm, (x, 0.01, 0.54), (0.13, 0.05, 0.6), LAVENDER)
    star5(bm, (1.0, -0.04, 0.54), 0.22, GOLD, 0.07)
    star5(bm, (0.46, -0.04, 0.54), 0.085, GOLD, 0.05)
    star5(bm, (1.54, -0.04, 0.54), 0.085, GOLD, 0.05)
    for x in (0.3, 0.62, 1.38, 1.7):
        box(bm, (x, -0.035, 0.88), (0.04, 0.02, 0.04), GOLD, yaw=0)


def hydra_post(bm):
    box(bm, (0, 0, 0.42), (0.32, 0.32, 0.84), LIGHT_STONE)
    box(bm, (0, 0, 0.9), (0.38, 0.38, 0.12), PINK, taper=0.8)
    box(bm, (0, -0.165, 0.55), (0.04, 0.02, 0.04), IRON)
def hydra_panel(bm):
    x0, x1 = 0.16, SEG - 0.16
    box(bm, (SEG / 2, 0, 0.27), (x1 - x0, 0.38, 0.5), TERRACOTTA)
    n = 7
    for i in range(n):
        xa = x0 + (x1 - x0) * i / n
        box(bm, (xa + (x1 - x0) / n / 2, -0.205, 0.27), ((x1 - x0) / n - 0.015, 0.05, 0.48), RUSTIC if i % 2 else WOOD)
    box(bm, (SEG / 2, 0, 0.53), (x1 - x0 + 0.04, 0.44, 0.06), DARKWOOD)
    rnd = random.Random(61)
    for i in range(9):
        x = x0 + 0.1 + (x1 - x0 - 0.2) * i / 8
        leaf(bm, (x, -0.2, 0.55), rnd.uniform(-150, -30), 0.15, 0.1, rnd.uniform(-10, 20), LEAF, droop=-0.3)
    for k, (x, y, z, r) in enumerate(((0.38, -0.06, 0.72, 0.17), (0.75, -0.08, 0.7, 0.18), (1.12, -0.07, 0.73, 0.17),
                                      (1.5, -0.06, 0.7, 0.17), (0.56, 0.08, 0.82, 0.16), (0.95, 0.08, 0.84, 0.17), (1.33, 0.08, 0.82, 0.16))):
        ball2(bm, (x, y, z), r, BUBBLE if k % 3 else c0(29, 0.9, 0.95), (1, 0.9, 0.9), 2, 0.14, 70 + k)


def paw_post(bm):
    wood_post(bm, 1.05, WOOD, w=0.2, bolts=(0.35, 0.8), seed=81)
    ivy(bm, 0.04, -0.11, 0.05, 0.6, 82, 4)
def paw_panel(bm):
    rails(bm, (0.35, 0.8), WOOD, h=0.13)
    box(bm, (1.0, -0.035, 0.575), (0.9, 0.05, 0.34), DARKWOOD)
    slab(bm, ellipse_pts(0.17, 0.14, 16, (1.0, 0.575)), CREAM, 0.04, 0.015, at=(0, -0.07, 0))
    slab(bm, ellipse_pts(0.06, 0.05, 12, (1.0, 0.545)), PINK, 0.02, 0.01, at=(0, -0.1, 0))
    for dx, dz in ((-0.075, 0.6), (-0.028, 0.635), (0.028, 0.635), (0.075, 0.6)):
        slab(bm, ellipse_pts(0.022, 0.028, 10, (1.0 + dx, dz)), PINK, 0.02, 0.008, at=(0, -0.1, 0))
    ivy(bm, 0.25, -0.05, 0.05, 0.4, 83, 4)


def quatre_post(bm):
    top = sq_post(bm, 0.98, CREAM, 0.22)
    ball2(bm, (0, 0, top + 0.09), 0.1, CREAM, (1, 1, 0.95), 2)
    ivy(bm, 0.0, -0.12, 0.05, 0.85, 91, 7, 0.08)
def quatre_panel(bm):
    box(bm, (SEG / 2, 0, 0.12), (SEG, 0.12, 0.12), CREAM)
    for i in range(3):
        xa = 0.1 + i * 0.6
        hc = (xa + 0.3, 0.48)
        outer = [(xa, 0.18), (xa + 0.6, 0.18), (xa + 0.6, 0.78), (xa, 0.78)]
        hole = polar(lambda a: 0.2 * (0.74 + 0.26 * math.cos(4 * a)), 40, hc)
        holed(bm, outer, hole, hc, 0.08, CREAM)
    band(bm, arch_pts(0.0, SEG, 0.82, 1.02), 0.1, 0.1, CREAM)
    for x in (0.4, 1.0, 1.6):
        z = arch_z(x, 0.0, SEG, 0.82, 1.02)
        box(bm, (x, 0, (0.78 + z) / 2), (0.08, 0.07, z - 0.78), CREAM)
    ivy(bm, 0.2, -0.07, 0.15, 0.7, 92, 5)
    ivy(bm, 1.8, -0.07, 0.1, 0.6, 93, 4)


def banner_post(bm):
    wood_post(bm, 1.05, WOOD, w=0.2, bolts=(0.2, 0.9), seed=101)
def banner_panel(bm):
    rails(bm, (0.2, 0.9), WOOD, h=0.13)
    for a, b_ in ((0.12, 0.92), (1.08, 1.88)):
        beam(bm, (a, 0.0, 0.26), (b_, 0.0, 0.84), 0.05, 0.1, WOOD)
        beam(bm, (a, 0.006, 0.84), (b_, 0.006, 0.26), 0.05, 0.1, WOOD)   # behind the other brace: they cross
    box(bm, (1.0, 0.0, 0.55), (0.12, 0.062, 0.62), WOOD)
    slab(bm, [(0.72, 0.96), (1.28, 0.96), (1.28, 0.5), (1.0, 0.38), (0.72, 0.5), (0.72, 0.73)], PINK_SOFT, 0.03, 0.01,
         center=(1.0, 0.7), at=(0, -0.07, 0))
    box(bm, (1.0, 0.0, 0.97), (0.58, 0.16, 0.03), PINK_SOFT)
    box(bm, (1.0, 0.075, 0.86), (0.56, 0.02, 0.2), PINK_SOFT)
    for x in (0.77, 1.23):
        box(bm, (x, -0.097, 0.73), (0.05, 0.015, 0.46), PINK)
    flat_flower(bm, (1.0, -0.1, 0.66), 0.1, PINK)


def heart_picket(bm, x, h, col, w=0.27, d=0.05, tip=0.14):
    outer = [(x - w / 2, 0), (x + w / 2, 0), (x + w / 2, h - tip), (x + 0.012, h), (x - 0.012, h), (x - w / 2, h - tip)]
    hc = (x, h * 0.75)
    holed(bm, outer, heart_pts(w * 0.72, hc, 32), hc, d, col)
def hearts_post(bm):
    heart_picket(bm, 0, 1.15, PINK_SOFT, 0.22, 0.07, 0.15)
def hearts_panel(bm):
    rails(bm, (0.2, 0.5), PINK, h=0.1, d=0.04, x0=0.0, x1=SEG)
    for i in range(5):
        x = (i + 1) * SEG / 6
        h = (1.0, 1.1, 1.02, 1.12, 0.98)[i]
        heart_picket(bm, x, h, PINK_SOFT)


def butterfly(bm, c, s, col):
    x, y, z = c
    for k in (-1, 1):
        slab(bm, ellipse_pts(0.13 * s, 0.1 * s, 12, (x + k * 0.11 * s, z + 0.06 * s), k * 25), col, 0.03 * s, 0.015 * s, at=(0, y, 0))
        slab(bm, ellipse_pts(0.09 * s, 0.07 * s, 12, (x + k * 0.08 * s, z - 0.09 * s), -k * 30), col, 0.03 * s, 0.015 * s, at=(0, y + 0.005, 0))
    ball2(bm, (x, y - 0.02 * s, z), 0.035 * s, LILAC, (0.7, 0.7, 2.6), 1)
def butter_post(bm):
    box(bm, (0, 0, 0.5), (0.26, 0.26, 1.0), LIGHT_STONE)
    box(bm, (0, 0, 1.04), (0.32, 0.32, 0.1), LIGHT_STONE, taper=0.85)
    ivy(bm, 0.05, -0.13, 0.05, 0.7, 111, 5)
    flat_flower(bm, (0.06, -0.16, 0.42), 0.05, LILAC_PALE)
    flat_flower(bm, (-0.04, -0.16, 0.2), 0.045, PINK_SOFT)
def butter_panel(bm):
    box(bm, (SEG / 2, 0, 0.15), (SEG, 0.1, 0.1), GREYBLUE)
    box(bm, (SEG / 2, 0, 0.93), (SEG, 0.1, 0.1), GREYBLUE)
    lattice(bm, 0.12, SEG - 0.12, 0.2, 0.88, GREYBLUE, 0.24, 0.045, 0.03)
    butterfly(bm, (1.0, -0.06, 1.08), 1.3, LILAC_PALE)
    flat_flower(bm, (1.7, -0.07, 0.95), 0.05, PINK_SOFT)


def lanternv_post(bm):
    top = sq_post(bm, 1.1, CREAM, 0.22)
    box(bm, (0, 0, top + 0.07), (0.17, 0.17, 0.14), CREAM, taper=0.7)
    beam(bm, (0, -0.1, 1.0), (0, -0.3, 1.0), 0.03, 0.03, IRON)
    beam(bm, (0, -0.1, 0.88), (0, -0.22, 1.0), 0.02, 0.02, IRON)
    lantern(bm, (0, -0.3, 1.0), 0.42)
    ivy(bm, 0.0, -0.12, 0.05, 0.6, 121, 4)
def lanternv_panel(bm):
    for z in (0.4, 0.8):
        tube(bm, [(0.0, 0.0, z), (SEG, 0.0, z)], [0.065, 0.065], WOOD, 10)
    vine_rail(bm, 0.12, 1.88, 0.8, -0.07, 122, CREAM)
    vine_rail(bm, 0.12, 1.88, 0.4, -0.07, 123, PINK_SOFT, 0.04)


def mushroom_post(bm):
    revolve(bm, [(0.15, 0.0), (0.16, 0.08), (0.14, 0.5), (0.12, 0.72)], CREAM, (0, 0, 0), 12)
    slab(bm, ellipse_pts(0.045, 0.07, 10, (0, 0.24)), DARKWOOD, 0.02, 0.008, at=(0, -0.145, 0))
    revolve(bm, [(0.05, 0.66), (0.33, 0.7), (0.32, 0.8), (0.26, 0.92), (0.15, 1.0), (0.05, 1.03)], MUSH_RED, (0, 0, 0), 14)
    for a, rr, z in ((-90, 0.27, 0.82), (-40, 0.25, 0.85), (-140, 0.25, 0.85), (-65, 0.15, 0.97), (-115, 0.15, 0.97), (20, 0.26, 0.83), (160, 0.26, 0.83), (90, 0.2, 0.92)):
        ax = math.radians(a)
        ball2(bm, (rr * math.cos(ax), rr * math.sin(ax), z), 0.04, CREAM, (1, 1, 0.55))
def mushroom_panel(bm):
    rails(bm, (0.3, 0.62), WOOD, h=0.1, d=0.04, x0=0.1, x1=SEG - 0.1)
    for i, x in enumerate((0.5, 0.83, 1.17, 1.5)):
        picket(bm, x, 0.85 + (0.05 if i % 2 else 0), CREAM, 0.17, 0.04, 0.12)
        flat_flower(bm, (x, -0.04, 0.7), 0.035, PINK_SOFT)
    rnd = random.Random(131)
    for i, x in enumerate((0.3, 0.65, 1.0, 1.35, 1.7)):
        grass(bm, (x, -0.08, 0), 4, 130 + i, 0.18)
        flat_flower(bm, (x + 0.05, -0.14, 0.12 + rnd.uniform(0, 0.06)), 0.05, CREAM)


def stump(bm, x, y, h, r, seed):
    revolve(bm, [(r * 1.08, 0.0), (r, 0.06), (r * 0.98, h * 0.6), (r, h)], WOOD, (x, y, 0), 12)
    revolve(bm, [(r * 0.85, h - 0.01), (r * 0.8, h + 0.015)], LOG_END, (x, y, 0), 12)
    for z in (h * 0.3, h * 0.72):
        torus(bm, (x, y, z), r * 1.03, 0.022, ROPE, 'Z', 14, 6)
def stumps_post(bm):
    stump(bm, 0, 0, 1.05, 0.2, 141)
def stumps_panel(bm):
    for i, (x, h, r) in enumerate(((0.41, 0.72, 0.2), (0.82, 0.88, 0.2), (1.2, 0.66, 0.18), (1.59, 0.8, 0.2))):
        stump(bm, x, 0.0, h, r, 142 + i)
    mushroom(bm, (1.0, -0.22, 0), 0.9, 1)
    flat_flower(bm, (1.5, -0.24, 0.1), 0.05, CREAM)
    flat_flower(bm, (1.62, -0.24, 0.16), 0.045, CREAM)
    grass(bm, (1.55, -0.22, 0), 5, 148, 0.18)
    grass(bm, (0.6, -0.22, 0), 4, 149, 0.16)


def baluster(bm, x, z0, z1, col):
    h = z1 - z0
    prof = [(0.05, 0), (0.05, 0.06), (0.035, 0.1), (0.06, 0.35), (0.045, 0.62), (0.03, 0.72), (0.045, 0.9), (0.05, 1.0)]
    revolve(bm, [(r, z0 + t * h) for r, t in prof], col, (x, 0, 0), 10)
def balus_post(bm):
    box(bm, (0, 0, 0.05), (0.3, 0.3, 0.1), CREAM)
    box(bm, (0, 0, 0.45), (0.25, 0.25, 0.8), CREAM)
    box(bm, (0, 0, 0.92), (0.29, 0.29, 0.14), LILAC_PALE)
    box(bm, (0, 0, 1.05), (0.22, 0.22, 0.12), CREAM, taper=0.8)
    ivy(bm, 0.04, -0.13, 0.05, 0.85, 151, 6)
    flat_flower(bm, (0.05, -0.16, 0.6), 0.045, LILAC_PALE)
def balus_panel(bm):
    box(bm, (SEG / 2, 0, 0.08), (SEG, 0.2, 0.16), CREAM)
    band(bm, arch_pts(0.0, SEG, 0.78, 0.95), 0.16, 0.1, CREAM)
    for x in (0.4, 0.7, 1.0, 1.3, 1.6):
        baluster(bm, x, 0.16, arch_z(x, 0.0, SEG, 0.78, 0.95) - 0.04, CREAM)
    ivy(bm, 1.85, -0.1, 0.1, 0.7, 152, 5)


def stonehedge_post(bm):
    stone_pillar(bm, 1.15, 0.36, LIGHT_STONE, LIGHT_STONE, seed=161, rows=5)
def stonehedge_panel(bm):
    leafy(bm, 0.18, SEG - 0.18, 0.05, 1.0, 0.4, seed=162)
    rnd = random.Random(163)
    for i in range(11):
        x = 0.3 + 1.4 * i / 10 + rnd.uniform(-0.04, 0.04)
        flat_flower(bm, (x, -0.3, 0.2 + 0.7 * ((i * 0.37) % 1)), 0.045, CREAM)


def cloud_pts(circles, base, c, n=48):
    def inside(px, pz):
        if base[0] <= px <= base[1] and base[2] <= pz <= base[3]:
            return True
        return any((px - cx) ** 2 + (pz - cz) ** 2 <= r * r for cx, cz, r in circles)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        d = (math.cos(a), math.sin(a))
        t = 0.0
        while inside(c[0] + d[0] * (t + 0.01), c[1] + d[1] * (t + 0.01)):
            t += 0.01
        pts.append((c[0] + d[0] * t, c[1] + d[1] * t))
    return pts
def cloud_post(bm):
    top = sq_post(bm, 1.0, CREAM, 0.2)
    star5(bm, (0, 0, top + 0.14), 0.13, GOLD, 0.07)
def cloud_panel(bm):
    for k, col in enumerate(RAINBOW):
        r = 0.72 - k * 0.082   # bands 0.08 high: never overlapping their neighbours
        pts = [(1.0 + r * math.cos(math.pi * i / 16), 0.03, 0.32 + r * math.sin(math.pi * i / 16)) for i in range(17)]
        band(bm, pts, 0.09, 0.08, col)
    circles = [(0.3, 0.26, 0.22), (0.62, 0.36, 0.27), (1.0, 0.3, 0.25), (1.36, 0.38, 0.27), (1.7, 0.26, 0.22)]
    slab(bm, cloud_pts(circles, (0.1, 1.9, 0.0, 0.26), (1.0, 0.25)), CLOUD, 0.26, 0.05, 0.7, center=(1.0, 0.25), at=(0, -0.02, 0))
    star5(bm, (0.55, -0.2, 0.32), 0.1, GOLD, 0.05)
    star5(bm, (1.42, -0.2, 0.36), 0.07, GOLD, 0.04)


FENCES2 = [
    ("Picket_Roses", roses_post, roses_panel),
    ("Heart_Rail", heartrail_post, heartrail_panel),
    ("Scroll_Arch", scroll_post, scroll_panel),
    ("Wisteria_Lattice", wisteria_post, wisteria_panel),
    ("Bow_Drape", bow_post, bow_panel),
    ("Log_StarLights", logstar_post, logstar_panel),
    ("Picket_Tulips", tulip_post, tulip_panel),
    ("Star_Purple", starp_post, starp_panel),
    ("Hydrangea_Planter", hydra_post, hydra_panel),
    ("Paw_Rail", paw_post, paw_panel),
    ("Quatrefoil_Ivy", quatre_post, quatre_panel),
    ("Banner_Cross", banner_post, banner_panel),
    ("Picket_Hearts", hearts_post, hearts_panel),
    ("Butterfly_Lattice", butter_post, butter_panel),
    ("Lantern_Vine", lanternv_post, lanternv_panel),
    ("Mushroom_Picket", mushroom_post, mushroom_panel),
    ("Log_Stumps", stumps_post, stumps_panel),
    ("Balustrade_Lilac", balus_post, balus_panel),
    ("Stone_Hedge", stonehedge_post, stonehedge_panel),
    ("Cloud_Rainbow", cloud_post, cloud_panel),
]


def build_fences2(only=None):
    root = bpy.data.collections.get("Fences") or bpy.data.collections.new("Fences")
    if root.name not in [c.name for c in bpy.context.scene.collection.children]:
        bpy.context.scene.collection.children.link(root)
    objs = []
    for row, (name, post, panel) in enumerate(FENCES2):
        if only and name not in only:
            continue
        sub = bpy.data.collections.get("Fence_" + name) or bpy.data.collections.new("Fence_" + name)
        if sub.name not in [c.name for c in root.children]:
            root.children.link(sub)
        y = -14 - (len(FENCES) + row) * 2.0
        bm = bmesh.new()
        post(bm)
        panel(bm)
        objs.append(finish_lamp(bm, "SM_Fence_" + name, sub, (0, y, 0)))
        bm = bmesh.new()
        post(bm)
        objs.append(finish_lamp(bm, "SM_Fence_%s_Post" % name, sub, (SEG, y, 0)))
    return check_closed(objs)
