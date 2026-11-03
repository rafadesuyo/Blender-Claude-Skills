# Premium candy crops for gab (2026-11-02): 9 crops x (Seed + Stage1..6 + harvested item), built
# like dragon_fruit.py: ONE material (M_GradientTexture = gradient atlas v3), smooth shading,
# 100% quads, closed parts, 0 z-fight. Each crop has its own plant shape:
#   ChocolateBar   cacao bush, wrapped bars grow straight off the trunk (cauliflory)
#   WhiteChocolate vanilla vine on a stake, cream orchids, white bars hang like vanilla pods
#   Truffle        cocoa-cup bush: paper cups bloom on brown stems and fill with truffles
#   Lollipop       white stick stems, swirl-rope lollipops (pink, blue, rainbow)
#   CandyCane      fern of fiddleheads that uncurl into striped canes, peppermints hang off hooks
#   LavaPlant      obsidian stalks with glowing seams + flame leaves on a lava-pool rock, magma fruit
#   CottonCandy    striped paper-cone stems topped with pink / blue floss puffs
#   PinkCloud      curly lavender stalks holding pink clouds (with a face) and pink raindrops
#   RainbowTruffle rainbow-petal flowers holding sprinkled rainbow truffles
#   exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/premium_crops.py")).read())
#   build_premium(only=None)   -> {object name: topo summary}
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

_GP = __import__("os").path.expanduser(r"~/.claude/skills/blender-game-props")
exec(open(_GP + r"\dragon_fruit.py").read())
exec(open(_GP + r"\zfight_check.py").read())

PI = math.pi
TAU = 2 * math.pi


def C(row, col, t=0.1):
    """Near-constant colour from one spot of a strip (stripes, small parts)."""
    return strip(row, col, t, t + 0.05)


# ---------- palette (atlas v3 columns, t0 -> t1)
CHOC = strip("r1", 35, 0.0, 0.5)        # milk chocolate
CHOC_D = strip("r3", 29, 0.0, 0.7)      # dark chocolate
TRUNK = strip("r1", 35, 0.0, 0.75)      # cocoa trunk (dark base with flip)
BRONZE = strip("r3", 22, 0.0, 0.5)      # young cacao leaves
WCHOC = strip("r3", 6, 0.0, 0.3)        # white chocolate
GOLD = strip("r4", 0, 0.0, 0.7)
SILVER = strip("r4", 9, 0.0, 0.5)
RED_W = strip("r4", 3, 0.1, 0.9)        # red wrapper
BLUE_W = strip("r4", 13, 0.1, 0.8)      # blue wrapper
WHITE = C("r4", 4, 0.0)
WHITE_G = strip("r4", 4, 0.0, 0.3)
RED = C("r1", 14, 0.05)
MINT = strip("r4", 7, 0.0, 0.45)
MINT_C = C("r4", 7, 0.15)
PINK = strip("r4", 11, 0.0, 0.7)
PINK_C = C("r4", 11, 0.35)
CC_PINK = strip("r4", 11, 0.0, 0.4)
CC_BLUE = strip("r4", 25, 0.0, 0.35)
BLUE_C = C("r4", 25, 0.3)
CPINK = strip("r3", 27, 0.0, 0.7)       # cloud pink
HPINK = strip("r3", 30, 0.0, 0.6)       # hot pink
LAV = strip("r4", 5, 0.0, 0.6)          # lavender stalks
LEAF = strip("r3", 4, 0.0, 0.7)
LEAF2 = strip("r3", 13, 0.0, 0.8)
DLEAF = strip("r3", 0, 0.1, 0.9)
CREAM = strip("r4", 8, 0.0, 0.3)
YEL = strip("r4", 22, 0.0, 0.7)
YEL_C = C("r4", 22, 0.2)
ORG = strip("r4", 27, 0.0, 0.8)
ORG_C = C("r4", 27, 0.3)
GRN = strip("r4", 7, 0.2, 0.9)
GRN_C = C("r4", 7, 0.5)
BLU = strip("r4", 25, 0.1, 0.9)
PURP = strip("r4", 21, 0.0, 0.8)
PURP_C = C("r4", 21, 0.4)
REDP = strip("r4", 3, 0.0, 0.8)
RAINBOW = strip("r4", 23, 0.02, 0.98)   # purple -> blue -> green -> orange -> red
LAVA = strip("r3", 33, 0.0, 1.0)        # orange -> dark red
HOT = strip("r3", 32, 0.0, 1.0)         # yellow -> orange
EMBER_B = strip("r3", 33, 1.0, 0.0)     # flame base: dark red -> orange
EMBER_T = strip("r3", 32, 1.0, 0.0)     # flame tip: orange -> yellow
ROCK = strip("r2", 6, 0.7, 1.0)         # dark grey rock
BASALT = strip("r3", 3, 0.0, 0.8)       # red-black obsidian
PAPER = strip("r2", 2, 0.45, 0.85)      # brown paper cups
BLACK = SEED


# ---------- generic pieces

def to_part(q):
    b = new_part()
    me = bpy.data.meshes.new("_tmp")
    q.to_mesh(me)
    q.free()
    b.from_mesh(me)
    bpy.data.meshes.remove(me)
    return b


def put(bm, part, m=None):
    """Drops a finished multi-piece part (already oriented) into bm."""
    if m is not None:
        bmesh.ops.transform(part, matrix=m, verts=part.verts)
    me = bpy.data.meshes.new("_tmp")
    part.to_mesh(me)
    part.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)


def uv_pick(b, pick):
    """Per-face strip choice: pick(face index, face) -> strip; t comes from the vert layer."""
    tl = b.verts.layers.float["t"]
    ul = b.loops.layers.uv["UVMap"]
    b.faces.index_update()
    for f in b.faces:
        u, va, vb = pick(f.index, f)
        for l in f.loops:
            t = min(max(l.vert[tl], 0.0), 1.0)
            l[ul].uv = (u, va + (vb - va) * t)


def stripes(b, n, sides, colour_of, cap_s):
    """Tube faces are made ring by ring: face i -> ring i // sides, side i % sides; caps after."""
    lim = (n - 1) * sides
    uv_pick(b, lambda fi, f: colour_of(fi // sides, fi % sides) if fi < lim else cap_s)


def rot_to(axis):
    return Z.rotation_difference(Vector(axis).normalized()).to_matrix().to_4x4()


def tube2(pts, radii, sides=8, twist=0.0, flat=1.0, ref=None, caps=("strip", "strip"), dome=0.6, section=None):
    """tube() with a twist: ring i's verts turn by twist * i face widths, so quads follow a helix
    (candy stripes coloured per side index become smooth spirals instead of stair steps)."""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    tang = [(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(n)]
    r0 = Vector(ref) if ref is not None else (Z if abs(tang[0].z) < 0.9 else Vector((1, 0, 0)))
    ax = (r0 - tang[0] * r0.dot(tang[0])).normalized()
    ay = tang[0].cross(ax)
    b = new_part()
    tl = b.verts.layers.float["t"]
    rings = []
    for i, p in enumerate(pts):
        if i:
            q = tang[i - 1].rotation_difference(tang[i])
            ax, ay = q @ ax, q @ ay
        ring = []
        for k in range(sides):
            a = TAU * (k + twist * i) / sides
            m = section(i, k) if section else 1.0
            v = b.verts.new(p + ax * (math.cos(a) * radii[i] * m) + ay * (math.sin(a) * radii[i] * flat * m))
            v[tl] = i / (n - 1)
            ring.append(v)
        rings.append(ring)
    for s in range(n - 1):
        for k in range(sides):
            j = (k + 1) % sides
            b.faces.new((rings[s][k], rings[s][j], rings[s + 1][j], rings[s + 1][k]))
    for end, ring, d in ((0, rings[0], -tang[0]), (1, rings[-1], tang[-1])):
        kind = caps[end]
        if not kind:
            continue
        if kind == "strip" or sides % 4:
            strip_cap(b, ring)
            continue
        new = grid_cap(b, ring)
        inner = {v for f in new for v in f.verts} - set(ring)
        c = sum((v.co for v in ring), Vector()) / len(ring)
        R = sum((v.co - c).length for v in ring) / len(ring)
        for v in inner:
            v[tl] = float(end)
            if kind == "dome":
                t = min((v.co - c).length / R, 1.0)
                v.co += d * (dome * R * (1 - t * t))
    bmesh.ops.recalc_face_normals(b, faces=b.faces)
    return b, rings, tang


def arc(base, yaw, L, e0, e1, n=6, pw=1.0, wob=0.0, wf=2.0, seed=0):
    """Path from base: heading yaw, elevation bending e0 -> e1 (deg); wob adds a sideways wiggle."""
    rnd = random.Random(seed)
    ph = rnd.uniform(0, TAU)
    side = Vector((-math.sin(yaw), math.cos(yaw), 0))
    pts, p = [], Vector(base)
    for i in range(n):
        f = i / (n - 1)
        pts.append(p + side * (wob * math.sin(ph + wf * PI * f) * f))
        e = math.radians(e0 + (e1 - e0) * f ** pw)
        p = p + Vector((math.cos(e) * math.cos(yaw), math.cos(e) * math.sin(yaw), math.sin(e))) * (L / (n - 1))
    return pts


def ball(bm, c, r, s, scale=(1, 1, 1), cuts=2, jitter=0.0, seed=0, flip=False, m=None, tfn=None):
    q = quad_sphere(r, cuts, scale, jitter, seed)
    b = to_part(q)
    h = r * scale[2]
    retag(b, tfn or (lambda v: 0.5 - v.co.z / (2 * h)))
    uv(b, s, flip)
    merge(bm, b, Matrix.Translation(c) @ (m if m is not None else Matrix()))


def stalk(bm, pts, r0, r1, s, sides=8, caps=("grid", "dome"), flip=True, twist=0.0, colour_of=None, cap_s=None, ref=None):
    pts = [Vector(p) for p in pts]
    n = len(pts)
    radii = [r0 + (r1 - r0) * i / (n - 1) for i in range(n)]
    b, rings, tang = tube2(pts, radii, sides, twist, caps=caps, ref=ref)
    if colour_of:
        stripes(b, n, sides, colour_of, cap_s or s)
    else:
        uv(b, s, flip)
    merge(bm, b)
    return pts


def leaves(bm, c, n, L, W, e0, e1, s, rnd, yaw0=0.0, flat=0.25, r0=0.012, lj=0.1):
    c = Vector(c)
    for j in range(n):
        yaw = yaw0 + TAU * j / n + rnd.uniform(-0.18, 0.18)
        leaf(bm, (c.x + math.cos(yaw) * r0, c.y + math.sin(yaw) * r0, c.z + rnd.uniform(-0.01, 0.01)), yaw,
             L * rnd.uniform(1 - lj, 1 + lj), W, e0 + rnd.uniform(-8, 8), e1, s, flat)


def soil(bm, R, h):
    return mound(bm, R, h)


def seeds_on(bm, top, makers, rad=0.05, z=-0.004):
    for i, mk in enumerate(makers):
        a = TAU * i / len(makers) + 0.4
        mk(bm, Vector((math.cos(a) * rad, math.sin(a) * rad, top + z)), a)


def sprout(bm, top, stem_s, leaf_s, h=0.08, L=0.078, W=0.034, n=2, e=(35, 5), r=0.009):
    b, _, _ = tube([(0, 0, top - 0.02), (0, 0.003, top + h * 0.5), (0, 0, top + h)], [r, r * 0.9, r * 0.8], 8)
    uv(b, stem_s, flip=True)
    merge(bm, b)
    for j in range(n):
        yaw = 0.15 + TAU * j / n
        leaf(bm, (math.cos(yaw) * 0.006, math.sin(yaw) * 0.006, top + h - 0.005), yaw, L, W, e[0], e[1], leaf_s)
    return top + h


def bloom(bm, c, axis, size, petals, centre, n=5, e0=50, e1=10, L=0.5, W=0.22, seed=0, cr=0.13, flip=False, cz=0.04):
    """Flower / cup of n petals around axis (petal colours cycle through the petals list)."""
    rnd = random.Random(seed)
    fb = new_part()
    for j in range(n):
        yaw = TAU * j / n + rnd.uniform(-0.08, 0.08)
        de = 5 * (j % 3)  # neighbouring petals at different tilts: no shared planes (z-fight)
        pts = arc(Vector((math.cos(yaw), math.sin(yaw), 0)) * (0.05 + 0.01 * (j % 3)) * size, yaw, L * size, e0 + de, e1 + de, 5)
        radii = [W * size * f for f in (0.35, 0.85, 1.0, 0.8, 0.25)]
        b, _, _ = tube(pts, radii, 8, flat=0.2, ref=Vector((-math.sin(yaw), math.cos(yaw), 0)))
        uv(b, petals[j % len(petals)], flip)
        merge(fb, b)
    if centre:
        merge(fb, sphere_part(size * cr, 2, (1, 1, 0.7), centre, lambda v: 0.3), Matrix.Translation((0, 0, cz * size)))
    put(bm, fb, Matrix.Translation(c) @ rot_to(axis))


def mini_box(bm, pos, size, s, normal, spin=0.0, bevel=0.0):
    b = box_part(size, (0, 0, 0), s, axis=0, bevel=bevel)
    merge(bm, b, Matrix.Translation(pos) @ rot_to(normal) @ Matrix.Rotation(spin, 4, 'Z'))


# ---------- candy parts (built around the origin, front = -Y)

def choc_bar(w, h, d, body, wrap, foil, label, cols=2, rows=4, wf=0.42):
    """Standing bar centred on the origin: chocolate slab + pillow squares on the front, the
    bottom wf of it in a wrapper (10 mm proud) with a torn foil band (5 mm proud) and a label."""
    fb = new_part()
    merge(fb, box_part((w, d * 0.6, h), (0, d * 0.2, 0), body, bevel=min(w, d) * 0.08))
    g = w * 0.07
    sw, sh = (w - g * (cols + 1)) / cols, (h - g * (rows + 1)) / rows
    zt = -h / 2 + h * wf
    # The foil band ends in the middle of a gap between square rows, so no square face is level
    # with its top (z-fight); squares below it are hidden and skipped.
    ft = min((-h / 2 + g / 2 + j * (sh + g) for j in range(rows + 1) if -h / 2 + g / 2 + j * (sh + g) > zt + 0.008),
             default=zt + 0.01)
    for i in range(cols):
        for j in range(rows):
            cx, cz = -w / 2 + g + sw / 2 + i * (sw + g), -h / 2 + g + sh / 2 + j * (sh + g)
            if cz < ft:
                continue
            merge(fb, box_part((sw, d * 0.5, sh), (cx, -d * 0.25, cz), body, bevel=min(sw, sh, d * 0.5) * 0.3))
    e, f = 0.010, 0.005
    wh = h * wf + e
    merge(fb, box_part((w + 2 * e, d + 2 * e, wh), (0, 0, -h / 2 - e + wh / 2), wrap, bevel=e * 0.6))
    fh = ft - zt + 0.004
    merge(fb, box_part((w + 2 * f, d + 2 * f, fh), (0, 0, ft - fh / 2), foil, bevel=f * 0.6))
    merge(fb, box_part((w * 0.72, 0.008, h * wf * 0.32), (0, -(d / 2 + e) - 0.002, -h / 2 + h * wf * 0.5), label, axis=2, bevel=0.002))
    return fb


def hang_bar(bm, attach, yaw, w, h, d, stem_s, drop=0.03, tilt=0.0, **kw):
    bar = choc_bar(w, h, d, **kw)
    a = Vector(attach)
    put(bm, bar, Matrix.Translation(a - Vector((0, 0, drop + h / 2))) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(tilt, 4, 'X'))
    b, _, _ = tube([a + Vector((0, 0, 0.01)), a - Vector((0, 0, drop * 0.5)), a - Vector((0, 0, drop + 0.015))], [0.008, 0.007, 0.007], 8)
    uv(b, stem_s)
    merge(bm, b)


def cup(R, H, s, pleats=16):
    b, _, _ = tube([(0, 0, 0), (0, 0, H * 0.5), (0, 0, H)], [R * 0.72, R * 0.86, R], pleats,
                   section=lambda i, k: 1.0 if k % 2 == 0 else 0.9, caps=("grid", "grid"))
    retag(b, lambda v: 0.2 + 0.6 * (1 - v.co.z / H))
    uv(b, s)
    return b


def truffle(r, body, drizzle=None, sprinkles=0, seed=0, sz=0.9):
    """Truffle ball around the origin; drizzle = 3 wavy lines over the top, sprinkles = tiny bars."""
    rnd = random.Random(seed)
    fb = new_part()
    h = r * sz
    merge(fb, sphere_part(r, 3, (1, 1, sz), body, lambda v: 0.5 - v.co.z / (2 * h), flip=(body == RAINBOW)))
    if drizzle:
        for k in range(3):
            y0 = (k - 1) * 0.42 * r
            pts = []
            for i in range(9):
                x = -0.8 * r + 1.6 * r * i / 8
                y = y0 + 0.1 * r * math.sin(i * 1.6 + k)
                zz = max(r * r - x * x - y * y, 0.0)
                pts.append(Vector((x, y, math.sqrt(zz) * sz * 0.99)))
            b, _, _ = tube(pts, [0.07 * r] * 9, 6)
            uv(b, drizzle)
            merge(fb, b)
    cols = (YEL_C, PINK_C, BLUE_C, GRN_C, WHITE, ORG_C, PURP_C)
    ga = PI * (3 - math.sqrt(5))
    for i in range(sprinkles):  # golden-angle spread over the top so sprinkles never overlap
        zf = 0.95 - 1.1 * (i + 0.5) / max(sprinkles, 1)
        a = ga * i + rnd.uniform(-0.15, 0.15)
        n = Vector((math.cos(a) * math.sqrt(1 - zf * zf), math.sin(a) * math.sqrt(1 - zf * zf), zf))
        p = Vector((n.x * r, n.y * r, n.z * h)) * 1.0
        mini_box(fb, p, (0.2 * r, 0.06 * r, 0.06 * r), cols[i % len(cols)], n, rnd.uniform(0, PI), bevel=0.012 * r)
    return fb


def swirl_pop(R, tr, colour_of, cap_s, sides=8, twist=0.6):
    """Swirl lollipop in the XZ plane (facing -Y): a candy rope coiled outward from a centre
    bead. colour_of(t along rope, side) -> strip."""
    fb = new_part()
    rho0, pitch = tr * 1.15, 2 * tr * 0.9
    a = pitch / TAU
    pts, th = [], rho0 / a
    while a * th <= R - tr:
        rho = a * th
        pts.append(Vector((rho * math.cos(th), 0, rho * math.sin(th))))
        th += 0.95 * tr / rho
    n = len(pts)
    radii = [tr] * (n - 2) + [tr * 0.85, tr * 0.6]
    b, _, _ = tube2(pts, radii, sides, twist, ref=Vector((0, 1, 0)), caps=("grid", "dome"), dome=0.5)
    stripes(b, n, sides, lambda s, k: colour_of(s / (n - 1), k), cap_s)
    merge(fb, b)
    merge(fb, sphere_part(tr * 1.3, 2, (1, 0.85, 1), cap_s, lambda v: 0.3))
    return fb


def lolly(bm, base, H, R, colour_of, cap_s, lean=(0.0, 0.0), yaw=0.0):
    tr = max(0.012, R * 0.14)
    top = Vector(base) + Vector((lean[0], lean[1], H))
    stalk(bm, [Vector(base) + (top - Vector(base)) * f for f in (0, 0.33, 0.66, 1.0)], 0.011, 0.009, WHITE_G,
          caps=("grid", "grid"))
    put(bm, swirl_pop(R, tr, colour_of, cap_s), Matrix.Translation(top) @ Matrix.Rotation(yaw, 4, 'Z'))


def pop_pink(t, k):
    return WHITE if (k // 2) % 2 else PINK_C


def pop_blue(t, k):
    return WHITE if (k // 2) % 2 else BLUE_C


def pop_rainbow(t, k):
    return WHITE if k in (3, 7) else RAINBOW


def pop_sun(t, k):
    return ORG_C if (k // 2) % 2 else YEL_C


def cane_pts(H, R, r, hook=200, shrink=0.0, step=1.2):
    st = r * step
    hz = H - R
    n = max(2, int(hz / st) + 1)
    pts = [Vector((0, 0, hz * i / (n - 1))) for i in range(n)]
    c = Vector((R, 0, hz))
    total = math.radians(hook)
    phi = 0.0
    while True:
        Rp = R * (1 - shrink * phi / total)
        phi += st / max(Rp, r)
        if phi > total:
            break
        Rp = R * (1 - shrink * phi / total)
        pts.append(c + Vector((-math.cos(phi) * Rp, 0, math.sin(phi) * Rp)))
    return pts


def cane_classic(s, k):
    return RED if k in (0, 1, 4, 5) else WHITE


def cane_mint(s, k):
    return RED if k in (0, 1) else (MINT_C if k == 4 else WHITE)


def cane(bm, base, H, R, r, yaw=0.0, hook=200, shrink=0.0, scheme=cane_classic, tilt=0.0, tip=0.6):
    pts = cane_pts(H, R, r, hook, shrink)
    n = len(pts)
    radii = [r] * (n - 2) + [r * 0.85, r * tip] if n > 3 else [r] * n
    if shrink:
        radii = [r * (1 - 0.55 * max(0.0, (i - n * 0.4) / (n * 0.6))) for i in range(n)]
    b, _, _ = tube2(pts, radii, 8, twist=1.5, ref=Vector((0, 1, 0)), caps=("grid", "dome"), dome=0.5)
    stripes(b, n, 8, scheme, WHITE)
    merge(bm, b, Matrix.Translation(base) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(tilt, 4, 'Y'))
    tipw = Matrix.Translation(base) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(tilt, 4, 'Y') @ pts[-1]
    return tipw


def peppermint(R, d, a=RED, b_=WHITE):
    b, _, _ = tube([(0, -d / 2, 0), (0, -d * 0.3, 0), (0, d * 0.3, 0), (0, d / 2, 0)], [R * 0.82, R, R, R * 0.82], 16,
                   ref=Vector((1, 0, 0)), caps=("grid", "grid"))
    lim = 3 * 16

    def pick(fi, f):
        c = f.calc_center_median()
        sec = int((math.atan2(c.z, c.x) / TAU) * 8 + 8) % 2
        if fi < lim:
            return a if ((fi % 16) // 2) % 2 else b_
        return a if sec else b_
    uv_pick(b, pick)
    return b


def magma(r, seed=0, plates=26):
    rnd = random.Random(seed)
    fb = new_part()
    merge(fb, sphere_part(r, 3, (1, 1, 1), HOT, lambda v: 0.55 + 0.45 * (0.5 - v.co.z / (2 * r))))
    ga = PI * (3 - math.sqrt(5))
    for i in range(plates):
        zf = 1 - 2 * (i + 0.5) / plates
        rr = math.sqrt(1 - zf * zf)
        n = Vector((math.cos(ga * i) * rr, math.sin(ga * i) * rr, zf))
        sz = r * rnd.uniform(0.37, 0.42) * math.sqrt(26 / plates)
        q = quad_sphere(1.0, 1, (sz, sz, sz * 0.32), 0.06, rnd.randint(0, 99))
        b = to_part(q)
        retag(b, lambda v: 0.3 + v.co.z / sz)
        uv(b, BASALT)
        merge(fb, b, Matrix.Translation(n * r * 0.97) @ rot_to(n) @ Matrix.Rotation(rnd.uniform(0, PI), 4, 'Z'))
    return fb


def fluff(bm, c, R, cols, seed=0, n=7, cuts=2):
    rnd = random.Random(seed)
    c = Vector(c)
    ball(bm, c, R * 0.66, cols[0], cuts=cuts, jitter=0.06, seed=seed)
    for i in range(n):
        a = TAU * i / n + rnd.uniform(-0.3, 0.3)
        zf = rnd.uniform(-0.45, 0.75)
        d = Vector((math.cos(a) * math.sqrt(1 - zf * zf), math.sin(a) * math.sqrt(1 - zf * zf), zf))
        ball(bm, c + d * R * 0.48, R * rnd.uniform(0.4, 0.52), cols[(i + 1) % len(cols)], cuts=cuts, jitter=0.08,
             seed=seed * 31 + i)


PUFFS = [(0, 0, 0.2, 0.55), (-0.45, 0.02, 0.02, 0.38), (0.45, 0.02, 0.0, 0.37), (-0.22, 0.12, 0.38, 0.34),
         (0.26, 0.12, 0.34, 0.33), (-0.78, 0.04, -0.06, 0.25), (0.78, 0.04, -0.08, 0.24), (0.0, 0.2, 0.02, 0.42)]


def cloud(R, s, seed=0, face=False, ys=0.8):
    rnd = random.Random(seed)
    fb = new_part()
    for i, (x, y, z, r) in enumerate(PUFFS):
        rr = r * R * rnd.uniform(0.95, 1.05)
        q = quad_sphere(rr, 3 if r > 0.3 else 2, (1, ys, 0.92), 0.03, seed + i)
        b = to_part(q)
        top = (z + r) * R
        retag(b, lambda v, zc=z * R: min(max((0.55 * R - (v.co.z + zc)) / (1.0 * R), 0.0), 1.0))
        uv(b, s)
        merge(fb, b, Matrix.Translation((x * R, y * R, z * R)))
    if face:
        r0, zc = 0.55 * R, 0.2 * R

        def front(dx, dz, out=0.0):
            yy = ys * math.sqrt(max(r0 * r0 - dx * dx - (dz / 0.92) ** 2, 0.0))
            return Vector((dx, -yy - out, zc + dz))
        for sx in (-1, 1):
            merge(fb, sphere_part(1.0, 1, (0.05 * R, 0.03 * R, 0.07 * R), BLACK, lambda v: 0.5),
                  Matrix.Translation(front(sx * 0.17 * R, 0.0, -0.012 * R)))
            merge(fb, sphere_part(1.0, 1, (0.065 * R, 0.022 * R, 0.035 * R), HPINK, lambda v: 0.2),
                  Matrix.Translation(front(sx * 0.31 * R, -0.1 * R, -0.01 * R)))
        pts = [front(0.07 * R * math.cos(a), -0.08 * R - 0.05 * R * math.sin(a), 0.004 * R)
               for a in [PI * (0.15 + 0.7 * i / 5) for i in range(6)]]
        b, _, _ = tube(pts, [0.014 * R] * 6, 6)
        uv(b, BLACK)
        merge(fb, b)
    return fb


def drop(r, s):
    b, _, _ = tube([(0, 0, 2.0 * r), (0, 0, 1.3 * r), (0, 0, 0.5 * r), (0, 0, -0.2 * r), (0, 0, -0.7 * r)],
                   [0.12 * r, 0.5 * r, 0.9 * r, 0.98 * r, 0.65 * r], 8, caps=("grid", "dome"), dome=0.6)
    uv(b, s)
    return b


def flame_leaf(bm, base, yaw, L, W, e0=62, e1=88, seed=0):
    pts = arc(base, yaw, L, e0, e1, 6, wob=0.12 * L, seed=seed)
    radii = [W * f for f in (0.35, 0.9, 1.0, 0.75, 0.42, 0.1)]
    b, _, _ = tube(pts, radii, 8, flat=0.28, ref=Vector((-math.sin(yaw), math.cos(yaw), 0)))
    uv_split(b, EMBER_B, EMBER_T, 0.45)
    merge(bm, b)


def obsidian(bm, pts, r0, r1, twist=0.35):
    return stalk(bm, pts, r0, r1, BASALT, 8, twist=twist,
                 colour_of=lambda s, k: LAVA if k in (0, 4) else BASALT, cap_s=BASALT)


def lava_rock(bm, R, h, seed=0):
    """Rock mound with glowing cracks down its sides and a lava pool on top."""
    prof = [(R, 0.0), (R * 0.98, h * 0.3), (R * 0.85, h * 0.62), (R * 0.6, h * 0.88), (R * 0.32, h)]
    n = len(prof)
    b, rings, _ = tube([(0, 0, z) for _, z in prof], [r for r, _ in prof], sides=16, caps=("grid", "dome"), dome=0.12)
    retag(b, lambda v: 1 - min(Vector((v.co.x, v.co.y)).length / R, 1.0))
    side, cap = (n - 1) * 16, 32
    cracks = {(2, 1), (3, 2), (7, 2), (12, 1), (13, 2)}

    def pick(fi, f):
        if fi < side:
            s, k = fi // 16, fi % 16
            return LAVA if (k, s) in cracks else ROCK
        if fi < side + cap:
            return ROCK
        return HOT if fi < side + cap + 16 else LAVA
    uv_pick(b, pick)
    merge(bm, b)
    return h + 0.12 * R * 0.32


def rock(bm, c, r, seed):
    ball(bm, c, r, ROCK, (1, 0.9, 0.7), cuts=1, jitter=0.18, seed=seed)


# ---------- seed makers  (bm, pos, angle)

def mk_bean(s):
    return lambda bm, p, a: ball(bm, p, 1.0, s, (0.024, 0.015, 0.012), cuts=1, m=Matrix.Rotation(a + 0.5, 4, 'Z'))


def mk_chip(s):
    def f(bm, p, a):
        b, _, _ = tube([p + Vector((0, 0, -0.004)), p + Vector((0, 0, 0.006)), p + Vector((0, 0, 0.015)),
                        p + Vector((0, 0, 0.023))], [0.014, 0.013, 0.007, 0.002], 8, caps=("grid", "grid"))
        uv(b, s)
        merge(bm, b)
    return f


def mk_ball(s, r=0.014):
    return lambda bm, p, a: ball(bm, p + Vector((0, 0, r * 0.4)), r, s, cuts=1)


def mk_cube(s):
    return lambda bm, p, a: mini_box(bm, p + Vector((0, 0, 0.006)), (0.018, 0.018, 0.018), s, Z, a, bevel=0.003)


def mk_sprinkle(s):
    return lambda bm, p, a: mini_box(bm, p + Vector((0, 0, 0.004)), (0.03, 0.009, 0.009), s, Z, a, bevel=0.003)


def mk_bead(bm, p, a):
    d = Vector((math.cos(a + 1.2), math.sin(a + 1.2), 0)) * 0.014
    b, _, _ = tube2([p - d, p - d * 0.33, p + d * 0.33, p + d], [0.008, 0.011, 0.011, 0.008], 8, twist=1.5,
                    caps=("grid", "grid"))
    stripes(b, 4, 8, cane_classic, WHITE)
    merge(bm, b, Matrix.Translation((0, 0, 0.008)))


def mk_puff(s):
    def f(bm, p, a):
        for j, (dx, r) in enumerate(((-0.008, 0.009), (0.008, 0.009), (0.0, 0.011))):
            ball(bm, p + Vector((dx * math.cos(a), dx * math.sin(a), 0.006 + 0.004 * (j == 2))), r, s, cuts=1, seed=j)
    return f


# ======================================================================== ChocolateBar
BAR_DARK = dict(body=CHOC, wrap=RED_W, foil=GOLD, label=GOLD)
BAR_WHITE = dict(body=WCHOC, wrap=BLUE_W, foil=SILVER, label=WHITE)


def cacao_tree(bm, H, r0, branches, crown, rnd, seed=0):
    pts = stalk(bm, [(0.025 * math.sin(PI * i / 7), 0.01 * math.sin(PI * i / 7), 0.03 + (H - 0.03) * i / 7)
                     for i in range(8)], r0, r0 * 0.45, TRUNK)
    tips = []
    for (z, yaw, L, e0, e1, n) in branches:
        bp = arc((0.025 * math.sin(PI * z / H), 0.01 * math.sin(PI * z / H), z), yaw, L, e0, e1, 5)
        stalk(bm, bp, r0 * 0.55, r0 * 0.3, TRUNK)
        tips.append((bp, yaw))
        leaves(bm, bp[-1], n, 0.24 * H ** 0.4, 0.08 * H ** 0.4, 40, -30, LEAF, rnd, yaw0=yaw, r0=0.016)
        leaf(bm, bp[2], yaw + 1.4, 0.18 * H ** 0.4, 0.07 * H ** 0.4, 20, -35, LEAF)
    leaves(bm, pts[-1], crown, 0.26 * H ** 0.4, 0.085 * H ** 0.4, 50, -25, LEAF, rnd, r0=0.016)
    for j in range(2):  # bronze young leaves on top, like a real cacao
        a = 0.8 + j * 3.1
        leaf(bm, pts[-1] + Vector((math.cos(a), math.sin(a), 0.4)) * 0.012, a, 0.12 * H ** 0.4, 0.04 * H ** 0.4, 70, 40, BRONZE)
    return pts, tips


def bar_under(bm, tip, size, drop=0.03, kw=BAR_DARK, stem=TRUNK, rows=4):
    """Bar hanging under a branch, a third of the way in from its tip, facing the front (-Y)-ish."""
    bp, yaw = tip
    p = bp[2] + (bp[3] - bp[2]) * 0.5
    w, h = size
    hang_bar(bm, p - Vector((0, 0, 0.01)), 0.35 * math.cos(yaw), w, h, w * 0.22, stem, drop=drop, rows=rows, **kw)


def choc_seed(bm):
    top = soil(bm, 0.2, 0.055)
    seeds_on(bm, top, [mk_bean(CHOC), mk_chip(CHOC_D), mk_bean(CHOC), mk_chip(CHOC_D)])


def choc_s1(bm):
    sprout(bm, soil(bm, 0.2, 0.055), TRUNK, LEAF)


def choc_s2(bm):
    top = soil(bm, 0.21, 0.06)
    pts = stalk(bm, [(0, 0, top - 0.02), (0.005, 0, top + 0.08), (0, 0, top + 0.17)], 0.012, 0.008, TRUNK)
    rnd = random.Random(2)
    leaves(bm, pts[1], 2, 0.1, 0.035, 20, -20, LEAF, rnd, yaw0=1.2)
    leaves(bm, pts[-1], 3, 0.12, 0.04, 35, -15, LEAF, rnd)


def choc_s3(bm):
    top = soil(bm, 0.24, 0.065)
    cacao_tree(bm, 0.42, 0.02, [(0.25, -0.6, 0.1, 30, 10, 2)], 5, random.Random(3))


def choc_s4(bm):
    top = soil(bm, 0.3, 0.07)
    cacao_tree(bm, 0.75, 0.03, [(0.5, -0.9, 0.2, 35, 5, 3), (0.58, 2.2, 0.2, 35, 5, 3)], 5, random.Random(4))


def choc_s5(bm):
    top = soil(bm, 0.33, 0.075)
    rnd = random.Random(5)
    pts, tips = cacao_tree(bm, 1.0, 0.036, [(0.62, -0.8, 0.26, 35, 0, 4), (0.7, 2.3, 0.24, 35, 0, 4),
                                            (0.78, 0.9, 0.2, 40, 10, 3)], 6, rnd)
    for z, a in ((0.32, -1.3), (0.45, -2.2), (0.52, -0.4), (0.38, 0.6), (0.6, 2.8)):  # tiny trunk flowers
        p = Vector((0.02 * math.sin(PI * z) + math.cos(a) * 0.03, math.sin(a) * 0.03, z))
        bloom(bm, p, (math.cos(a), math.sin(a), 0.3), 0.07, [strip("r4", 1, 0.0, 1.0)], YEL, n=5, e0=40, e1=5)
    for t in tips[:2]:  # first small bars: fully wrapped buds
        bar_under(bm, t, (0.06, 0.1), drop=0.02, rows=3)


def choc_s6(bm):
    top = soil(bm, 0.4, 0.085)
    rnd = random.Random(6)
    pts, tips = cacao_tree(bm, 1.4, 0.05, [(0.8, -1.2, 0.42, 30, -5, 5), (0.9, -2.2, 0.4, 30, -5, 5),
                                           (1.0, 0.3, 0.38, 35, 0, 5), (0.86, 2.0, 0.4, 30, -5, 4),
                                           (1.08, 3.6, 0.34, 35, 0, 4)], 7, rnd)
    for i, t in enumerate(tips):
        bar_under(bm, t, (0.13, 0.22) if i < 3 else (0.11, 0.19), drop=0.03)
    for z, a in ((0.5, -1.5),):  # one bar sprouting straight off the trunk (cacao style)
        p = Vector((0.025 * math.sin(PI * z / 1.4) + math.cos(a) * 0.045, 0.01 + math.sin(a) * 0.045, z))
        hang_bar(bm, p, a + PI / 2, 0.11, 0.19, 0.028, TRUNK, drop=0.02, **BAR_DARK)


def choc_item(bm):
    w, h = 0.16, 0.3
    put(bm, choc_bar(w, h, 0.04, cols=2, rows=4, **BAR_DARK), Matrix.Translation((0, 0, h / 2 + 0.01)))


# ======================================================================== WhiteChocolate (vanilla vine)

def vine(bm, H, turns, rr=0.06, r=0.011, z0=0.02, leaf_every=4, rnd=None, Lf=0.2):
    n = int(turns * 16) + 2
    pts = [Vector((math.cos(TAU * turns * i / (n - 1)) * rr, math.sin(TAU * turns * i / (n - 1)) * rr,
                   z0 + (H - z0) * i / (n - 1))) for i in range(n)]
    stalk(bm, pts, r, r * 0.6, LEAF2)
    spots = []
    for i in range(3, n - 1, leaf_every):
        a = TAU * turns * i / (n - 1)
        leaf(bm, pts[i] + Vector((math.cos(a), math.sin(a), 0)) * r * 0.6, a + rnd.uniform(-0.3, 0.3),
             Lf * rnd.uniform(0.85, 1.1), 0.045 * Lf / 0.2, 20 + rnd.uniform(-10, 10), -35, LEAF, 0.22)
        spots.append((pts[i], a))
    return pts, spots


def stake2(bm, H, bars=()):
    merge(bm, box_part((0.05, 0.05, H - 0.01), (0, 0, (H + 0.01) / 2), WOOD))
    for z, w, y in bars:
        merge(bm, box_part((w, 0.036, 0.036), (0, y, z), WOOD, axis=0))


def orchid(bm, p, out, size, seed=0):
    bloom(bm, p, out, size, [CREAM], YEL, n=5, e0=35, e1=-5, L=0.5, W=0.25, seed=seed)


def wc_seed(bm):
    top = soil(bm, 0.2, 0.055)
    seeds_on(bm, top, [mk_chip(WCHOC)] * 4)


def wc_s1(bm):
    top = soil(bm, 0.2, 0.055)
    b, _, _ = tube([(0, 0, top - 0.02), (0.01, 0, top + 0.04), (0.02, 0.01, top + 0.08), (0.01, 0.02, top + 0.1)],
                   [0.008, 0.007, 0.006, 0.005], 8)
    uv(b, LEAF2, flip=True)
    merge(bm, b)
    for yaw in (0.3, PI + 0.3):
        leaf(bm, (math.cos(yaw) * 0.006, math.sin(yaw) * 0.006, top + 0.04), yaw, 0.09, 0.026, 30, -5, LEAF)


def wc_s2(bm):
    top = soil(bm, 0.21, 0.06)
    vine(bm, 0.24, 1.0, rr=0.03, r=0.009, z0=top - 0.02, leaf_every=5, rnd=random.Random(2), Lf=0.12)


def wc_s3(bm):
    top = soil(bm, 0.24, 0.065)
    stake2(bm, 0.5)
    vine(bm, 0.45, 1.3, rr=0.05, r=0.01, z0=top - 0.02, leaf_every=5, rnd=random.Random(3), Lf=0.16)


def wc_s4(bm):
    top = soil(bm, 0.3, 0.07)
    stake2(bm, 0.9, bars=((0.7, 0.34, 0.0),))
    vine(bm, 0.86, 2.0, z0=top - 0.02, rnd=random.Random(4), Lf=0.2)


def wc_s5(bm):
    top = soil(bm, 0.33, 0.075)
    stake2(bm, 1.1, bars=((0.85, 0.4, 0.0),))
    pts, spots = vine(bm, 1.06, 2.5, z0=top - 0.02, rnd=random.Random(5), Lf=0.22)
    for j, (p, a) in enumerate(spots[2::3]):
        o = Vector((math.cos(a + 0.6), math.sin(a + 0.6), 0.25))
        orchid(bm, p + o * 0.04, o, 0.13, seed=j)


def wc_s6(bm):
    top = soil(bm, 0.4, 0.085)
    stake2(bm, 1.45, bars=((1.05, 0.48, 0.0),))
    pts, spots = vine(bm, 1.4, 3.0, rr=0.065, z0=top - 0.02, rnd=random.Random(6), Lf=0.24)
    p, a = spots[-1]
    o = Vector((math.cos(a + 0.6), math.sin(a + 0.6), 0.3))
    orchid(bm, p + o * 0.04, o, 0.15, seed=9)
    # hanging bunches of white bars on short spurs off the vine
    for i, (z, a, n) in enumerate(((0.62, -1.6, 2), (0.95, -0.4, 2), (0.82, 2.6, 1), (1.18, -2.3, 1))):
        c = Vector((math.cos(a) * 0.065, math.sin(a) * 0.065, z))
        o = Vector((math.cos(a), math.sin(a), 0))
        spur = c + o * 0.08 + Vector((0, 0, 0.03))
        stalk(bm, [c, c + o * 0.05 + Vector((0, 0, 0.03)), spur], 0.009, 0.007, LEAF2, caps=("grid", "grid"))
        for j in range(n):
            side = Vector((-o.y, o.x, 0)) * (0.06 * (j - (n - 1) / 2))
            hang_bar(bm, spur + side, a + PI / 2 + (j - 0.5) * 0.3 * (n > 1), 0.085, 0.17, 0.026, LEAF2,
                     drop=0.03 + 0.02 * j, **BAR_WHITE)


def wc_item(bm):
    w, h = 0.16, 0.3
    put(bm, choc_bar(w, h, 0.04, cols=2, rows=4, **BAR_WHITE), Matrix.Translation((0, 0, h / 2 + 0.01)))


# ======================================================================== Truffle (cocoa-cup bush)

def cup_stems(bm, top, specs, rnd, leaf_s=DLEAF):
    """specs: (yaw, length, e0, e1). Returns stem tips + tip directions."""
    out = []
    for yaw, L, e0, e1 in specs:
        pts = arc((math.cos(yaw) * 0.015, math.sin(yaw) * 0.015, top - 0.02), yaw, L, e0, e1, 6, seed=int(yaw * 10))
        stalk(bm, pts, 0.012, 0.009, TRUNK, caps=("grid", "grid"))
        for i in (2, 4):
            leaf(bm, pts[i], yaw + (1.6 if i == 2 else -1.6) + rnd.uniform(-0.3, 0.3), 0.12 * (L / 0.6) ** 0.3,
                 0.06 * (L / 0.6) ** 0.3, 25, -15, leaf_s, 0.25)
        out.append((pts[-1], (pts[-1] - pts[-2]).normalized()))
    return out


def cup_on(bm, tip, d, R, s, fill=None, seed=0):
    m = Matrix.Translation(tip - d * 0.01) @ rot_to(d)
    merge(bm, cup(R, R * 0.8, s), m)
    if fill:
        put(bm, fill, m @ Matrix.Translation((0, 0, R * 0.8 + R * 0.35)))


def tr_seed(bm):
    top = soil(bm, 0.2, 0.055)
    seeds_on(bm, top, [mk_ball(CHOC_D, 0.013), mk_ball(CHOC, 0.012), mk_ball(CHOC_D, 0.013), mk_ball(CHOC, 0.012)])


def tr_s1(bm):
    sprout(bm, soil(bm, 0.2, 0.055), TRUNK, DLEAF, L=0.07, W=0.04)


def tr_s2(bm):
    top = soil(bm, 0.21, 0.06)
    rnd = random.Random(2)
    stalk(bm, [(0, 0, top - 0.02), (0, 0, top + 0.06), (0, 0, top + 0.11)], 0.011, 0.008, TRUNK)
    leaves(bm, (0, 0, top + 0.1), 3, 0.1, 0.055, 30, -10, DLEAF, rnd)


def tr_s3(bm):
    top = soil(bm, 0.24, 0.065)
    rnd = random.Random(3)
    tips = cup_stems(bm, top, [(0.3, 0.28, 80, 65), (2.4, 0.22, 65, 40), (4.4, 0.22, 65, 40)], rnd)
    p, d = tips[0]
    ball(bm, p + d * 0.02, 0.022, PAPER, (1, 1, 1.3), m=rot_to(d))


def tr_s4(bm):
    top = soil(bm, 0.3, 0.07)
    rnd = random.Random(4)
    tips = cup_stems(bm, top, [(0.0, 0.48, 85, 70), (1.3, 0.4, 70, 45), (2.6, 0.38, 65, 40), (3.9, 0.4, 70, 45),
                               (5.2, 0.36, 65, 40)], rnd)
    for p, d in tips:
        ball(bm, p + d * 0.025, 0.03, PAPER, (1, 1, 1.35), m=rot_to(d))


def tr_s5(bm):
    top = soil(bm, 0.33, 0.075)
    rnd = random.Random(5)
    tips = cup_stems(bm, top, [(0.0, 0.7, 85, 72), (1.1, 0.58, 70, 45), (2.2, 0.55, 65, 40), (3.3, 0.6, 70, 45),
                               (4.4, 0.52, 65, 40), (5.5, 0.56, 70, 45)], rnd)
    for i, (p, d) in enumerate(tips):
        nib = new_part()
        merge(nib, sphere_part(0.04, 2, (1, 1, 0.85), CHOC, lambda v: 0.5 - v.co.z / 0.068))
        cup_on(bm, p, d, 0.05, PAPER, nib)


def tr_s6(bm):
    top = soil(bm, 0.4, 0.085)
    rnd = random.Random(6)
    tips = cup_stems(bm, top, [(0.0, 0.95, 85, 74), (0.95, 0.78, 72, 48), (1.85, 0.72, 65, 40), (2.8, 0.8, 72, 48),
                               (3.75, 0.7, 65, 40), (4.65, 0.76, 72, 48), (5.55, 0.7, 66, 42)], rnd)
    styles = [(CHOC_D, WCHOC), (CHOC, CHOC_D), (CHOC_D, HPINK), (CHOC_D, WCHOC), (CHOC, WCHOC), (CHOC_D, GOLD), (CHOC, CHOC_D)]
    for i, (p, d) in enumerate(tips):
        body, dz = styles[i]
        cup_on(bm, p, d, 0.075, PAPER if i % 2 == 0 else GOLD, truffle(0.078, body, dz, seed=i), seed=i)


def tr_item(bm):
    R = 0.1
    merge(bm, cup(R, R * 0.8, PAPER))
    put(bm, truffle(0.105, CHOC_D, WCHOC, seed=1), Matrix.Translation((0, 0, R * 0.8 + 0.105 * 0.35)))


# ======================================================================== Lollipop

def lp_seed(bm):
    top = soil(bm, 0.2, 0.055)
    seeds_on(bm, top, [mk_ball(PINK_C, 0.013), mk_ball(BLUE_C, 0.013), mk_ball(YEL_C, 0.013), mk_ball(GRN_C, 0.013)])


def lp_s1(bm):
    top = sprout(bm, soil(bm, 0.2, 0.055), WHITE_G, MINT)
    ball(bm, (0, 0, top + 0.008), 0.013, PINK_C, cuts=1)


def lp_s2(bm):
    top = soil(bm, 0.21, 0.06)
    rnd = random.Random(2)
    lolly(bm, (0, 0, top - 0.02), 0.2, 0.04, pop_pink, PINK_C)
    leaves(bm, (0, 0, top + 0.03), 3, 0.1, 0.04, 30, 0, MINT, rnd)


def lp_s3(bm):
    top = soil(bm, 0.24, 0.065)
    rnd = random.Random(3)
    lolly(bm, (0, 0, top - 0.02), 0.38, 0.075, pop_pink, PINK_C, lean=(0.02, 0))
    leaves(bm, (0, 0, top + 0.02), 4, 0.14, 0.05, 30, -5, MINT, rnd)


def lp_s4(bm):
    top = soil(bm, 0.3, 0.07)
    rnd = random.Random(4)
    lolly(bm, (0.03, 0, top - 0.02), 0.62, 0.1, pop_pink, PINK_C, lean=(0.05, 0), yaw=-0.2)
    lolly(bm, (-0.03, 0.01, top - 0.02), 0.45, 0.075, pop_blue, BLUE_C, lean=(-0.08, 0.02), yaw=0.3)
    leaves(bm, (0, 0, top + 0.02), 5, 0.17, 0.055, 30, -10, MINT, rnd)


def lp_s5(bm):
    top = soil(bm, 0.33, 0.075)
    rnd = random.Random(5)
    lolly(bm, (0.0, 0.01, top - 0.02), 0.85, 0.12, pop_rainbow, RAINBOW, lean=(0.02, 0))
    lolly(bm, (0.04, 0, top - 0.02), 0.6, 0.09, pop_pink, PINK_C, lean=(0.16, -0.02), yaw=-0.3)
    lolly(bm, (-0.04, 0, top - 0.02), 0.52, 0.08, pop_blue, BLUE_C, lean=(-0.15, 0.02), yaw=0.3)
    leaves(bm, (0, 0, top + 0.02), 6, 0.2, 0.06, 30, -10, MINT, rnd)
    for i, (a, s) in enumerate(((-1.2, YEL_C), (-2.2, PINK_C), (0.4, GRN_C))):  # gumball buds
        ball(bm, (math.cos(a) * 0.16, math.sin(a) * 0.16, top + 0.02), 0.025, s, cuts=2)


def lp_s6(bm):
    top = soil(bm, 0.4, 0.085)
    rnd = random.Random(6)
    lolly(bm, (0.0, 0.02, top - 0.02), 1.2, 0.2, pop_rainbow, RAINBOW, lean=(0.02, 0))
    lolly(bm, (0.05, 0, top - 0.02), 0.85, 0.15, pop_pink, PINK_C, lean=(0.26, -0.03), yaw=-0.35)
    lolly(bm, (-0.05, 0, top - 0.02), 0.72, 0.13, pop_blue, BLUE_C, lean=(-0.25, 0.03), yaw=0.35)
    lolly(bm, (0.0, 0.06, top - 0.02), 0.55, 0.1, pop_sun, YEL_C, lean=(0.02, 0.18), yaw=PI)
    leaves(bm, (0, 0, top + 0.02), 7, 0.26, 0.075, 30, -15, MINT, rnd)
    leaves(bm, (0, 0.02, top + 0.35), 3, 0.14, 0.045, 30, 0, MINT, rnd, yaw0=0.5)


def lp_item(bm):
    lolly(bm, (0, 0, 0), 0.24, 0.12, pop_rainbow, RAINBOW)
    for sx in (-1, 1):  # ribbon bow under the pop
        pts = [Vector((sx * (0.012 + 0.045 * math.sin(PI * f)), -0.004, 0.125 + 0.01 * f + 0.03 * math.sin(TAU * f))) for f in
               [i / 7 for i in range(8)]]
        b, _, _ = tube(pts, [0.012 + 0.012 * math.sin(PI * i / 7) for i in range(8)], 8, flat=0.3, ref=Vector((0, 1, 0)))
        uv(b, HPINK)
        merge(bm, b)
    ball(bm, (0, -0.002, 0.13), 0.016, HPINK, cuts=1)


# ======================================================================== CandyCane (fiddlehead fern)

def fronds(bm, top, n, L, rnd, yaw0=0.0):
    leaves(bm, (0, 0, top), n, L, L * 0.22, 35, -25, MINT, rnd, yaw0=yaw0, flat=0.2)


def cc_seed(bm):
    top = soil(bm, 0.2, 0.055)
    seeds_on(bm, top, [mk_bead] * 4)


def cc_s1(bm):
    top = soil(bm, 0.2, 0.055)
    cane(bm, Vector((0, 0, top - 0.02)), 0.12, 0.028, 0.008, hook=330, shrink=0.6)
    for yaw in (0.9, 4.0):
        leaf(bm, (math.cos(yaw) * 0.01, math.sin(yaw) * 0.01, top), yaw, 0.07, 0.022, 30, 0, MINT)


def cc_s2(bm):
    top = soil(bm, 0.21, 0.06)
    cane(bm, Vector((0.01, 0, top - 0.02)), 0.24, 0.045, 0.011, yaw=-0.3, hook=380, shrink=0.65)
    cane(bm, Vector((-0.02, 0.02, top - 0.02)), 0.17, 0.035, 0.01, yaw=2.6, hook=380, shrink=0.65, scheme=cane_mint)
    fronds(bm, top, 3, 0.1, random.Random(2))


def cc_s3(bm):
    top = soil(bm, 0.24, 0.065)
    for (x, y, H, yaw, tl, sch) in ((0.0, 0.0, 0.42, -0.4, 0.05, cane_classic), (-0.04, 0.02, 0.34, 2.4, -0.1, cane_mint),
                                    (0.04, 0.03, 0.3, 1.2, 0.12, cane_classic)):
        cane(bm, Vector((x, y, top - 0.02)), H, 0.06, 0.014, yaw=yaw, hook=290, shrink=0.4, scheme=sch, tilt=tl)
    fronds(bm, top, 5, 0.15, random.Random(3))


def cc_s4(bm):
    top = soil(bm, 0.3, 0.07)
    for (x, y, H, yaw, tl, sch) in ((0.0, 0.0, 0.72, -0.5, 0.04, cane_classic), (-0.08, 0.03, 0.6, 2.5, -0.18, cane_mint),
                                    (0.08, 0.03, 0.56, 1.1, 0.2, cane_classic), (0.0, -0.07, 0.48, 4.0, 0.16, cane_mint)):
        cane(bm, Vector((x, y, top - 0.02)), H, 0.08, 0.018, yaw=yaw, hook=220, shrink=0.15, scheme=sch, tilt=tl)
    fronds(bm, top, 6, 0.22, random.Random(4))


def cc_s5(bm):
    top = soil(bm, 0.33, 0.075)
    for (x, y, H, yaw, tl, sch) in ((0.0, 0.0, 0.98, -0.5, 0.04, cane_classic), (-0.1, 0.04, 0.82, 2.5, -0.2, cane_mint),
                                    (0.1, 0.04, 0.76, 1.1, 0.22, cane_classic), (0.0, -0.09, 0.66, 4.0, 0.18, cane_mint),
                                    (0.04, 0.1, 0.6, 5.3, -0.2, cane_classic)):
        cane(bm, Vector((x, y, top - 0.02)), H, 0.1, 0.022, yaw=yaw, hook=205, scheme=sch, tilt=tl)
    fronds(bm, top, 7, 0.26, random.Random(5))
    for i, a in enumerate((-1.3, -2.4, 0.2)):  # peppermint buds in the fronds
        merge(bm, peppermint(0.03, 0.016), Matrix.Translation((math.cos(a) * 0.17, math.sin(a) * 0.17, top + 0.04)) @
              Matrix.Rotation(a + PI / 2, 4, 'Z') @ Matrix.Rotation(-0.4, 4, 'X'))


def cc_s6(bm):
    top = soil(bm, 0.4, 0.085)
    specs = ((0.0, 0.0, 1.35, -0.6, 0.04, cane_classic), (-0.13, 0.05, 1.15, 2.4, -0.22, cane_mint),
             (0.13, 0.05, 1.08, 1.0, 0.24, cane_classic), (0.0, -0.12, 0.95, 4.0, 0.2, cane_mint),
             (0.06, 0.13, 0.88, 5.2, -0.22, cane_classic), (-0.1, -0.08, 0.8, 3.1, 0.26, cane_classic))
    for i, (x, y, H, yaw, tl, sch) in enumerate(specs):
        tip = cane(bm, Vector((x, y, top - 0.02)), H, 0.12, 0.026, yaw=yaw, hook=195, scheme=sch, tilt=tl)
        if i < 4:  # a peppermint hangs from the hook tip on a little thread
            stalk(bm, [tip, tip - Vector((0, 0, 0.04)), tip - Vector((0, 0, 0.07))], 0.004, 0.004, WHITE_G,
                  caps=("grid", "grid"))
            merge(bm, peppermint(0.045, 0.022, a=(RED if i % 2 == 0 else MINT_C)),
                  Matrix.Translation(tip - Vector((0, 0, 0.11))) @ Matrix.Rotation(yaw + PI / 2, 4, 'Z'))
    fronds(bm, top, 8, 0.32, random.Random(6))


def cc_item(bm):
    cane(bm, Vector((0, 0, 0)), 0.42, 0.075, 0.022, hook=195, scheme=cane_mint)


# ======================================================================== LavaPlant

def lv_seed(bm):
    top = lava_rock(bm, 0.2, 0.055)
    seeds_on(bm, top, [mk_ball(HOT, 0.013), lambda b, p, a: rock(b, p, 0.016, 3), mk_ball(HOT, 0.012),
                       lambda b, p, a: rock(b, p, 0.014, 4)], rad=0.07)


def lv_s1(bm):
    top = lava_rock(bm, 0.2, 0.055)
    obsidian(bm, [(0, 0, top - 0.02), (0, 0, top + 0.04), (0, 0, top + 0.07)], 0.011, 0.008)
    for yaw in (0.4, PI + 0.4):
        flame_leaf(bm, (math.cos(yaw) * 0.006, math.sin(yaw) * 0.006, top + 0.06), yaw, 0.08, 0.03)


def lv_s2(bm):
    top = lava_rock(bm, 0.21, 0.06)
    obsidian(bm, [(0, 0, top - 0.02), (0.01, 0, top + 0.08), (0, 0, top + 0.16)], 0.014, 0.009)
    for j in range(3):
        yaw = TAU * j / 3 + 0.3
        flame_leaf(bm, (math.cos(yaw) * 0.008, math.sin(yaw) * 0.008, top + 0.15), yaw, 0.1, 0.034, 55, 85, seed=j)


def lava_stalks(bm, top, specs, seed):
    """specs: (yaw, height, lean, r). Returns stalk tips."""
    rnd = random.Random(seed)
    tips = []
    for yaw, H, lean, r in specs:
        pts = arc((math.cos(yaw) * 0.02, math.sin(yaw) * 0.02, top - 0.03), yaw, H, 90 - lean, 85, 7,
                  wob=0.04 * H, seed=rnd.randint(0, 99))
        obsidian(bm, pts, r, r * 0.55)
        for i in (2, 4):
            a = yaw + (1.9 if i == 2 else -1.9)
            flame_leaf(bm, pts[i], a, 0.15 * H ** 0.5, 0.045 * H ** 0.5, 40, 80, seed=i)
        tips.append(pts[-1])
    return tips


def flame_crown(bm, p, n, L, W, seed=0):
    for j in range(n):
        yaw = TAU * j / n + 0.3
        flame_leaf(bm, p + Vector((math.cos(yaw), math.sin(yaw), 0)) * 0.01, yaw, L, W, 50, 88, seed=seed + j)


def lv_s3(bm):
    top = lava_rock(bm, 0.24, 0.065)
    tips = lava_stalks(bm, top, [(0.0, 0.38, 5, 0.018)], 3)
    flame_crown(bm, tips[0], 5, 0.12, 0.04)


def lv_s4(bm):
    top = lava_rock(bm, 0.3, 0.07)
    tips = lava_stalks(bm, top, [(0.0, 0.7, 4, 0.024), (2.5, 0.5, 18, 0.02)], 4)
    for i, p in enumerate(tips):
        flame_crown(bm, p, 5, 0.14, 0.045, seed=i * 5)
    rock(bm, (0.2, -0.12, 0.03), 0.05, 1)


def lv_s5(bm):
    top = lava_rock(bm, 0.33, 0.075)
    tips = lava_stalks(bm, top, [(0.0, 0.95, 4, 0.028), (2.5, 0.72, 22, 0.024), (5.5, 0.66, 24, 0.022)], 5)
    for i, p in enumerate(tips):
        flame_crown(bm, p, 5, 0.15, 0.048, seed=i * 5)
        put(bm, magma(0.04, seed=i, plates=12), Matrix.Translation(p + Vector((0, 0, 0.04))))
    rock(bm, (0.24, -0.12, 0.03), 0.055, 1)
    rock(bm, (-0.22, -0.16, 0.025), 0.045, 2)


def lv_s6(bm):
    top = lava_rock(bm, 0.4, 0.085)
    tips = lava_stalks(bm, top, [(0.0, 1.25, 4, 0.034), (2.5, 0.98, 24, 0.03), (5.5, 0.88, 26, 0.028)], 6)
    for i, p in enumerate(tips):
        flame_crown(bm, p, 6, 0.2, 0.06, seed=i * 6)
        put(bm, magma(0.11 - 0.012 * i, seed=i), Matrix.Translation(p + Vector((0, 0, 0.09 - 0.01 * i))))
    for i, (x, y, r) in enumerate(((0.3, -0.16, 0.07), (-0.28, -0.2, 0.055), (0.05, 0.36, 0.06), (-0.33, 0.14, 0.05))):
        rock(bm, (x, y, 0.025), r, i + 1)


def lv_item(bm):
    put(bm, magma(0.12, seed=7), Matrix.Translation((0, 0, 0.12)))
    obsidian(bm, [(0, 0, 0.225), (0.005, 0, 0.255), (0.015, 0, 0.28)], 0.012, 0.009)
    flame_leaf(bm, (0.012, 0, 0.27), 0.0, 0.1, 0.035, 40, 70)


# ======================================================================== CottonCandy

def paper_stick(bm, pts, r0, r1):
    return stalk(bm, pts, r0, r1, WHITE_G, 8, twist=0.8, caps=("grid", "grid"),
                 colour_of=lambda s, k: HPINK if k in (0, 4) else WHITE, cap_s=WHITE)


def ct_seed(bm):
    top = soil(bm, 0.2, 0.055)
    seeds_on(bm, top, [mk_cube(CC_PINK), mk_cube(CC_BLUE), mk_cube(WHITE), mk_cube(CC_PINK)])


def ct_s1(bm):
    top = sprout(bm, soil(bm, 0.2, 0.055), WHITE_G, MINT)
    fluff(bm, (0, 0, top + 0.015), 0.025, [CC_PINK], n=4, seed=1)


def ct_s2(bm):
    top = soil(bm, 0.21, 0.06)
    paper_stick(bm, [(0, 0, top - 0.02), (0.005, 0, top + 0.1), (0, 0, top + 0.18)], 0.01, 0.008)
    fluff(bm, (0, 0, top + 0.21), 0.05, [CC_PINK], n=5, seed=2)
    leaves(bm, (0, 0, top + 0.02), 3, 0.09, 0.035, 30, 0, MINT, random.Random(2))


def ct_stems(bm, top, specs, seed, leaf_n, leaf_L):
    rnd = random.Random(seed)
    for (yaw, H, lean, R, cols) in specs:
        pts = arc((math.cos(yaw) * 0.015, math.sin(yaw) * 0.015, top - 0.02), yaw, H, 90 - lean, 88, 5)
        paper_stick(bm, pts, 0.014 * (H / 0.8) ** 0.4, 0.011 * (H / 0.8) ** 0.4)
        fluff(bm, pts[-1] + Vector((0, 0, R * 0.6)), R, cols, seed=int(H * 100), n=7, cuts=3 if R > 0.1 else 2)
    leaves(bm, (0, 0, top + 0.02), leaf_n, leaf_L, leaf_L * 0.36, 30, -10, MINT, rnd)


def ct_s3(bm):
    ct_stems(bm, soil(bm, 0.24, 0.065), [(0.0, 0.34, 5, 0.075, [CC_PINK]), (2.6, 0.24, 22, 0.06, [CC_BLUE])], 3, 4, 0.12)


def ct_s4(bm):
    ct_stems(bm, soil(bm, 0.3, 0.07), [(0.0, 0.58, 4, 0.11, [CC_PINK]), (2.1, 0.44, 26, 0.09, [CC_BLUE]),
                                       (5.5, 0.4, 22, 0.08, [CC_PINK, CC_BLUE])], 4, 5, 0.16)


def ct_s5(bm):
    top = soil(bm, 0.33, 0.075)
    ct_stems(bm, top, [(0.0, 0.8, 4, 0.14, [CC_PINK]), (2.5, 0.62, 28, 0.12, [CC_BLUE]),
                       (5.5, 0.56, 30, 0.11, [CC_PINK, CC_BLUE])], 5, 6, 0.2)
    for i, a in enumerate((-1.4, 0.6)):
        fluff(bm, (math.cos(a) * 0.16, math.sin(a) * 0.16, top + 0.03), 0.03, [CC_BLUE if i else CC_PINK], n=4, seed=10 + i)


def ct_s6(bm):
    ct_stems(bm, soil(bm, 0.4, 0.085), [(0.0, 1.08, 3, 0.24, [CC_PINK]), (2.5, 0.86, 30, 0.2, [CC_BLUE]),
                                        (5.5, 0.76, 32, 0.18, [CC_PINK, CC_BLUE, CC_PINK])], 6, 7, 0.26)


def ct_item(bm):
    paper_stick(bm, [(0, 0, 0.0), (0, 0, 0.06), (0, 0, 0.12), (0, 0, 0.18)], 0.008, 0.045)
    fluff(bm, (0, 0, 0.27), 0.12, [CC_PINK, CC_BLUE, CC_PINK], n=8, seed=7, cuts=3)


# ======================================================================== PinkCloud

def curl_stalk(bm, base, yaw, H, r, seed=0, lean=6):
    pts = arc(base, yaw, H, 90 - lean, 90, 8, wob=0.06 * H, wf=3.0, seed=seed)
    stalk(bm, pts, r, r * 0.7, LAV, caps=("grid", "grid"))
    return pts


def hang_drops(bm, c, R, n, seed=0):
    rnd = random.Random(seed)
    for i in range(n):
        x = (i - (n - 1) / 2) * 0.42 * R + rnd.uniform(-0.05, 0.05) * R
        r = R * rnd.uniform(0.09, 0.12)
        merge(bm, drop(r, HPINK if i % 2 else PINK), Matrix.Translation(Vector(c) + Vector((x, -0.1 * R, -0.28 * R - 2.0 * r))))


def pc_seed(bm):
    top = soil(bm, 0.2, 0.055)
    seeds_on(bm, top, [mk_puff(CPINK), mk_puff(CPINK), mk_puff(CPINK)])


def pc_s1(bm):
    top = sprout(bm, soil(bm, 0.2, 0.055), LAV, MINT)
    put(bm, cloud(0.03, CPINK, seed=1), Matrix.Translation((0, 0, top + 0.012)))


def pc_s2(bm):
    top = soil(bm, 0.21, 0.06)
    pts = curl_stalk(bm, (0, 0, top - 0.02), 0.0, 0.2, 0.01, 2)
    put(bm, cloud(0.055, CPINK, seed=2), Matrix.Translation(pts[-1] + Vector((0, 0, 0.012))))
    leaves(bm, (0, 0, top + 0.03), 2, 0.09, 0.04, 30, 0, MINT, random.Random(2), yaw0=0.3)


def pc_s3(bm):
    top = soil(bm, 0.24, 0.065)
    pts = curl_stalk(bm, (0, 0, top - 0.02), 0.0, 0.38, 0.013, 3)
    put(bm, cloud(0.09, CPINK, seed=3), Matrix.Translation(pts[-1] + Vector((0, 0, 0.02))))
    leaves(bm, (0, 0, top + 0.03), 3, 0.12, 0.05, 30, -5, MINT, random.Random(3))


def pc_s4(bm):
    top = soil(bm, 0.3, 0.07)
    a = curl_stalk(bm, (0.01, 0, top - 0.02), 0.0, 0.62, 0.016, 4)
    b = curl_stalk(bm, (-0.02, 0.01, top - 0.02), 2.8, 0.44, 0.013, 5)
    put(bm, cloud(0.13, CPINK, seed=4), Matrix.Translation(a[-1] + Vector((0, 0, 0.03))))
    put(bm, cloud(0.09, CPINK, seed=5), Matrix.Translation(b[-1] + Vector((0, 0, 0.02))))
    leaves(bm, (0, 0, top + 0.03), 4, 0.15, 0.06, 30, -10, MINT, random.Random(4))


def pc_s5(bm):
    top = soil(bm, 0.33, 0.075)
    a = curl_stalk(bm, (0.01, 0, top - 0.02), 0.0, 0.86, 0.02, 6)
    b = curl_stalk(bm, (-0.02, 0.01, top - 0.02), 2.9, 0.62, 0.016, 7, lean=18)
    c = curl_stalk(bm, (0.02, 0.02, top - 0.02), 0.25, 0.55, 0.015, 8, lean=18)
    for p, R, sd in ((a[-1], 0.17, 6), (b[-1], 0.11, 7), (c[-1], 0.1, 8)):
        put(bm, cloud(R, CPINK, seed=sd), Matrix.Translation(p + Vector((0, 0, 0.2 * R))))
    hang_drops(bm, a[-1] + Vector((0, 0, 0.034)), 0.17, 2, 6)
    leaves(bm, (0, 0, top + 0.03), 5, 0.18, 0.065, 30, -10, MINT, random.Random(5))


def pc_s6(bm):
    top = soil(bm, 0.4, 0.085)
    a = curl_stalk(bm, (0.01, 0, top - 0.02), 0.0, 1.12, 0.026, 9)
    b = curl_stalk(bm, (-0.03, 0.01, top - 0.02), 2.9, 0.78, 0.019, 10, lean=24)
    c = curl_stalk(bm, (0.03, 0.02, top - 0.02), 0.25, 0.7, 0.018, 11, lean=24)
    big = a[-1] + Vector((0, 0, 0.06))
    put(bm, cloud(0.3, CPINK, seed=9, face=True), Matrix.Translation(big))
    hang_drops(bm, big, 0.3, 4, 9)
    for p, R, sd in ((b[-1], 0.15, 10), (c[-1], 0.14, 11)):
        cc = p + Vector((0, 0, 0.2 * R))
        put(bm, cloud(R, CPINK, seed=sd), Matrix.Translation(cc))
        hang_drops(bm, cc, R, 2, sd)
    leaves(bm, (0, 0, top + 0.03), 6, 0.22, 0.08, 30, -12, MINT, random.Random(6))


def pc_item(bm):
    R = 0.15
    put(bm, cloud(R, CPINK, seed=12, face=True), Matrix.Translation((0, 0, 0.3 * R + 0.05)))
    hang_drops(bm, (0, 0, 0.3 * R + 0.05), R, 2, 12)


# ======================================================================== RainbowTruffle

PETALS = [REDP, ORG, YEL, GRN, BLU, PURP, PINK]


def rt_stem(bm, base, yaw, H, lean, rnd, r=0.014):
    pts = arc(base, yaw, H, 90 - lean, 86, 7, wob=0.03 * H, seed=rnd.randint(0, 99))
    stalk(bm, pts, r, r * 0.65, LEAF, caps=("grid", "grid"))
    for i in (2, 4):
        leaf(bm, pts[i], yaw + (1.7 if i == 2 else -1.5), 0.14 * H ** 0.4, 0.05 * H ** 0.4, 25, -20, LEAF2, 0.22)
    return pts[-1], (pts[-1] - pts[-2]).normalized()


def rt_bud(bm, p, d, size):
    bloom(bm, p, d, size, PETALS, None, n=7, e0=72, e1=108, L=0.6, W=0.22)


def rt_flower(bm, p, d, size, r_tr, seed=0):
    bloom(bm, p, d, size, PETALS, None, n=7, e0=48, e1=12, L=0.6, W=0.26, seed=seed)
    put(bm, truffle(r_tr, RAINBOW, sprinkles=14, seed=seed), Matrix.Translation(p + d * r_tr * 0.95) @ rot_to(d))


def rt_seed(bm):
    top = soil(bm, 0.2, 0.055)
    seeds_on(bm, top, [mk_sprinkle(s) for s in (PINK_C, YEL_C, BLUE_C, GRN_C, ORG_C, PURP_C)], rad=0.055)


def rt_s1(bm):
    top = sprout(bm, soil(bm, 0.2, 0.055), LEAF, LEAF2)
    rt_bud(bm, Vector((0, 0, top + 0.003)), Z, 0.05)


def rt_s2(bm):
    top = soil(bm, 0.21, 0.06)
    p, d = rt_stem(bm, (0, 0, top - 0.02), 0.0, 0.2, 2, random.Random(2), 0.01)
    rt_bud(bm, p, d, 0.09)


def rt_s3(bm):
    top = soil(bm, 0.24, 0.065)
    p, d = rt_stem(bm, (0, 0, top - 0.02), 0.0, 0.4, 3, random.Random(3), 0.012)
    rt_bud(bm, p, d, 0.12)


def rt_s4(bm):
    top = soil(bm, 0.3, 0.07)
    rnd = random.Random(4)
    for yaw, H, lean, s in ((0.0, 0.62, 3, 0.16), (2.6, 0.45, 20, 0.12)):
        p, d = rt_stem(bm, (math.cos(yaw) * 0.015, math.sin(yaw) * 0.015, top - 0.02), yaw, H, lean, rnd)
        rt_bud(bm, p, d, s)


def rt_s5(bm):
    top = soil(bm, 0.33, 0.075)
    rnd = random.Random(5)
    for i, (yaw, H, lean, s) in enumerate(((0.0, 0.85, 3, 0.3), (2.5, 0.62, 22, 0.18), (5.5, 0.56, 24, 0.16))):
        p, d = rt_stem(bm, (math.cos(yaw) * 0.015, math.sin(yaw) * 0.015, top - 0.02), yaw, H, lean, rnd, 0.016)
        if i == 0:  # first flower opening, truffle just showing
            bloom(bm, p, d, s, PETALS, None, n=7, e0=62, e1=48, L=0.55, W=0.24)
            put(bm, truffle(0.04, RAINBOW, sprinkles=8, seed=3), Matrix.Translation(p + d * 0.03) @ rot_to(d))
        else:
            rt_bud(bm, p, d, s)


def rt_s6(bm):
    top = soil(bm, 0.4, 0.085)
    rnd = random.Random(6)
    for i, (yaw, H, lean, s, r) in enumerate(((0.0, 1.15, 3, 0.42, 0.1), (2.5, 0.9, 24, 0.34, 0.085),
                                              (5.5, 0.8, 26, 0.32, 0.08))):
        p, d = rt_stem(bm, (math.cos(yaw) * 0.015, math.sin(yaw) * 0.015, top - 0.02), yaw, H, lean, rnd, 0.02)
        rt_flower(bm, p, d, s, r, seed=i)
    leaves(bm, (0, 0, top + 0.03), 5, 0.2, 0.065, 30, -12, LEAF2, rnd)


def rt_item(bm):
    R = 0.1
    merge(bm, cup(R, R * 0.8, GOLD))
    put(bm, truffle(0.105, RAINBOW, sprinkles=24, seed=4), Matrix.Translation((0, 0, R * 0.8 + 0.105 * 0.35)))


# ======================================================================== build

CROPS = [
    ("ChocolateBar", [choc_seed, choc_s1, choc_s2, choc_s3, choc_s4, choc_s5, choc_s6, choc_item]),
    ("WhiteChocolate", [wc_seed, wc_s1, wc_s2, wc_s3, wc_s4, wc_s5, wc_s6, wc_item]),
    ("Truffle", [tr_seed, tr_s1, tr_s2, tr_s3, tr_s4, tr_s5, tr_s6, tr_item]),
    ("Lollipop", [lp_seed, lp_s1, lp_s2, lp_s3, lp_s4, lp_s5, lp_s6, lp_item]),
    ("CandyCane", [cc_seed, cc_s1, cc_s2, cc_s3, cc_s4, cc_s5, cc_s6, cc_item]),
    ("LavaPlant", [lv_seed, lv_s1, lv_s2, lv_s3, lv_s4, lv_s5, lv_s6, lv_item]),
    ("CottonCandy", [ct_seed, ct_s1, ct_s2, ct_s3, ct_s4, ct_s5, ct_s6, ct_item]),
    ("PinkCloud", [pc_seed, pc_s1, pc_s2, pc_s3, pc_s4, pc_s5, pc_s6, pc_item]),
    ("RainbowTruffle", [rt_seed, rt_s1, rt_s2, rt_s3, rt_s4, rt_s5, rt_s6, rt_item]),
]
SUFFIX = ["_Seed", "_Stage1", "_Stage2", "_Stage3", "_Stage4", "_Stage5", "_Stage6", ""]
PX = [0, 0.6, 1.2, 1.85, 2.7, 3.75, 5.0, 6.2]


def build_premium(only=None, parent="PremiumCrops", row0=-3.0, dy=-2.2):
    root = bpy.data.collections.get(parent) or bpy.data.collections.new(parent)
    if root.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(root)
    mat = gradient_material()
    out = {}
    for ci, (crop, fns) in enumerate(CROPS):
        if only and crop not in only:
            continue
        coll = bpy.data.collections.get(crop) or bpy.data.collections.new(crop)
        if coll.name not in root.children:
            root.children.link(coll)
        for si, fn in enumerate(fns):
            name = "SM_" + crop + SUFFIX[si]
            old = bpy.data.objects.get(name)
            if old:
                bpy.data.objects.remove(old)
            bm = bmesh.new()
            fn(bm)
            me = bpy.data.meshes.get(name) or bpy.data.meshes.new(name)
            bm.to_mesh(me)
            bm.free()
            if "t" in me.attributes:
                me.attributes.remove(me.attributes["t"])
            me.materials.clear()
            me.materials.append(mat)
            ob = bpy.data.objects.new(name, me)
            ob.location = (PX[si], row0 + dy * ci, 0)
            coll.objects.link(ob)
            r = topo_check(ob, "quad")
            out[name] = {k: r[k] for k in ("faces", "quads", "tris", "ngons", "open_edges", "double_verts",
                                           "inside_out_parts")}
            out[name]["zfight"] = len(zfight(ob))
    return out
