# gab villagers (2026-11-02): one plush body for every animal villager (penguin first; cat, pig,
# dog... reuse it). Built 1:1 from Dante's penguin reference (1122 x 1402 px; 1 px = 1 mm, x from
# the centre line px 562, z up from the feet's bottom px 1165).
#
# Colours: ONE gradient atlas texture per animal, same layout for all (Characters_tex/make_atlas.py):
# the body's front island (the face / belly pattern, traced from the reference) + gradient columns
# (body, belly, accent, eye, mouth, shine, blush). One material, M_Villager; a new animal = a new atlas.
#
# Animation without skeletons (UEFN entities can't use skeletal meshes): every piece carries a
# PART ID in its second UV map "Part" (u = (id + 0.5) / 10, v = 0.5), so a World Position Offset
# material can move each piece about its own pivot in real time (PART_PIVOTS below):
#   0 body (bob / squash)  1 left foot  2 right foot  3 left flipper  4 right flipper
#   5 tuft  6 face (eyes, beak, mouth: they ride the body)
#   exec(open(r"<skills>/blender-game-props/villager_base.py").read())
#   build_villager_base()
import bpy, bmesh, math, os
from mathutils import Vector, Matrix

PX = 0.001
CX, GROUND = 562, 1165
X = lambda px: (px - CX) * PX
Z = lambda py: (GROUND - py) * PX

# body: a superellipsoid (rounded square from the front, softer from the side)
BODY_X0, BODY_X1, BODY_Y0, BODY_Y1 = 215, 910, 308, 1130
BA = (BODY_X1 - BODY_X0) / 2 * PX          # half width
BC = (BODY_Y1 - BODY_Y0) / 2 * PX          # half height
BB = 0.28                                  # half depth
BZ = Z((BODY_Y0 + BODY_Y1) / 2)            # centre height
BP = 3.0                                   # roundness (2 = ellipsoid)

PARTS = {"Body": 0, "FootL": 1, "FootR": 2, "FlipperL": 3, "FlipperR": 4, "Tuft": 5, "Face": 6}
PART_PIVOTS = {}   # filled by the build: part -> pivot (Blender metres), for the WPO material

COLORS = {  # penguin (linear-ish sRGB picks from the reference)
    "Body": (0.40, 0.38, 0.58), "Belly": (0.98, 0.94, 0.91), "Blush": (0.97, 0.66, 0.70),
    "Accent": (1.0, 0.72, 0.16), "Eye": (0.30, 0.15, 0.08), "Shine": (1, 1, 1), "Mouth": (0.93, 0.48, 0.52)}


def body_front_y(x, z):
    """y of the body's front surface at (x, z) (negative = front)."""
    t = 1 - abs(x / BA) ** BP - abs((z - BZ) / BC) ** BP
    return -BB * max(t, 0.0) ** (1 / BP)


DETAIL = 1.0   # resolution multiplier for every rounded piece (build_villager_base sets it)


def superellipsoid(bm, center, half, power=(3.0, 3.0, 3.0), cuts=10):
    """Smooth rounded blob from a subdivided cube (all quads)."""
    cuts = max(2, int(round(cuts * DETAIL)))
    b = bmesh.new()
    bmesh.ops.create_cube(b, size=2.0)
    bmesh.ops.subdivide_edges(b, edges=b.edges[:], cuts=cuts, use_grid_fill=True)
    px, py, pz = power
    for v in b.verts:
        n = v.co.normalized()
        # map the cube point onto the superellipsoid along its direction
        d = (abs(n.x) ** px + abs(n.y) ** py + abs(n.z) ** pz) ** (1.0 / min(power))
        v.co = Vector((n.x / d, n.y / d, n.z / d))
    # exactly half[] in every direction (the mixed powers above overshoot a little)
    ext = [max(abs(v.co[i]) for v in b.verts) for i in range(3)]
    for v in b.verts:
        v.co = Vector((v.co.x / ext[0] * half[0], v.co.y / ext[1] * half[1], v.co.z / ext[2] * half[2]))
    bmesh.ops.translate(b, vec=Vector(center), verts=b.verts)
    return b


def to_object(b, name, coll, mats, part, uv_fn=None):
    for f in b.faces:
        f.smooth = True
    uv = b.loops.layers.uv.new("UVMap")
    pl = b.loops.layers.uv.new("Part")
    for f in b.faces:
        for l in f.loops:
            l[uv].uv = uv_fn(l.vert.co, f) if uv_fn else (0.02, 0.98)
            l[pl].uv = ((PARTS[part] + 0.5) / 10, 0.5)
    me = bpy.data.meshes.new(name)
    b.to_mesh(me)
    b.free()
    for m in mats:
        me.materials.append(m)
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    o["part"] = part
    return o


def lin(c):
    """sRGB 0..1 -> linear (Blender and UEFN colour inputs are linear)."""
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c)


def mat(name, color, rough=0.75, sheen=0.4):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*lin(color), 1)
    bsdf.inputs["Roughness"].default_value = rough
    if "Sheen Weight" in bsdf.inputs:
        bsdf.inputs["Sheen Weight"].default_value = sheen
    return m


def body_material(mask_img):
    """M_Villager: BodyColor / BellyColor / BlushColor mixed by the mask texture (R / G / B)."""
    m = bpy.data.materials.get("M_Villager") or bpy.data.materials.new("M_Villager")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.85
    if "Sheen Weight" in bsdf.inputs:
        bsdf.inputs["Sheen Weight"].default_value = 0.6
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = mask_img
    tex.image.colorspace_settings.name = "Non-Color"
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(tex.outputs["Color"], sep.inputs["Color"])

    def rgb(name, c):
        n = nt.nodes.new("ShaderNodeRGB")
        n.name = n.label = name
        n.outputs[0].default_value = (*lin(c), 1)
        return n

    body, belly, blush = rgb("BodyColor", COLORS["Body"]), rgb("BellyColor", COLORS["Belly"]), rgb("BlushColor", COLORS["Blush"])
    dash = rgb("DashColor", (0.93, 0.45, 0.52))
    m1 = nt.nodes.new("ShaderNodeMix"); m1.data_type = "RGBA"
    nt.links.new(sep.outputs[0], m1.inputs["Factor"]); nt.links.new(body.outputs[0], m1.inputs[6]); nt.links.new(belly.outputs[0], m1.inputs[7])
    m2 = nt.nodes.new("ShaderNodeMix"); m2.data_type = "RGBA"
    nt.links.new(sep.outputs[1], m2.inputs["Factor"]); nt.links.new(m1.outputs[2], m2.inputs[6]); nt.links.new(blush.outputs[0], m2.inputs[7])
    m3 = nt.nodes.new("ShaderNodeMix"); m3.data_type = "RGBA"
    nt.links.new(sep.outputs[2], m3.inputs["Factor"]); nt.links.new(m2.outputs[2], m3.inputs[6]); nt.links.new(dash.outputs[0], m3.inputs[7])
    nt.links.new(m3.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    return m



# ---------- atlas (Characters_tex/make_atlas.py: same layout for every animal) ----------
ATLAS_N = 1024
ISL_W, ISL_H = 640, 757
COL_X0, COL_W = 664, 44
COLUMNS = ["body", "belly", "accent", "eye", "mouth", "shine", "blush"]


def col_u(name):
    return (COL_X0 + COL_W * COLUMNS.index(name) + COL_W / 2) / ATLAS_N


def column_uvs(b, name, flip=False):
    """Every loop on one atlas column, light at the piece's top, dark at its bottom (flip: reversed)."""
    uv = b.loops.layers.uv.get("UVMap") or b.loops.layers.uv.new("UVMap")
    zs = [v.co.z for v in b.verts]
    lo, hi = min(zs), max(zs)
    u = col_u(name)
    for f in b.faces:
        for l in f.loops:
            t = (hi - l.vert.co.z) / max(hi - lo, 1e-6)
            if flip:
                t = 1 - t
            l[uv].uv = (u, 1 - (0.04 + 0.92 * t))


def body_uvs(b):
    """Front: the painted island (front projection over the body's box). Back: the body column at
    the same height, so the shading matches across the edge."""
    uv = b.loops.layers.uv.get("UVMap") or b.loops.layers.uv.new("UVMap")
    for f in b.faces:
        for l in f.loops:
            x, z = l.vert.co.x, l.vert.co.z
            px, py = x / PX + CX, GROUND - z / PX
            t = min(max((py - BODY_Y0) / (BODY_Y1 - BODY_Y0), 0.0), 1.0)
            if f.normal.y > 0.2:
                l[uv].uv = (col_u("body"), 1 - (0.01 + 0.98 * t))
            else:
                s = min(max((px - BODY_X0) / (BODY_X1 - BODY_X0), 0.002), 0.998)
                l[uv].uv = (s * ISL_W / ATLAS_N, 1 - (0.002 + 0.996 * t) * ISL_H / ATLAS_N)


def finish(b, name, coll, mat, part, column=None, flip=False):
    for f in b.faces:
        f.smooth = True
    if column:
        column_uvs(b, column, flip)
    pl = b.loops.layers.uv.new("Part")
    for f in b.faces:
        for l in f.loops:
            l[pl].uv = ((PARTS[part] + 0.5) / 10, 0.5)
    me = bpy.data.meshes.new(name)
    b.to_mesh(me)
    b.free()
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    o["part"] = part
    return o


def add(b, other):
    me = bpy.data.meshes.new("_t")
    other.to_mesh(me)
    other.free()
    b.from_mesh(me)
    bpy.data.meshes.remove(me)


def atlas_material(img):
    m = bpy.data.materials.get("M_Villager") or bpy.data.materials.new("M_Villager")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.8
    if "Sheen Weight" in bsdf.inputs:
        bsdf.inputs["Sheen Weight"].default_value = 0.5
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Linear"
    uvn = nt.nodes.new("ShaderNodeUVMap")
    uvn.uv_map = "UVMap"
    nt.links.new(uvn.outputs[0], tex.inputs[0])
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    return m


def tube(path, r, n=10):
    """Closed round tube along path (list of Vectors in the XZ plane), capped with domes."""
    b = bmesh.new()
    rings = []
    for i, p in enumerate(path):
        t = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        side = t.cross(Vector((0, 1, 0))).normalized()
        ring = []
        for k in range(n):
            a = 2 * math.pi * k / n
            ring.append(b.verts.new(p + side * (r * math.cos(a)) + Vector((0, r * math.sin(a), 0))))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(n):
            b.faces.new((rings[i][k], rings[i][(k + 1) % n], rings[i + 1][(k + 1) % n], rings[i + 1][k]))
    for ring, tip in ((rings[0], path[0] - (path[1] - path[0]).normalized() * r * 0.8), (rings[-1], path[-1] + (path[-1] - path[-2]).normalized() * r * 0.8)):
        c = b.verts.new(tip)
        for k in range(n):
            b.faces.new((ring[k], ring[(k + 1) % n], c))
    bmesh.ops.recalc_face_normals(b, faces=b.faces)
    return b


def build_villager_base(atlas_path, name="Villager_Penguin", detail=1.0):
    """detail scales the resolution (1.0 = the 10.7k-face original, 0.65 = the lighter game version)."""
    global DETAIL
    DETAIL = detail
    coll = bpy.data.collections.get(name)
    if coll:
        for o in list(coll.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    else:
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
    img = bpy.data.images.load(atlas_path, check_existing=True)
    img.reload()
    M = atlas_material(img)
    for old in ("M_VillagerAccent", "M_VillagerEye", "M_VillagerShine", "M_VillagerMouth"):
        if old in bpy.data.materials and bpy.data.materials[old].users == 0:
            bpy.data.materials.remove(bpy.data.materials[old])
    objs = []

    # --- body
    b = superellipsoid(None, (0, 0, BZ), (BA, BB, BC), (BP, 2.6, BP), cuts=18)
    body_uvs(b)
    objs.append(finish(b, "Body", coll, M, "Body"))
    PART_PIVOTS["Body"] = (0, 0, 0)

    # --- eyes with a shine
    for side, px in (("L", 412), ("R", 712)):
        ex, ez = X(px), Z(557)
        ey = body_front_y(ex, ez)
        b = superellipsoid(None, (ex, ey + 0.004, ez), (0.046, 0.022, 0.057), (2.0, 2.0, 2.0), cuts=6)
        objs.append(finish(b, "Eye" + side, coll, M, "Face", "eye"))
        sx, sz = ex + 0.015, ez + 0.026
        b = superellipsoid(None, (sx, body_front_y(sx, sz) - 0.014, sz), (0.013, 0.008, 0.013), (2.0, 2.0, 2.0), cuts=4)
        objs.append(finish(b, "EyeShine" + side, coll, M, "Face", "shine"))

    # --- upper beak: a thick crescent (x 495..628, y 533..590), its ends drooping
    bz = Z(552)
    by = body_front_y(0, bz) - 0.026
    b = superellipsoid(None, (0, 0, 0), (0.07, 0.038, 0.026), (2.4, 2.0, 2.2), cuts=10)
    for v in b.verts:
        v.co.z -= 6.0 * v.co.x * v.co.x           # the ends droop ~3 cm
        v.co.y -= 0.6 * (0.067 - abs(v.co.x)) * 0.3  # the middle sticks out a little more
    bmesh.ops.translate(b, vec=Vector((0, by, bz)), verts=b.verts)
    objs.append(finish(b, "Beak", coll, M, "Face", "accent"))

    # --- lower beak: an orange U rim (x 505..617, y 585..665) round the open pink mouth
    mz_top, rz, rx = Z(584), 0.074, 0.052
    path = []
    steps = max(8, int(round(24 * DETAIL)))
    for i in range(steps + 1):
        a = -math.pi / 2 + math.pi * i / steps
        x, z = rx * math.sin(a), mz_top - rz * math.cos(a)
        path.append(Vector((x, body_front_y(x, z) - 0.014, z)))
    path = [path[0] + Vector((0, 0, 0.008))] + path + [path[-1] + Vector((0, 0, 0.008))]
    b = tube(path, 0.011, max(6, int(round(10 * DETAIL))))
    objs.append(finish(b, "Jaw", coll, M, "Face", "accent"))
    mz = mz_top - rz * 0.55 + 0.017   # Dante moved the tongue up 1.7 cm
    b = superellipsoid(None, (0, body_front_y(0, mz) - 0.012, mz), (rx - 0.004, 0.012, rz * 0.62), (2.0, 2.0, 2.4), cuts=8)
    objs.append(finish(b, "Mouth", coll, M, "Face", "mouth"))
    PART_PIVOTS["Face"] = (0, 0, 0)

    # --- flippers: tapered paddles out of the sides, nearly level
    for side, s in (("L", -1), ("R", 1)):
        cx = s * (BA + 0.085)
        cz = Z(742)
        b = superellipsoid(None, (0, 0, 0), (0.135, 0.055, 0.068), (2.4, 2.0, 2.4), cuts=10)
        for v in b.verts:
            t = (v.co.x + 0.135) / 0.27
            v.co.z *= 1.0 - 0.28 * t
            v.co.y *= 1.0 - 0.25 * t
        bmesh.ops.rotate(b, cent=Vector(), matrix=Matrix.Rotation(math.radians(-4 * s), 3, 'Y'), verts=b.verts)
        if s < 0:
            bmesh.ops.scale(b, vec=Vector((-1, 1, 1)), verts=b.verts)
            bmesh.ops.reverse_faces(b, faces=b.faces)
        bmesh.ops.translate(b, vec=Vector((cx, 0.02, cz)), verts=b.verts)
        piv = Vector((s * BA, 0.02, cz))   # out of the T-pose: hanging ~35 degrees down from the shoulder
        bmesh.ops.rotate(b, cent=piv, matrix=Matrix.Rotation(math.radians(35 * s), 3, 'Y'), verts=b.verts)
        part = "Flipper" + side
        objs.append(finish(b, part, coll, M, part, "body"))
        PART_PIVOTS[part] = (s * BA, 0.02, cz)

    # --- feet: simple rounded rectangular blocks (Dante: no toes), side by side at the front
    for side, px in (("L", 394), ("R", 730)):
        fx = X(px)
        b = superellipsoid(None, (fx, -0.165, 0.055), (0.088, 0.08, 0.055), (4.0, 3.0, 3.2), cuts=8)
        part = "Foot" + side
        objs.append(finish(b, part, coll, M, part, "accent"))
        PART_PIVOTS[part] = (fx, -0.12, 0.05)

    # --- tuft: a big curled feather, a smaller one under it and a little ball
    def feather(c, half, rot):
        b = superellipsoid(None, (0, 0, 0), half, (2.2, 2.0, 2.2), cuts=8)
        for v in b.verts:
            v.co.z += 0.35 * (v.co.x / half[0]) ** 2 * half[2]
        bmesh.ops.rotate(b, cent=Vector(), matrix=Matrix.Rotation(math.radians(rot), 3, 'Y'), verts=b.verts)
        bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
        return b
    b = feather((X(548), 0.0, Z(238)), (0.108, 0.05, 0.05), 16)
    for extra in (feather((X(522), 0.0, Z(296)), (0.082, 0.045, 0.036), 4),
                  superellipsoid(None, (X(668), 0.0, Z(286)), (0.028, 0.026, 0.028), (2.0, 2.0, 2.0), cuts=5),
                  superellipsoid(None, (X(585), 0.0, Z(318)), (0.09, 0.06, 0.045), (2.0, 2.0, 2.0), cuts=6)):
        add(b, extra)
    objs.append(finish(b, "Tuft", coll, M, "Tuft", "body"))
    PART_PIVOTS["Tuft"] = (0, 0, BZ + BC)
    return [o.name for o in objs]






