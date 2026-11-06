# Dragon fruit crop from Dante's sheet: Seed + 6 growth stages + harvested fruit (whole + half).
# ONE material (M_GradientTexture = gradient atlas v3), smooth shading, all quads except the
# spine points (a point needs its pole). Built with blender-clean-topology's quad helpers.
#   exec(open(r"<skills>/blender-game-props/dragon_fruit.py").read())
#   build_dragon_fruit()   -> {object name: topo summary}
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

_CT = _skill("blender-clean-topology")
for _f in ("quad_build.py", "topo_check.py", "topo_clean.py"):
    exec(open(_CT + "/" + _f).read())

ATLAS = __import__("os").path.expanduser(r"~/Desktop/Farm/Crops/GradientTexture_v3.png")
_ROWS = {"r1": (6, 316), "r2": (330, 630), "r3": (712, 1003), "r4": (1040, 1331)}  # pixel y, top down


def strip(row, col, t0=0.0, t1=1.0):
    """(u, v at t=0, v at t=1) of one atlas gradient column; t0/t1 pick a part of it."""
    y0, y1 = _ROWS[row]
    v = lambda t: 1 - (y0 + (y1 - y0) * t) / 2048
    return ((28 + 57 * col) / 2048, v(t0), v(t1))


STEM = strip("r3", 4, 0.0, 0.7)     # fresh green -> dark green
SPROUT = strip("r1", 1, 0.0, 1.0)   # lime
SPINE = strip("r1", 3, 0.0, 0.6)    # yellow-lime
FRUIT = strip("r3", 20, 0.0, 0.45)  # magenta pink, darker underneath
BRACT = strip("r3", 20, 0.25, 0.0)  # bract base: fruit pink, lighter outward
TIP = strip("r1", 24, 0.0, 0.35)    # bract / sepal tips: lime
PETAL = strip("r4", 8, 0.0, 0.6)    # cream tip -> yellow base
STAMEN = strip("r4", 22, 0.0, 0.6)  # yellow
SOIL = strip("r2", 2, 0.55, 1.0)    # soil rim -> dark soil centre
WOOD = strip("r2", 2, 0.45, 0.75)   # warm brown wood
SEED = strip("r2", 7, 0.2, 0.8)     # black
FLESH = strip("r4", 4, 0.0, 0.2)    # white
Z = Vector((0, 0, 1))


# ---------- part plumbing: every part is its own bmesh with a "t" vert layer, UV'd, then merged

def new_part():
    b = bmesh.new()
    b.verts.layers.float.new("t")
    b.loops.layers.uv.new("UVMap")
    return b


def retag(b, fn):
    tl = b.verts.layers.float["t"]
    for v in b.verts:
        v[tl] = fn(v)


def uv(b, s, flip=False):
    u, va, vb = s
    tl = b.verts.layers.float["t"]
    ul = b.loops.layers.uv["UVMap"]
    for f in b.faces:
        for l in f.loops:
            t = min(max(l.vert[tl], 0.0), 1.0)
            l[ul].uv = (u, va + (vb - va) * (1 - t if flip else t))


def uv_split(b, s_base, s_tip, cut=0.6):
    """Two colours on one part without a smear: each FACE samples one strip (base strip where
    the face's average t < cut, else the tip strip), so no face spans two atlas columns."""
    tl = b.verts.layers.float["t"]
    ul = b.loops.layers.uv["UVMap"]
    for f in b.faces:
        tip = sum(v[tl] for v in f.verts) / len(f.verts) >= cut
        u, va, vb = s_tip if tip else s_base
        for l in f.loops:
            t = min(max(l.vert[tl], 0.0), 1.0)
            t = (t - cut) / (1 - cut) if tip else t / cut
            l[ul].uv = (u, va + (vb - va) * min(max(t, 0.0), 1.0))


def merge(bm, b, mat=None):
    for f in b.faces:
        f.smooth = True
    if mat is not None:
        bmesh.ops.transform(b, matrix=mat, verts=b.verts)
    orient_outward(b)
    me = bpy.data.meshes.new("_tmp")
    b.to_mesh(me)
    b.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)


def sphere_part(r, cuts, scale, s, tfn, flip=False):
    q = quad_sphere(r, cuts, scale)
    b = new_part()
    me = bpy.data.meshes.new("_tmp")
    q.to_mesh(me)
    q.free()
    b.from_mesh(me)
    bpy.data.meshes.remove(me)
    retag(b, tfn)
    uv(b, s, flip)
    return b


def tube(pts, radii, sides=8, section=None, flat=1.0, ref=None, caps=("strip", "strip"), dome=0.6):
    """Closed quad tube along pts (ring frames carried along the path, no twisting). radii per
    ring, flat squashes the 2nd axis, section(i, k) multiplies a ring vert's radius (ribs, wings).
    caps per end: "strip" | "grid" (sides % 4 == 0) | "dome" (grid lifted outward) | None.
    Returns (bmesh, rings, tangents); t layer = position along the path (0 start, 1 end)."""
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
        rx = radii[i]
        ring = []
        for k in range(sides):
            a = 2 * math.pi * k / sides
            m = section(i, k) if section else 1.0
            v = b.verts.new(p + ax * (math.cos(a) * rx * m) + ay * (math.sin(a) * rx * flat * m))
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


def box_part(size, center, s, axis=2, bevel=0.006):
    q = quad_box(size, bevel=bevel)
    b = new_part()
    me = bpy.data.meshes.new("_tmp")
    q.to_mesh(me)
    q.free()
    b.from_mesh(me)
    bpy.data.meshes.remove(me)
    h = size[axis] / 2
    retag(b, lambda v: 0.5 - v.co[axis] / (2 * h))
    uv(b, s)
    bmesh.ops.translate(b, vec=Vector(center), verts=b.verts)
    return b


def spine(bm, pos, d, length=0.022, base=0.006):
    """Small spike as a tapered box (6 quads, closed): its tip is a tiny square instead of a
    point, so the model stays 100% quads and still reads as pointed."""
    d = d.normalized()
    a = d.cross(Z if abs(d.z) < 0.9 else Vector((1, 0, 0))).normalized()
    c = d.cross(a)
    b = new_part()
    tl = b.verts.layers.float["t"]
    sq = ((1, 1), (-1, 1), (-1, -1), (1, -1))
    q = [b.verts.new(pos - d * 0.004 + (a * x + c * y) * base) for x, y in sq]
    t = [b.verts.new(pos + d * length + (a * x + c * y) * base * 0.12) for x, y in sq]
    for v in q:
        v[tl] = 1.0
    for v in t:
        v[tl] = 0.0
    b.faces.new(q)
    b.faces.new(t[::-1])
    for i in range(4):
        j = (i + 1) % 4
        b.faces.new((q[i], q[j], t[j], t[i]))
    uv(b, SPINE)
    merge(bm, b)


# ---------- plant pieces

def mound(bm, R, h):
    prof = [(R, 0.0), (R * 0.98, h * 0.3), (R * 0.85, h * 0.62), (R * 0.6, h * 0.88), (R * 0.32, h)]
    b, rings, _ = tube([(0, 0, z) for _, z in prof], [r for r, _ in prof], sides=16,
                       caps=("grid", "dome"), dome=0.25)
    retag(b, lambda v: 1 - min(Vector((v.co.x, v.co.y)).length / R, 1.0))
    uv(b, SOIL)
    merge(bm, b)
    return h + 0.25 * R * 0.32  # height of the top centre


def seeds(bm, top, n=4, seed=1):
    rnd = random.Random(seed)
    for i in range(n):
        a = 2 * math.pi * i / n + 0.4
        b = sphere_part(1.0, 1, (0.022, 0.013, 0.011), SEED, lambda v: 0.5)
        m = Matrix.Translation((math.cos(a) * 0.045, math.sin(a) * 0.045, top - 0.006)) @ \
            Matrix.Rotation(a + rnd.uniform(-0.6, 0.6), 4, 'Z')
        merge(bm, b, m)


def leaf(bm, base, yaw, L, W, e0, e1, s, flat=0.25, n=6):
    d = lambda e: Vector((math.cos(e) * math.cos(yaw), math.cos(e) * math.sin(yaw), math.sin(e)))
    pts, p = [], Vector(base)
    for i in range(n):
        pts.append(p.copy())
        p += d(math.radians(e0 + (e1 - e0) * i / (n - 1))) * (L / (n - 1))
    radii = [W * max(0.12, math.sin(math.pi * (0.12 + 0.8 * i / (n - 1)))) for i in range(n)]
    side = Vector((-math.sin(yaw), math.cos(yaw), 0))
    b, _, _ = tube(pts, radii, 8, flat=flat, ref=side)
    uv(b, s)
    merge(bm, b)


def rib12(depth=0.14):
    return lambda i, k: 1.0 if k % 2 == 0 else 1 - depth


def column(bm, pts, r, top_round=True, joints=(), spines_at=(), seed=0):
    """Ribbed young cactus column (12 sides = 6 ribs) with a rounded top and spines on the ribs."""
    pts = [Vector(p) for p in pts]
    radii = [r] * len(pts)
    for j in joints:  # pinched segment joints
        radii[j] *= 0.82
    if top_round:
        d = (pts[-1] - pts[-2]).normalized()
        end = pts[-1]
        for a in (35, 65):
            pts.append(end + d * (r * math.sin(math.radians(a))))
            radii.append(r * math.cos(math.radians(a)))
    b, rings, tang = tube(pts, radii, 12, section=rib12(), caps=("grid", "dome" if top_round else "grid"), dome=0.55)
    uv(b, STEM, flip=True)
    tips = [(rings[i][k].co.copy(), (rings[i][k].co - pts[i]).normalized()) for i in spines_at for k in range(0, 12, 2)]
    merge(bm, b)
    rnd = random.Random(seed)
    for pos, d in tips:
        if rnd.random() < 0.8:
            spine(bm, pos, d, length=0.016, base=0.004)


def pad_section(i, k):
    return (1.0, 0.55, 1.0, 0.55)[k % 4]  # wings at k=0/4, ridges at k=2/6 (squashed by flat)


def pad(bm, base, yaw, L, e0, e1, W, nsc=4, spines=True, flat=0.32, seed=0):
    """Mature dragon fruit stem: flat 2-winged strap with a ridge, scalloped edges, spines on the
    wing edges at each scallop, arching out and drooping. Returns its centre line."""
    N = nsc * 3 + 2
    d = lambda e: Vector((math.cos(e) * math.cos(yaw), math.cos(e) * math.sin(yaw), math.sin(e)))
    pts, p = [], Vector(base)
    for i in range(N):
        pts.append(p.copy())
        s = i / (N - 1)
        p += d(math.radians(e0 + (e1 - e0) * s ** 0.85)) * (L / (N - 1))
    radii = []
    for i in range(N):
        s = i / (N - 1)
        prof = (0.55 + 0.45 * min(s / 0.2, 1.0)) * (1 - 0.8 * max(0.0, (s - 0.55) / 0.45) ** 1.6)
        bump = math.sin(math.pi * nsc * s) ** 2
        radii.append(W * prof * (0.78 + 0.22 * bump))
    radii[-1] = W * 0.1
    side = d(math.radians(e0)).cross(Z)
    if side.length < 1e-6:
        side = Vector((1, 0, 0))
    b, rings, _ = tube(pts, radii, 8, section=pad_section, flat=flat, ref=side.normalized())
    uv(b, STEM, flip=True)
    tips = []
    if spines:
        for j in range(nsc):
            i = min(range(1, N - 1), key=lambda i: abs(i / (N - 1) - (j + 0.5) / nsc))
            for k in (0, 4):
                v = rings[i][k]
                tips.append((v.co.copy(), (v.co - pts[i]).normalized()))
    merge(bm, b)
    for pos, dd in tips:
        spine(bm, pos, dd)
    return pts


def fruit_part(r, rows=((5, -18), (5, 28)), crown=4, half=False, seed=0, cuts=3):
    """Dragon fruit around the origin (body centre), pink bract scales with lime tips. half=True
    cuts it at y=0 and shows white flesh with black seeds facing -Y (needs an odd cuts count so a
    vert loop runs along y=0)."""
    rnd = random.Random(seed)
    fb = new_part()
    sz = 1.12
    body = sphere_part(r, cuts, (1, 1, sz), FRUIT, lambda v: 0.5 - v.co.z / (2 * r * sz))
    if half:
        bmesh.ops.delete(body, geom=[v for v in body.verts if v.co.y < -1e-6], context='VERTS')
        ring_edges = [e for e in body.edges if e.is_boundary]
        ring = [ring_edges[0].verts[0]]
        prev = None
        while True:  # walk the cut's boundary loop in order
            v = ring[-1]
            nxt = [e.other_vert(v) for e in v.link_edges if e.is_boundary and e.other_vert(v) is not prev]
            if not nxt or nxt[0] is ring[0]:
                break
            prev = v
            ring.append(nxt[0])
        cap = grid_cap(body, ring, inner=0.86)
        ul = body.loops.layers.uv["UVMap"]
        rs = set(ring)
        for f in cap:
            s = FRUIT if any(v in rs for v in f.verts) else FLESH
            for l in f.loops:
                l[ul].uv = (s[0], s[1] + (s[2] - s[1]) * 0.15)
    merge(fb, body)
    if half:
        for i in range(26):
            a = rnd.uniform(0, 2 * math.pi)
            rr = math.sqrt(rnd.uniform(0.04, 0.7))
            c = Vector((math.cos(a) * rr * r * 0.85, 0.0, math.sin(a) * rr * r * sz * 0.85))
            merge(fb, box_part((0.012, 0.008, 0.007), (c.x, -0.002, c.z), SEED, bevel=0))
    specs = [(n, e, j * 0.5) for j, (n, e) in enumerate(rows)] + ([(crown, 72, 0.25)] if crown else [])
    for n, elev, off in specs:
        for j in range(n):
            az = 2 * math.pi * (j + off) / n + rnd.uniform(-0.15, 0.15)
            e = math.radians(elev)
            p = Vector((math.cos(e) * math.cos(az) * r, math.cos(e) * math.sin(az) * r, math.sin(e) * r * sz))
            nrm = Vector((p.x, p.y, p.z / (sz * sz))).normalized()
            if half and p.y < 0.25 * r:
                continue
            # Wide flat scales that hug the body and only flick out at the tip.
            L, w = (0.8 * r, 0.42 * r) if elev < 60 else (0.62 * r, 0.3 * r)
            up = (Z - nrm * Z.dot(nrm)).normalized() if abs(nrm.z) < 0.98 else Vector((1, 0, 0))
            d0 = (nrm * 0.12 + up * 0.88).normalized()
            d1 = (nrm * 0.75 + up * 0.25).normalized()
            pts = [p - nrm * 0.08 * r + up * 0.0, p + d0 * 0.32 * L + nrm * 0.02 * r,
                   p + d0 * 0.6 * L + d1 * 0.15 * L, p + d0 * 0.72 * L + d1 * 0.45 * L]
            tang = up.cross(nrm)
            b, _, _ = tube(pts, [0.55 * w, w, 0.62 * w, 0.1 * w], 6, flat=0.22,
                           ref=tang if tang.length > 1e-6 else Vector((1, 0, 0)))
            uv_split(b, BRACT, TIP, 0.62)
            merge(fb, b)
    return fb


def place(bm, part, c, tilt=0.0, yaw=0.0):
    m = Matrix.Translation(c) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(tilt, 4, 'X')
    me = bpy.data.meshes.new("_tmp")
    bmesh.ops.transform(part, matrix=m, verts=part.verts)
    part.to_mesh(me)
    part.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)


def flower(bm, c, axis, size, seed=0):
    rnd = random.Random(seed)
    fb = new_part()
    for n, L, W, e0, e1, s, flip, off in ((10, 0.62, 0.17, 28, -8, None, False, 0.5),  # lime sepals, pink tips
                                          (9, 0.5, 0.2, 58, 22, PETAL, True, 0.0)):
        for j in range(n):
            yaw = 2 * math.pi * (j + off) / n + rnd.uniform(-0.1, 0.1)
            dd = lambda e: Vector((math.cos(e) * math.cos(yaw), math.cos(e) * math.sin(yaw), math.sin(e)))
            pts, p = [], Vector((math.cos(yaw), math.sin(yaw), 0)) * 0.05 * size
            for i in range(5):
                pts.append(p.copy())
                p += dd(math.radians(e0 + (e1 - e0) * i / 4)) * (L * size / 4)
            radii = [W * size * f for f in (0.35, 0.85, 1.0, 0.75, 0.15)]
            b, _, _ = tube(pts, radii, 8, flat=0.18, ref=Vector((-math.sin(yaw), math.cos(yaw), 0)))
            if s:
                uv(b, s, flip)
            else:
                uv_split(b, TIP, BRACT, 0.7)
            merge(fb, b)
    merge(fb, sphere_part(size * 0.13, 2, (1, 1, 0.65), STAMEN, lambda v: 0.3), Matrix.Translation((0, 0, 0.07 * size)))
    b, _, _ = tube([(0, 0, -0.45 * size), (0, 0, -0.2 * size), (0, 0, 0.04 * size)],
                   [0.07 * size, 0.09 * size, 0.13 * size], 8, caps=("strip", "strip"))
    uv(b, STEM)
    merge(fb, b)
    rot = Z.rotation_difference(Vector(axis).normalized()).to_matrix().to_4x4()
    bmesh.ops.transform(fb, matrix=Matrix.Translation(c) @ rot, verts=fb.verts)
    me = bpy.data.meshes.new("_tmp")
    fb.to_mesh(me)
    fb.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)


def stake(bm, H, bars=()):
    merge(bm, box_part((0.06, 0.06, H + 0.06), (0, 0, (H - 0.06) / 2), WOOD))
    for z, w, y in bars:
        merge(bm, box_part((w, 0.042, 0.042), (0, y, z), WOOD, axis=0))


def crown_pads(bm, H, specs, rnd):
    """specs: (count, base z, length, e0, e1, width, yaw offset deg)."""
    out = []
    for n, z, L, e0, e1, W, off in specs:
        for j in range(n):
            yaw = math.radians(off + 360 * j / n + rnd.uniform(-14, 14))
            base = Vector((math.cos(yaw) * 0.03, math.sin(yaw) * 0.03, z + rnd.uniform(-0.03, 0.03)))
            out.append(pad(bm, base, yaw, L * rnd.uniform(0.9, 1.08), e0 + rnd.uniform(-6, 6), e1, W,
                           seed=rnd.randint(0, 999)))
    return out


def main_stem(bm, z0, z1, W):
    pts = [(0.0, -0.045, z0 + (z1 - z0) * i / 6) for i in range(7)]
    b, _, _ = tube(pts, [W] * 6 + [W * 0.5], 8, section=pad_section, flat=0.5, ref=Vector((1, 0, 0)))
    uv(b, STEM, flip=True)
    merge(bm, b)


# ---------- stages

def st_seed(bm):
    top = mound(bm, 0.2, 0.055)
    seeds(bm, top)


def st_sprout(bm):
    top = mound(bm, 0.2, 0.055)
    b, _, _ = tube([(0, 0, top - 0.02), (0, 0.003, top + 0.04), (0, 0, top + 0.08)], [0.009, 0.008, 0.007], 8)
    uv(b, SPROUT, flip=True)
    merge(bm, b)
    for yaw in (0.15, math.pi + 0.15):  # bases apart so the two leaves don't share verts
        leaf(bm, (math.cos(yaw) * 0.006, math.sin(yaw) * 0.006, top + 0.075), yaw, 0.078, 0.034, 35, 5, SPROUT)


def st_seedling(bm):
    top = mound(bm, 0.21, 0.06)
    column(bm, [(0, 0, top - 0.03), (0, 0, top + 0.05), (0.004, 0, top + 0.13)], 0.034, spines_at=(1, 2))


def st_young(bm):
    top = mound(bm, 0.24, 0.065)
    column(bm, [(0, 0, top - 0.03), (0, 0, top + 0.07), (0, 0, top + 0.13), (0.004, 0, top + 0.17),
                (0.01, 0, top + 0.25), (0.012, 0, top + 0.32)], 0.044, joints=(3,), spines_at=(1, 2, 4, 5), seed=1)
    column(bm, [(0.02, 0, top + 0.12), (0.075, 0, top + 0.14), (0.1, 0, top + 0.18), (0.105, 0, top + 0.25)],
           0.033, spines_at=(2, 3), seed=2)


def st_growing(bm):
    rnd = random.Random(4)
    top = mound(bm, 0.3, 0.07)
    stake(bm, 0.95, bars=((0.66, 0.36, 0.0),))
    main_stem(bm, top - 0.03, 0.7, 0.034)
    crown_pads(bm, 0.95, [(7, 0.8, 0.46, 52, -86, 0.07, 15), (3, 0.52, 0.34, 22, -88, 0.06, 75)], rnd)
    pad(bm, (0.03, -0.04, top - 0.02), -0.9, 0.13, 60, 20, 0.035, nsc=2)


def st_flowering(bm):
    rnd = random.Random(5)
    top = mound(bm, 0.33, 0.075)
    stake(bm, 1.15, bars=((0.8, 0.42, 0.0),))
    main_stem(bm, top - 0.03, 0.85, 0.038)
    crown_pads(bm, 1.15, [(8, 0.98, 0.56, 52, -86, 0.078, 10), (4, 0.66, 0.42, 22, -88, 0.068, 55)], rnd)
    flower(bm, (0.04, -0.2, 0.66), (0.15, -0.8, 0.55), 0.3)


def st_full(bm):
    rnd = random.Random(6)
    top = mound(bm, 0.4, 0.085)
    stake(bm, 1.62, bars=((1.0, 0.5, 0.0), (1.36, 0.56, 0.0)))
    main_stem(bm, top - 0.03, 1.25, 0.045)
    crown_pads(bm, 1.62, [(9, 1.45, 0.72, 52, -84, 0.09, 0), (5, 1.05, 0.56, 25, -86, 0.082, 40),
                          (3, 0.72, 0.42, 12, -88, 0.07, 100)], rnd)
    for i, (x, y, z) in enumerate(((-0.36, -0.12, 1.1), (0.38, -0.08, 1.16), (-0.25, -0.2, 0.78),
                                   (0.28, -0.18, 0.84))):
        f = fruit_part(0.1, rows=((4, -15), (4, 30)), crown=3, seed=i)
        place(bm, f, Vector((x, y, z)), tilt=rnd.uniform(-0.25, 0.25), yaw=rnd.uniform(0, 6.28))
        b, _, _ = tube([(x * 0.55, y * 0.5, z + 0.12), (x * 0.9, y * 0.9, z + 0.1)], [0.012, 0.014], 8)
        uv(b, STEM)
        merge(bm, b)


def st_item(bm):
    place(bm, fruit_part(0.12, rows=((6, -20), (6, 22)), crown=5, seed=7, cuts=5), Vector((0, 0, 0.135)))


def st_half(bm):
    place(bm, fruit_part(0.12, rows=((6, -20), (6, 22)), crown=5, half=True, seed=7, cuts=5), Vector((0, 0, 0.135)))


STAGES = [("SM_DragonFruit_Seed", st_seed), ("SM_DragonFruit_Stage1", st_sprout),
          ("SM_DragonFruit_Stage2", st_seedling), ("SM_DragonFruit_Stage3", st_young),
          ("SM_DragonFruit_Stage4", st_growing), ("SM_DragonFruit_Stage5", st_flowering),
          ("SM_DragonFruit_Stage6", st_full), ("SM_DragonFruit", st_item),
          ("SM_DragonFruit_Half", st_half)]
X = [0, 0.6, 1.2, 1.85, 2.7, 3.75, 5.0, 5.0, 5.55]
Y = [0, 0, 0, 0, 0, 0, 0, -1.1, -1.1]


def gradient_material():
    m = bpy.data.materials.get("M_GradientTexture")
    if m:
        return m
    m = bpy.data.materials.new("M_GradientTexture")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(ATLAS, check_existing=True)
    tex.location = (-400, 200)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.75
    return m


def build_dragon_fruit(collection="DragonFruit", only=None):
    coll = bpy.data.collections.get(collection) or bpy.data.collections.new(collection)
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    mat = gradient_material()
    out = {}
    for (name, fn), x, y in zip(STAGES, X, Y):
        if only and name not in only:
            continue
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
        ob.location = (x, y, 0)
        coll.objects.link(ob)
        r = topo_check(ob, "quad")
        out[name] = {k: r[k] for k in ("faces", "tris_if_triangulated", "quads", "tris", "ngons", "open_edges",
                                       "double_verts", "flipped_edges", "inside_out_parts", "errors")}
    return out
