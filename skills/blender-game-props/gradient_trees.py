# Fruit trees in the NewLua Studios stylized farm pack style (gradient atlas, quads only, smooth).
# Run inside the pack .blend (Blender MCP execute_blender_code):
#   exec(open(r"<skills>/blender-game-props/gradient_trees.py").read())
#   build_trees()                 # all types, or build_trees(["Apple", "Peach"])
# Each type makes SM_<Type>Tree_Stage1..4 (Stage4 carries the fruit) + the fruit item SM_<Fruit>,
# in collection Trees > Tree_<Type>, one row per type. The seed (SM_Tree_Seed) is shared.
# Swap a tree's fruit: change the fruit function in TYPES (any f_* works on any shape).
import bpy, bmesh, math, random
from mathutils import Vector, Matrix
from collections import Counter

CW = 57 / 2048  # atlas column width


def c0(k, v0=0.85, v1=0.995):  # top-row atlas column k
    return ((k + 0.5) * CW, v0, v1)


def c1(k, v0=0.69, v1=0.835):  # second-row atlas column k
    return ((k + 0.5) * CW, v0, v1)


BARK = c1(2, 0.69, 0.79)
BARK_DARK = c0(35, 0.86, 0.99)
PALM_BARK = c1(1, 0.69, 0.765)
LEAFY = c0(9)


def uv_part(b, column, zmin=None, zmax=None, flip=False):
    u, v0, v1 = column
    uvl = b.loops.layers.uv.verify()
    zs = [v.co.z for v in b.verts]
    lo = min(zs) if zmin is None else zmin
    hi = max(zs) if zmax is None else zmax
    for f in b.faces:
        for l in f.loops:
            t = max(0.0, min(1.0, (l.vert.co.z - lo) / max(hi - lo, 1e-6)))
            if flip:
                t = 1 - t
            l[uvl].uv = (u, v0 + (v1 - v0) * t)


def orient_outward(b):
    """Makes a closed piece's normals point outward: recalculate, then check with the signed volume
    and flip everything if it came out inside-out (thin shapes like leaves can fool the recalc)."""
    bmesh.ops.recalc_face_normals(b, faces=b.faces)
    vol = sum(f.calc_center_median().dot(f.normal) * f.calc_area() for f in b.faces)
    if vol < 0:
        bmesh.ops.reverse_faces(b, faces=b.faces)


def merge(bm, b):
    orient_outward(b)
    t = bpy.data.meshes.new("_t")
    b.to_mesh(t)
    b.free()
    bm.from_mesh(t)
    bpy.data.meshes.remove(t)


def quad_sphere(r, cuts=2, scale=(1, 1, 1), jitter=0.06, seed=0):
    rnd = random.Random(seed)
    b = bmesh.new()
    bmesh.ops.create_cube(b, size=2.0)
    if cuts:
        bmesh.ops.subdivide_edges(b, edges=b.edges[:], cuts=cuts, use_grid_fill=True)
    for v in b.verts:
        n = v.co.normalized() * r * (1 + rnd.uniform(-jitter, jitter))
        v.co = Vector((n.x * scale[0], n.y * scale[1], n.z * scale[2]))
    return b


def blob(bm, c, r, col, seed, scale=(1, 1, 0.85), cuts=2, flip=False):
    b = quad_sphere(r, cuts, scale, 0.07, seed)
    bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
    uv_part(b, col, flip=flip)
    merge(bm, b)


def quad_cap(b, ring):
    """Closes a ring with quads only (even vertex count): strips across the ring, no n-gon or fan."""
    n = len(ring)
    for i in range(n // 2 - 1):
        b.faces.new((ring[i], ring[i + 1], ring[n - 2 - i], ring[n - 1 - i]))


def tube(bm, pts, radii, col, sides=8, zmin=None, zmax=None):
    """Closed quad tube along points: both ends capped with quads, so there are no holes and the
    normals can always be worked out to point outward. Odd side counts are rounded up."""
    sides += sides % 2
    b = bmesh.new()
    rings = []
    # Ring orientation is carried along the path (parallel transport): each ring is the previous
    # one turned only as much as the path bends, so the faces never corkscrew (twist).
    tangents = [(Vector(pts[min(i + 1, len(pts) - 1)]) - Vector(pts[max(i - 1, 0)])).normalized() for i in range(len(pts))]
    q = tangents[0].to_track_quat('Z', 'Y')
    ax, ay = q @ Vector((1, 0, 0)), q @ Vector((0, 1, 0))
    for i, (p, r) in enumerate(zip(pts, radii)):
        p = Vector(p)
        if i > 0:
            turn = tangents[i - 1].rotation_difference(tangents[i])
            ax, ay = turn @ ax, turn @ ay
        rings.append([b.verts.new(p + ax * (r * math.cos(2 * math.pi * k / sides)) + ay * (r * math.sin(2 * math.pi * k / sides))) for k in range(sides)])
    for s in range(len(rings) - 1):
        for k in range(sides):
            b.faces.new((rings[s][k], rings[s][(k + 1) % sides], rings[s + 1][(k + 1) % sides], rings[s + 1][k]))
    quad_cap(b, rings[0])
    quad_cap(b, rings[-1])
    bmesh.ops.recalc_face_normals(b, faces=b.faces)
    uv_part(b, col, zmin, zmax)
    merge(bm, b)


def leaf(bm, base, yaw, length, width, tilt, col, droop=0.25, segs=None):
    """A leaf as a thin closed slab of quads (top, bottom, sides, both ends), so it shows from both
    sides in engines that hide back faces. droop > 0 curls the tip up, < 0 hangs it down."""
    b = bmesh.new()
    prof = segs or [(0.0, 0.18), (0.35, 1.0), (0.75, 0.7), (1.0, 0.08)]
    th = max(0.006, width * 0.06) / 2
    # per row: top-left, top-right, bottom-right, bottom-left
    rows = [[b.verts.new((t * length, -w * width / 2, th)), b.verts.new((t * length, w * width / 2, th)),
             b.verts.new((t * length, w * width / 2, -th)), b.verts.new((t * length, -w * width / 2, -th))] for t, w in prof]
    for i in range(len(rows) - 1):
        a, n = rows[i], rows[i + 1]
        for k in range(4):
            b.faces.new((a[k], n[k], n[(k + 1) % 4], a[(k + 1) % 4]))
    b.faces.new(rows[0][::-1])
    b.faces.new(rows[-1])
    for v in b.verts:
        v.co.z += droop * (v.co.x ** 2) / max(length, 1e-6)
    bmesh.ops.rotate(b, cent=Vector(), matrix=Matrix.Rotation(math.radians(-tilt), 3, 'Y'), verts=b.verts)
    bmesh.ops.rotate(b, cent=Vector(), matrix=Matrix.Rotation(math.radians(yaw), 3, 'Z'), verts=b.verts)
    bmesh.ops.translate(b, vec=Vector(base), verts=b.verts)
    uv_part(b, col)
    merge(bm, b)


def trunk(bm, h, r0, r1, bend, col=BARK):
    pts = [(0, 0, 0), (0, 0, h * 0.06)] + [(bend * t * t, 0, h * t) for t in (0.3, 0.6, 1.0)]
    tube(bm, pts, [r0 * 1.7, r0 * 1.2, r0, (r0 + r1) / 2, r1], col, zmin=0, zmax=h)
    return Vector(pts[-1])


# ---------------- fruits: f(bm, centre, radius, seed) ----------------
def f_apple(bm, c, r, sd):
    b = quad_sphere(r, 1, (1, 1, 0.92), 0.03, sd)
    for v in b.verts:
        if v.co.z > r * 0.8:
            v.co.z -= r * 0.18
    bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
    uv_part(b, c0(6, 0.86, 0.96))
    merge(bm, b)
    tube(bm, [(c[0], c[1], c[2] + r * 0.6), (c[0] + r * 0.08, c[1], c[2] + r * 1.25)], [r * 0.1, r * 0.07], BARK_DARK, sides=4)
    leaf(bm, (c[0], c[1], c[2] + r * 1.05), random.Random(sd).uniform(0, 360), r * 0.9, r * 0.5, 15, LEAFY)


def f_orange(bm, c, r, sd):
    b = quad_sphere(r, 1, (1, 1, 0.93), 0.02, sd)
    bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
    uv_part(b, c0(10, 0.86, 0.97))
    merge(bm, b)
    leaf(bm, (c[0], c[1], c[2] + r * 0.9), random.Random(sd).uniform(0, 360), r * 0.8, r * 0.45, 10, c0(13))


def f_lemon(bm, c, r, sd):
    b = quad_sphere(r, 1, (1.35, 0.95, 0.95), 0.02, sd)
    for v in b.verts:
        if abs(v.co.x) > r * 1.2:
            v.co.x *= 1.12
    bmesh.ops.rotate(b, cent=Vector(), matrix=Matrix.Rotation(math.radians(random.Random(sd).uniform(0, 180)), 3, 'Z'), verts=b.verts)
    bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
    uv_part(b, c0(23, 0.87, 0.99))
    merge(bm, b)


def f_cherry(bm, c, r, sd):
    for dx in (-0.55, 0.55):
        p = (c[0] + dx * r, c[1], c[2] - r * 0.2)
        b = quad_sphere(r * 0.6, 1, (1, 1, 0.95), 0.02, sd)
        bmesh.ops.translate(b, vec=Vector(p), verts=b.verts)
        uv_part(b, c0(14, 0.88, 0.99))
        merge(bm, b)
        tube(bm, [(p[0], p[1], p[2] + r * 0.5), (c[0], c[1], c[2] + r * 1.3)], [r * 0.06, r * 0.05], BARK_DARK, sides=4)


def f_pear(bm, c, r, sd):
    b = quad_sphere(r, 2, (1, 1, 1.25), 0.02, sd)
    for v in b.verts:
        t = (v.co.z / (r * 1.25) + 1) / 2
        k = 1.0 if t < 0.45 else 1.0 - 0.55 * (t - 0.45) / 0.55
        v.co.x *= k
        v.co.y *= k
    bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
    uv_part(b, c0(3, 0.86, 0.99))
    merge(bm, b)
    tube(bm, [(c[0], c[1], c[2] + r * 1.15), (c[0] + r * 0.1, c[1], c[2] + r * 1.6)], [r * 0.09, r * 0.06], BARK_DARK, sides=4)


def f_coconut(bm, c, r, sd):
    b = quad_sphere(r, 1, (1, 1, 1.12), 0.04, sd)
    bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
    uv_part(b, c0(35, 0.88, 0.995))
    merge(bm, b)


def f_plum(bm, c, r, sd):
    b = quad_sphere(r, 1, (0.95, 0.95, 1.12), 0.02, sd)
    bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
    uv_part(b, c1(3, 0.69, 0.78))
    merge(bm, b)
    tube(bm, [(c[0], c[1], c[2] + r * 0.9), (c[0], c[1], c[2] + r * 1.35)], [r * 0.08, r * 0.06], BARK_DARK, sides=4)


def f_peach(bm, c, r, sd):
    b = quad_sphere(r, 2, (1, 1, 0.97), 0.02, sd)
    for v in b.verts:
        if v.co.x > r * 0.6 and abs(v.co.y) < r * 0.25:
            v.co.x -= r * 0.12
    bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
    uv_part(b, c0(27, 0.87, 0.99), flip=True)
    merge(bm, b)
    leaf(bm, (c[0], c[1], c[2] + r * 0.95), random.Random(sd).uniform(0, 360), r * 0.9, r * 0.5, 15, LEAFY)


def hang(bm, blobs, fruit, n, r, seed, lower=-0.6, upper=0.2):
    """n fruits on the surface of the canopy blobs, mostly on the lower half."""
    rnd = random.Random(seed)
    for i in range(n):
        c, br = blobs[i % len(blobs)]
        a = rnd.uniform(0, 2 * math.pi)
        h = rnd.uniform(lower, upper)
        rr = br * math.sqrt(max(0.0, 1 - h * h)) + r * 0.35
        fruit(bm, (c[0] + rr * math.cos(a), c[1] + rr * math.sin(a), c[2] + br * h * 0.85), r, seed * 100 + i)


FRUIT_R = 0.15  # final-stage fruit radius (m)


# ---------------- tree shapes: shape(bm, s, fruit_or_None, leaf_column); s = 1 is the ~3 m tree --------
def t_apple(bm, s, fruit, L):  # round clustered canopy
    top = trunk(bm, 1.5 * s, 0.13 * s, 0.07 * s, 0.1 * s)
    tube(bm, [(0.03 * s, 0, 0.9 * s), (0.45 * s, 0.1 * s, 1.5 * s)], [0.06 * s, 0.035 * s], BARK, 6, 0, 1.5 * s)
    tube(bm, [(0.03 * s, 0, 1.05 * s), (-0.42 * s, -0.08 * s, 1.55 * s)], [0.055 * s, 0.03 * s], BARK, 6, 0, 1.5 * s)
    bl = [((top.x, 0, 2.15 * s), 0.72 * s), ((0.55 * s, 0.12 * s, 1.72 * s), 0.48 * s), ((-0.52 * s, -0.1 * s, 1.75 * s), 0.46 * s),
          ((0.05 * s, 0.52 * s, 1.8 * s), 0.43 * s), ((0.02 * s, -0.52 * s, 1.82 * s), 0.42 * s)]
    for i, (c, r) in enumerate(bl):
        blob(bm, c, r, L, 10 + i)
    if fruit:
        hang(bm, bl, fruit, 12, FRUIT_R, 1)


def t_orange(bm, s, fruit, L):  # dense pom-pom ball
    trunk(bm, 1.2 * s, 0.12 * s, 0.08 * s, 0.03 * s)
    blob(bm, (0, 0, 2.0 * s), 0.95 * s, L, 20, (1, 1, 0.92), cuts=3)
    rnd = random.Random(4)
    for i in range(10):
        a = 2 * math.pi * i / 10 + rnd.uniform(-0.2, 0.2)
        h = rnd.uniform(-0.3, 0.7)
        R = 0.95 * s * 0.92
        blob(bm, (R * math.cos(a) * math.sqrt(1 - h * h), R * math.sin(a) * math.sqrt(1 - h * h), 2.0 * s + R * h * 0.9), 0.32 * s, L, 30 + i)
    if fruit:
        hang(bm, [((0, 0, 2.0 * s), 1.08 * s)], fruit, 14, FRUIT_R, 2, -0.55, 0.55)


def t_lemon(bm, s, fruit, L):  # upright oval
    trunk(bm, 1.1 * s, 0.11 * s, 0.06 * s, 0.02 * s)
    bl = [((0, 0, 1.6 * s), 0.6 * s), ((0.05 * s, 0.03 * s, 2.25 * s), 0.55 * s), ((0.0, -0.02 * s, 2.8 * s), 0.38 * s)]
    for i, (c, r) in enumerate(bl):
        blob(bm, c, r, L, 40 + i, (1, 1, 1.15))
    if fruit:
        hang(bm, bl[:2], fruit, 12, FRUIT_R * 0.9, 3, -0.6, 0.5)


def t_cherry(bm, s, fruit, L):  # wide flat umbrella
    trunk(bm, 1.1 * s, 0.14 * s, 0.09 * s, 0.0, BARK_DARK)
    bl = [((0, 0, 1.95 * s), 0.6 * s)]
    for i in range(5):
        a = 2 * math.pi * i / 5 + 0.3
        tube(bm, [(0, 0, 1.0 * s), (0.75 * s * math.cos(a), 0.75 * s * math.sin(a), 1.65 * s)], [0.06 * s, 0.035 * s], BARK_DARK, 6, 0, 1.6 * s)
        bl.append(((0.95 * s * math.cos(a), 0.95 * s * math.sin(a), 1.75 * s), 0.5 * s))
    for i, (c, r) in enumerate(bl):
        blob(bm, c, r, L, 50 + i, (1.15, 1.15, 0.55))
    if fruit:
        hang(bm, bl, fruit, 14, FRUIT_R * 0.95, 4, -0.9, -0.2)


def t_pear(bm, s, fruit, L):  # tall narrow column
    trunk(bm, 0.9 * s, 0.11 * s, 0.07 * s, 0.02 * s)
    bl = [((0, 0, 1.35 * s), 0.55 * s), ((0.03 * s, 0, 1.95 * s), 0.52 * s), ((0, 0.02 * s, 2.55 * s), 0.42 * s), ((0, 0, 3.05 * s), 0.27 * s)]
    for i, (c, r) in enumerate(bl):
        blob(bm, c, r, L, 60 + i, (0.95, 0.95, 1.25))
    if fruit:
        hang(bm, bl[:3], fruit, 11, FRUIT_R, 5, -0.5, 0.4)


def t_coconut(bm, s, fruit, L):  # curved palm, drooping fronds
    pts = [(0.4 * s * (t ** 1.8), 0, 2.9 * s * t) for t in (0, 0.06, 0.25, 0.45, 0.65, 0.85, 1.0)]
    radii = [0.17 * s, 0.13 * s, 0.11 * s, 0.1 * s, 0.09 * s, 0.085 * s, 0.08 * s]
    tube(bm, pts, radii, PALM_BARK, 8, 0, 2.9 * s)
    for i in range(1, len(pts) - 1):
        tube(bm, [Vector(pts[i]) - Vector((0, 0, 0.03 * s)), Vector(pts[i]) + Vector((0, 0, 0.03 * s))], [radii[i] * 1.18] * 2, BARK_DARK, 8)
    top = Vector(pts[-1])
    for i in range(8):
        leaf(bm, top + Vector((0, 0, 0.04 * s)), 360 * i / 8 + 10, 1.5 * s, 0.42 * s, 12 + (i % 2) * 10, L, droop=-0.55,
             segs=[(0, 0.2), (0.2, 0.8), (0.45, 1.0), (0.7, 0.75), (1.0, 0.1)])
    if fruit:
        for i in range(5):
            a = 2 * math.pi * i / 5
            fruit(bm, (top.x + 0.17 * math.cos(a), 0.17 * math.sin(a), top.z - 0.16), 0.17, 600 + i)


def t_plum(bm, s, fruit, L):  # low bushy, three trunks
    bl = []
    for a, lean, h in ((0.3, 0.45, 1.3), (2.4, 0.5, 1.15), (4.4, 0.4, 1.4)):
        dx, dy = math.cos(a) * lean * s, math.sin(a) * lean * s
        tube(bm, [(0, 0, 0), (dx * 0.3, dy * 0.3, h * 0.4 * s), (dx, dy, h * s)], [0.12 * s, 0.08 * s, 0.05 * s], BARK, 7, 0, h * s)
        bl.append(((dx * 1.1, dy * 1.1, (h + 0.35) * s), 0.55 * s))
    bl.append(((0, 0, 1.95 * s), 0.55 * s))
    for i, (c, r) in enumerate(bl):
        blob(bm, c, r, L, 70 + i, (1.1, 1.1, 0.8))
    if fruit:
        hang(bm, bl, fruit, 13, FRUIT_R * 0.95, 6, -0.75, 0.1)


def t_peach(bm, s, fruit, L):  # twisty trunk, cloud pads
    pts = [(0, 0, 0), (0, 0, 0.1 * s), (0.25 * s, 0.1 * s, 0.7 * s), (-0.15 * s, 0.05 * s, 1.35 * s), (0.2 * s, -0.05 * s, 2.0 * s), (0.05 * s, 0, 2.5 * s)]
    tube(bm, pts, [0.2 * s, 0.14 * s, 0.11 * s, 0.09 * s, 0.07 * s, 0.05 * s], BARK_DARK, 8, 0, 2.5 * s)
    pads = [((0.6 * s, 0.15 * s, 1.35 * s), 0.55 * s), ((-0.6 * s, -0.1 * s, 1.85 * s), 0.55 * s), ((0.1 * s, 0, 2.6 * s), 0.6 * s)]
    tube(bm, [(0.2 * s, 0.08 * s, 0.9 * s), (0.6 * s, 0.15 * s, 1.25 * s)], [0.06 * s, 0.04 * s], BARK_DARK, 6, 0, 2.5 * s)
    tube(bm, [(-0.1 * s, 0.05 * s, 1.5 * s), (-0.6 * s, -0.1 * s, 1.75 * s)], [0.06 * s, 0.04 * s], BARK_DARK, 6, 0, 2.5 * s)
    for i, (c, r) in enumerate(pads):
        blob(bm, c, r, L, 80 + i, (1.3, 1.3, 0.68))
    if fruit:
        hang(bm, pads, fruit, 12, FRUIT_R, 7, -0.95, -0.3)


# ---------------- seasonal: Halloween (spooky dead tree + jack-o'-lanterns) ----------------
SPOOKY_BARK = c0(30, 0.94, 0.998)     # near-black purple
PUMPKIN = c0(8, 0.88, 0.99)           # orange
GLOW = c0(23, 0.975, 0.995)           # bright yellow (the carved face)


def f_jack(bm, c, r, sd):
    """Ribbed pumpkin with a glowing face, facing away from the tree's centre."""
    # carve on the cube grid first (6 x 6 cells on the +X side), then round it into a pumpkin
    b = bmesh.new()
    bmesh.ops.create_cube(b, size=2.0)
    bmesh.ops.subdivide_edges(b, edges=b.edges[:], cuts=5, use_grid_fill=True)
    carved = set()
    for f in b.faces:
        m = f.calc_center_median()
        if m.x < 0.99:
            continue
        y, z = round(m.y * 6) / 6, round(m.z * 6) / 6
        eye = abs(abs(y) - 0.5) < 0.05 and (abs(z - 0.17) < 0.05 or abs(z - 0.5) < 0.05)
        mouth = (abs(z + 0.5) < 0.05 and abs(y) < 0.7) or (abs(z + 0.17) < 0.05 and abs(abs(y) - 0.83) < 0.05)
        if eye or mouth:
            carved.add(f.index)
    for v in b.verts:
        n = v.co.normalized() * r
        a = math.atan2(n.y, n.x)
        k = 1 + 0.07 * math.cos(8 * a)
        v.co = Vector((n.x * 1.08 * k, n.y * 1.08 * k, n.z * 0.82))
    uv_part(b, PUMPKIN)
    uvl = b.loops.layers.uv.verify()
    b.faces.ensure_lookup_table()
    for i in carved:
        f = b.faces[i]
        for l in f.loops:
            l[uvl].uv = (GLOW[0], GLOW[2])
    # push the carved cells in a little so they read as cut out
    inner = {v for i in carved for v in b.faces[i].verts}
    for v in inner:
        v.co *= 0.96
    yaw = math.atan2(c[1], c[0]) if (abs(c[0]) + abs(c[1])) > 1e-4 else 0.0
    bmesh.ops.rotate(b, cent=Vector(), matrix=Matrix.Rotation(yaw, 3, 'Z'), verts=b.verts)
    bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
    merge(bm, b)
    tube(bm, [(c[0], c[1], c[2] + r * 0.7), (c[0] + r * 0.12, c[1], c[2] + r * 1.15)], [r * 0.14, r * 0.09], BARK_DARK, sides=5)


def t_halloween(bm, s, fruit, L):
    rnd = random.Random(13)
    # gnarled trunk that twists as it rises
    pts = [(0, 0, 0), (0.05 * s, 0, 0.15 * s), (0.22 * s, 0.1 * s, 0.6 * s), (-0.12 * s, 0.05 * s, 1.15 * s), (0.15 * s, -0.12 * s, 1.7 * s), (0.0, 0.0, 2.2 * s)]
    tube(bm, pts, [0.3 * s, 0.2 * s, 0.15 * s, 0.13 * s, 0.1 * s, 0.06 * s], SPOOKY_BARK, 8, 0, 2.2 * s)
    # spreading roots
    for i in range(5):
        a = 2 * math.pi * i / 5 + 0.4
        tube(bm, [(0.12 * s * math.cos(a), 0.12 * s * math.sin(a), 0.2 * s), (0.45 * s * math.cos(a + 0.2), 0.45 * s * math.sin(a + 0.2), 0.04 * s),
                  (0.75 * s * math.cos(a + 0.4), 0.75 * s * math.sin(a + 0.4), 0.0)], [0.08 * s, 0.05 * s, 0.012 * s], SPOOKY_BARK, 6, 0, 2.2 * s)
    # clawed branches: (start height, direction angle, length, rise)
    tips = []
    for h, a, ln, rise in ((1.0, 0.3, 1.0, 0.5), (1.3, 2.4, 1.05, 0.65), (1.6, 4.3, 0.95, 0.75), (1.85, 1.3, 0.8, 0.85), (2.1, 3.4, 0.7, 0.9), (2.2, 5.6, 0.55, 0.7)):
        base = Vector((rnd.uniform(-0.05, 0.05) * s, rnd.uniform(-0.05, 0.05) * s, h * s))
        d = Vector((math.cos(a), math.sin(a), 0))
        side = Vector((-d.y, d.x, 0)) * 0.18 * s
        p1 = base + d * ln * 0.35 * s + Vector((0, 0, rise * 0.25 * s)) + side
        p2 = base + d * ln * 0.7 * s + Vector((0, 0, rise * 0.55 * s)) - side
        p3 = base + d * ln * s + Vector((0, 0, rise * s))
        tube(bm, [base, p1, p2, p3], [0.07 * s, 0.045 * s, 0.025 * s, 0.006 * s], SPOOKY_BARK, 6, 0, 3.1 * s)
        # a hooked twig off each branch
        q = p2 + Vector((-d.y, d.x, 0)) * 0.3 * s + Vector((0, 0, 0.25 * s))
        tube(bm, [p1 + (p2 - p1) * 0.5, q, q + d * 0.15 * s - Vector((0, 0, 0.08 * s))], [0.025 * s, 0.012 * s, 0.004 * s], SPOOKY_BARK, 5, 0, 3.1 * s)
        tips.append(p1 + (p2 - p1) * 0.6)
    if fruit:   # jack-o'-lanterns hanging on vines from the branches
        for i, t in enumerate(tips):
            drop = 0.35 + 0.15 * (i % 2)
            c = t - Vector((0, 0, drop))
            tube(bm, [t, t - Vector((0, 0, drop * 0.5)), c + Vector((0, 0, 0.15))], [0.012, 0.01, 0.008], c0(31, 0.86, 0.95), 4)
            fruit(bm, (c.x, c.y, c.z), 0.17, 1300 + i)


# ---------------- seasonal: Christmas (pine + star + gifts) ----------------
PINE = c0(13, 0.85, 0.99)
STAR_GOLD = c0(23, 0.9, 0.995)
GIFT_COLS = [c0(6, 0.88, 0.99), c0(21, 0.87, 0.99), c1(3, 0.70, 0.79), c0(29, 0.87, 0.99), c0(13, 0.88, 0.99), c0(33, 0.87, 0.99)]
RIBBON = [c0(23, 0.93, 0.995), c0(18, 0.85, 0.87)]   # gold, white


def lathe(bm, profile, col, sides=16, spiky=0.0, seed=0):
    """Quad surface of revolution from a (radius, z) profile; spiky pushes every other vertex out."""
    rnd = random.Random(seed)
    b = bmesh.new()
    rings = []
    for j, (r, z) in enumerate(profile):
        ring = []
        for k in range(sides):
            a = 2 * math.pi * (k + 0.5 * (j % 2)) / sides
            rr = r * (1 + (spiky if k % 2 == 0 and j == 1 else 0)) * (1 + rnd.uniform(-0.03, 0.03))
            ring.append(b.verts.new((rr * math.cos(a), rr * math.sin(a), z - (0.05 * r if k % 2 == 0 and j == 1 else 0))))
        rings.append(ring)
    for j in range(len(rings) - 1):
        for k in range(sides):
            b.faces.new((rings[j][k], rings[j][(k + 1) % sides], rings[j + 1][(k + 1) % sides], rings[j + 1][k]))
    quad_cap(b, rings[0])    # closed underneath and at the tip
    quad_cap(b, rings[-1])
    bmesh.ops.recalc_face_normals(b, faces=b.faces)
    uv_part(b, col)
    merge(bm, b)


def star(bm, c, r, col=STAR_GOLD, yaw=0.0):
    b = bmesh.new()
    ctr = b.verts.new((0, 0, 0))
    inner = [b.verts.new((0, 0.42 * r * math.cos(2 * math.pi * (i + 0.5) / 5 + math.pi / 2), 0.42 * r * math.sin(2 * math.pi * (i + 0.5) / 5 + math.pi / 2))) for i in range(5)]
    outer = [b.verts.new((0, r * math.cos(2 * math.pi * i / 5 + math.pi / 2), r * math.sin(2 * math.pi * i / 5 + math.pi / 2))) for i in range(5)]
    for i in range(5):   # one kite (quad) per point
        b.faces.new((ctr, inner[i - 1], outer[i], inner[i]))
    ext = bmesh.ops.extrude_face_region(b, geom=b.faces[:])
    bmesh.ops.translate(b, vec=Vector((r * 0.3, 0, 0)), verts=[e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)])
    bmesh.ops.translate(b, vec=Vector((-r * 0.15, 0, 0)), verts=b.verts)
    bmesh.ops.recalc_face_normals(b, faces=b.faces)
    uv_part(b, col)
    bmesh.ops.rotate(b, cent=Vector(), matrix=Matrix.Rotation(math.radians(yaw), 3, 'Z'), verts=b.verts)
    bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
    merge(bm, b)


def f_gift(bm, c, r, sd):
    """Gift box (size ~2r) with a crossed ribbon and a bow."""
    rnd = random.Random(sd)
    col = GIFT_COLS[sd % len(GIFT_COLS)]
    rib = RIBBON[(sd // len(GIFT_COLS)) % 2] if col is not GIFT_COLS[4] else RIBBON[0]
    w = r * 1.8
    h = w * rnd.uniform(0.75, 1.1)
    yaw = rnd.uniform(-25, 25)

    def box(center, size, column):
        b = bmesh.new()
        bmesh.ops.create_cube(b, size=1.0)
        bmesh.ops.scale(b, vec=Vector(size), verts=b.verts)
        bmesh.ops.translate(b, vec=Vector(center), verts=b.verts)
        uv_part(b, column)
        bmesh.ops.rotate(b, cent=Vector(), matrix=Matrix.Rotation(math.radians(yaw), 3, 'Z'), verts=b.verts)
        bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
        merge(bm, b)
    box((0, 0, h / 2), (w, w, h), col)
    box((0, 0, h / 2), (w * 0.22, w * 1.03, h * 1.03), rib)
    box((0, 0, h / 2), (w * 1.03, w * 0.22, h * 1.03), rib)
    for sgn in (-1, 1):   # bow loops
        b = bmesh.new()
        bmesh.ops.create_cube(b, size=1.0)
        bmesh.ops.scale(b, vec=Vector((w * 0.32, w * 0.12, w * 0.2)), verts=b.verts)
        bmesh.ops.rotate(b, cent=Vector(), matrix=Matrix.Rotation(math.radians(35 * sgn), 3, 'Y'), verts=b.verts)
        bmesh.ops.translate(b, vec=Vector((sgn * w * 0.15, 0, h + w * 0.08)), verts=b.verts)
        uv_part(b, rib)
        bmesh.ops.rotate(b, cent=Vector(), matrix=Matrix.Rotation(math.radians(yaw), 3, 'Z'), verts=b.verts)
        bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
        merge(bm, b)


def t_christmas(bm, s, fruit, L):
    tube(bm, [(0, 0, 0), (0, 0, 0.55 * s)], [0.14 * s, 0.11 * s], BARK, 8, 0, 0.6 * s)
    tiers = [(0.4, 1.15, 1.0), (0.98, 0.95, 0.9), (1.52, 0.74, 0.82), (2.02, 0.5, 0.78)]   # base z, radius, height
    for i, (z, r, hgt) in enumerate(tiers):
        z, r, hgt = z * s, r * s, hgt * s
        prof = [(0.12 * s, z + 0.12 * hgt), (r, z), (r * 0.72, z + 0.3 * hgt), (r * 0.4, z + 0.62 * hgt), (0.04 * s, z + hgt)]
        lathe(bm, prof, PINE, 16, 0.12, 40 + i)
    top = tiers[-1][0] * s + tiers[-1][2] * s
    if fruit:
        star(bm, (0, 0, top + 0.18), 0.26)
        star(bm, (0, 0, top + 0.18), 0.26, yaw=90)
        k = 0
        for i, (z, r, hgt) in enumerate(tiers[:3]):   # gifts resting on the tier skirts
            n = 5 - i
            for j in range(n):
                a = 2 * math.pi * j / n + i * 0.6
                rr = r * s * 0.93
                fruit(bm, (rr * math.cos(a), rr * math.sin(a), z * s - 0.08), 0.12, k)
                k += 1
        for j, (a, d) in enumerate(((0.5, 1.0), (1.6, 1.15), (3.2, 0.95), (4.6, 1.1))):   # a few under the tree
            fruit(bm, (d * math.cos(a), d * math.sin(a), 0.0), 0.14, 20 + j)


TYPES = [  # type, shape, fruit, leaf column, fruit item name
    ("Apple", t_apple, f_apple, c0(9), "SM_Apple"),
    ("Orange", t_orange, f_orange, c0(13), "SM_Orange"),
    ("Lemon", t_lemon, f_lemon, c0(5), "SM_Lemon"),
    ("Cherry", t_cherry, f_cherry, c0(19), "SM_Cherry"),
    ("Pear", t_pear, f_pear, c0(22), "SM_Pear"),
    ("Coconut", t_coconut, f_coconut, c0(24), "SM_Coconut"),
    ("Plum", t_plum, f_plum, c0(22, 0.86, 0.99), "SM_Plum"),
    ("Peach", t_peach, f_peach, c0(9, 0.87, 0.995), "SM_Peach"),
    ("Halloween", t_halloween, f_jack, c0(30, 0.85, 0.95), "SM_JackOLantern"),
    ("Christmas", t_christmas, f_gift, c0(13), "SM_Gift"),
]
STAGES = ((0.33, 3.3), (0.63, 6.0), (1.0, 10.0))  # Stage2..4: scale, x position


def finish(bm, name, coll, loc, mat):
    o = bpy.data.objects.get(name)
    if o:
        bpy.data.objects.remove(o, do_unlink=True)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    o.location = loc
    return o


def check_closed(objs):
    """Per object: open (boundary) edges, inside-out parts (closed islands whose signed volume is
    negative) and the face sizes used. A clean model has 0 open edges and 0 inside-out parts."""
    out = {}
    for o in objs:
        b = bmesh.new()
        b.from_mesh(o.data)
        open_edges = sum(1 for e in b.edges if len(e.link_faces) < 2)
        b.faces.ensure_lookup_table()
        seen, inside_out, islands = set(), 0, 0
        for f in b.faces:
            if f.index in seen:
                continue
            islands += 1
            stack, vol = [f], 0.0
            seen.add(f.index)
            while stack:
                g = stack.pop()
                vol += g.calc_center_median().dot(g.normal) * g.calc_area() / 3.0
                for e in g.edges:
                    for h in e.link_faces:
                        if h.index not in seen:
                            seen.add(h.index)
                            stack.append(h)
            if vol < 0:
                inside_out += 1
        out[o.name] = {"open_edges": open_edges, "inside_out": inside_out, "parts": islands,
                       "faces": dict(Counter(len(f.verts) for f in b.faces))}
        b.free()
    return out


def fix_normals(objs):
    """Recalculates every part's normals to point outward."""
    for o in objs:
        b = bmesh.new()
        b.from_mesh(o.data)
        bmesh.ops.recalc_face_normals(b, faces=b.faces)
        b.to_mesh(o.data)
        b.free()


def build_trees(only=None):
    mat = bpy.data.materials["M_GradientTexture"]
    trees = bpy.data.collections.get("Trees")
    if trees is None:
        trees = bpy.data.collections.new("Trees")
        bpy.context.scene.collection.children.link(trees)
    stats = {}
    for row, (name, shape, fruit, L, item) in enumerate(TYPES):
        if only and name not in only:
            continue
        sub = bpy.data.collections.get("Tree_" + name) or bpy.data.collections.new("Tree_" + name)
        if sub.name not in [c.name for c in trees.children]:
            trees.children.link(sub)
        y = 8 + row * 4.5
        bm = bmesh.new()
        if name == "Coconut":
            tube(bm, [(0, 0, 0), (0.02, 0, 0.2)], [0.03, 0.022], PALM_BARK, 6)
            for k in range(4):
                leaf(bm, (0.02, 0, 0.19), 90 * k + 20, 0.3, 0.1, 15, L, droop=-0.4)
        else:
            tube(bm, [(0, 0, 0), (0.01, 0, 0.18), (0.02, 0, 0.36)], [0.025, 0.02, 0.016], BARK, 6)
            leaf(bm, (0.02, 0, 0.34), 20, 0.2, 0.11, 25, L)
            leaf(bm, (0.02, 0, 0.34), 200, 0.2, 0.11, 25, L)
            leaf(bm, (0.015, 0, 0.22), 110, 0.15, 0.08, 35, L)
        objs = [finish(bm, "SM_%sTree_Stage1" % name, sub, (1.5, y, 0), mat)]
        for st, (s, x) in enumerate(STAGES, start=2):
            bm = bmesh.new()
            shape(bm, s, fruit if st == 4 else None, L)
            objs.append(finish(bm, "SM_%sTree_Stage%d" % (name, st), sub, (x, y, 0), mat))
        bm = bmesh.new()
        fruit(bm, (0, 0, 0.16), 0.16, 999)
        zs = [v.co.z for v in bm.verts]
        bmesh.ops.translate(bm, vec=Vector((0, 0, -min(zs))), verts=bm.verts)
        objs.append(finish(bm, item, sub, (13.5, y, 0), mat))
        for o in objs:
            stats[o.name] = [dict(Counter(len(p.vertices) for p in o.data.polygons)), round(o.dimensions.z, 2)]
    return stats
