# Lamp posts in the NewLua stylized farm pack style (gradient atlas, quads only, closed shells).
# Run inside the pack .blend:
#   exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/lamp_posts.py")).read())
#   build_lamps()
# Makes SM_LampPost_Wood, SM_LampPost_Roof, SM_LampPost_Halloween in collection LampPosts.
# Slot 0 = M_GradientTexture (atlas), slot 1 = M_LanternGlow (emissive glass / carved face).
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/gradient_trees.py")).read())

WOOD = c1(1, 0.69, 0.765)        # orange-brown wood
WOOD_DARK = c0(35, 0.86, 0.99)
STONE = c0(2, 0.85, 0.91)        # warm grey stone
ROCK = c0(28, 0.85, 0.99)
IRON = c0(35, 0.93, 0.998)       # dark brown-black metal
GRASS = c0(9)
ROOF = c0(6, 0.86, 0.97)
PETAL = c0(23, 0.92, 0.995)
SOIL = c1(1, 0.69, 0.71)
PURPLE_WOOD = c0(30, 0.88, 0.97)
PURPLE_STONE = c0(30, 0.85, 0.9)
BANNER = c1(3, 0.70, 0.79)
WEB = c0(18, 0.85, 0.87)
GLOWMARK = 1


def glow_material():
    m = bpy.data.materials.get("M_LanternGlow") or bpy.data.materials.new("M_LanternGlow")
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (1.0, 0.45, 0.04, 1)
    b.inputs["Emission Color"].default_value = (1.0, 0.42, 0.03, 1)
    b.inputs["Emission Strength"].default_value = 2.5
    return m


def box(bm, center, size, col, yaw=0.0, pitch=0.0, roll=0.0, taper=1.0, glowing=False):
    """Closed 6-quad box; taper < 1 shrinks the top face."""
    b = bmesh.new()
    bmesh.ops.create_cube(b, size=1.0)
    for v in b.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
        if v.co.z > 0:
            v.co.x *= taper
            v.co.y *= taper
    uv_part(b, col)
    m = Matrix.Rotation(math.radians(yaw), 3, 'Z') @ Matrix.Rotation(math.radians(pitch), 3, 'Y') @ Matrix.Rotation(math.radians(roll), 3, 'X')
    bmesh.ops.rotate(b, cent=Vector(), matrix=m, verts=b.verts)
    bmesh.ops.translate(b, vec=Vector(center), verts=b.verts)
    for f in b.faces:
        f.material_index = GLOWMARK if glowing else 0
    merge(bm, b)


def beam(bm, a, b_, w, h, col):
    """Box from point a to point b (w x h cross-section)."""
    a, b_ = Vector(a), Vector(b_)
    d = b_ - a
    q = d.normalized().to_track_quat('X', 'Z')
    bb = bmesh.new()
    bmesh.ops.create_cube(bb, size=1.0)
    for v in bb.verts:
        v.co = Vector((v.co.x * d.length, v.co.y * w, v.co.z * h))
    uv_part(bb, col)
    bmesh.ops.rotate(bb, cent=Vector(), matrix=q.to_matrix(), verts=bb.verts)
    bmesh.ops.translate(bb, vec=(a + b_) / 2, verts=bb.verts)
    merge(bm, bb)


def stone_blocks(bm, z0, z1, w, col, seed=0, rows=2):
    """A stone base made of slightly uneven stacked blocks (two per row, offset)."""
    rnd = random.Random(seed)
    h = (z1 - z0) / rows
    for r in range(rows):
        ww = w * (1 - 0.06 * r)
        split = rnd.uniform(0.4, 0.6)
        # two blocks per row, the seam alternating between x and y like real masonry
        axis = r % 2
        a = ww * split
        bsz = ww - a
        if axis == 0:
            box(bm, (-ww / 2 + a / 2, 0, z0 + h * (r + 0.5)), (a - 0.012, ww + rnd.uniform(-0.01, 0.01), h - 0.012), col, yaw=rnd.uniform(-2, 2))
            box(bm, (ww / 2 - bsz / 2, 0, z0 + h * (r + 0.5)), (bsz - 0.012, ww + rnd.uniform(-0.01, 0.01), h - 0.012), col, yaw=rnd.uniform(-2, 2))
        else:
            box(bm, (0, -ww / 2 + a / 2, z0 + h * (r + 0.5)), (ww + rnd.uniform(-0.01, 0.01), a - 0.012, h - 0.012), col, yaw=rnd.uniform(-2, 2))
            box(bm, (0, ww / 2 - bsz / 2, z0 + h * (r + 0.5)), (ww + rnd.uniform(-0.01, 0.01), bsz - 0.012, h - 0.012), col, yaw=rnd.uniform(-2, 2))


def grass(bm, c, n=6, seed=0, h=0.32):
    rnd = random.Random(seed)
    for i in range(n):
        leaf(bm, (c[0] + rnd.uniform(-0.05, 0.05), c[1] + rnd.uniform(-0.05, 0.05), c[2]), rnd.uniform(0, 360),
             h * rnd.uniform(0.7, 1.15), 0.08, rnd.uniform(52, 72), GRASS, droop=-0.25)


def rock(bm, c, r, seed, col=None):
    b = quad_sphere(r, 1, (1.2, 1.0, 0.6), 0.15, seed)
    bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
    uv_part(b, col or ROCK)
    merge(bm, b)


def flower(bm, c, seed, size=0.11):
    for k in range(5):
        leaf(bm, c, 72 * k + seed * 13, size, size * 0.75, 8, PETAL, droop=0.15)
    b = quad_sphere(size * 0.32, 1, (1, 1, 0.8), 0, seed)
    bmesh.ops.translate(b, vec=Vector((c[0], c[1], c[2] + 0.012)), verts=b.verts)
    uv_part(b, c0(10, 0.9, 0.99))
    merge(bm, b)


def lantern(bm, hook, s=1.0):
    """Hanging lantern; hook = its top point. Dark frame, glowing glass, little roof."""
    x, y, z = hook
    tube(bm, [(x, y, z), (x, y, z - 0.08 * s)], [0.012 * s, 0.012 * s], IRON, 6)
    box(bm, (x, y, z - 0.12 * s), (0.1 * s, 0.1 * s, 0.06 * s), IRON, taper=0.45)
    box(bm, (x, y, z - 0.2 * s), (0.32 * s, 0.32 * s, 0.1 * s), IRON, taper=0.5)
    box(bm, (x, y, z - 0.42 * s), (0.2 * s, 0.2 * s, 0.32 * s), IRON, glowing=True)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(bm, (x + sx * 0.105 * s, y + sy * 0.105 * s, z - 0.42 * s), (0.035 * s, 0.035 * s, 0.34 * s), IRON)
    box(bm, (x, y, z - 0.61 * s), (0.27 * s, 0.27 * s, 0.06 * s), IRON)
    box(bm, (x, y, z - 0.665 * s), (0.12 * s, 0.12 * s, 0.05 * s), IRON, taper=1.6)


def smooth_round_parts(me):
    """Round parts smooth, boxes (6-face islands) stay crisp."""
    b = bmesh.new()
    b.from_mesh(me)
    b.faces.ensure_lookup_table()
    seen = set()
    for f in b.faces:
        if f.index in seen:
            continue
        stack, isl = [f], []
        seen.add(f.index)
        while stack:
            g = stack.pop()
            isl.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index)
                        stack.append(h)
        for g in isl:
            g.smooth = len(isl) > 6
    b.to_mesh(me)
    b.free()


def finish_lamp(bm, name, coll, loc):
    o = bpy.data.objects.get(name)
    if o:
        bpy.data.objects.remove(o, do_unlink=True)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(bpy.data.materials["M_GradientTexture"])
    me.materials.append(glow_material())
    smooth_round_parts(me)
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    o.location = loc
    return o


def lamp_wood(bm):
    stone_blocks(bm, 0.0, 0.46, 0.54, STONE, 1)
    box(bm, (0, 0, 0.51), (0.27, 0.27, 0.1), IRON)
    box(bm, (0, 0, 1.6), (0.2, 0.2, 2.1), WOOD)
    box(bm, (0, 0, 2.66), (0.24, 0.24, 0.1), IRON)
    beam(bm, (-0.12, 0, 2.52), (0.95, 0, 2.52), 0.16, 0.16, WOOD)
    beam(bm, (0.07, 0, 1.8), (0.64, 0, 2.46), 0.1, 0.1, WOOD)
    box(bm, (0.82, 0, 2.52), (0.08, 0.2, 0.2), IRON)
    lantern(bm, (0.82, 0, 2.42))
    rock(bm, (0.34, 0.28, 0.04), 0.11, 1)
    rock(bm, (-0.36, -0.22, 0.03), 0.09, 2)
    grass(bm, (-0.33, 0.3, 0), 6, 1)
    grass(bm, (0.34, -0.33, 0), 5, 2)


def lamp_roof(bm):
    stone_blocks(bm, 0.0, 0.68, 0.56, STONE, 2, rows=3)
    box(bm, (0, 0, 0.73), (0.27, 0.27, 0.1), IRON)
    box(bm, (0, 0, 1.65), (0.2, 0.2, 1.9), WOOD)
    beam(bm, (-0.1, 0, 2.3), (0.9, 0, 2.3), 0.15, 0.15, WOOD)
    beam(bm, (0.08, 0, 1.75), (0.55, 0, 2.24), 0.09, 0.09, WOOD)
    for sgn in (-1, 1):
        box(bm, (sgn * 0.27, 0, 2.78), (0.62, 0.7, 0.07), ROOF, pitch=sgn * 32)
        for k in range(3):
            box(bm, (sgn * (0.12 + k * 0.17), 0, 2.86 - k * 0.11), (0.2, 0.72, 0.05), ROOF, pitch=sgn * 32)
    beam(bm, (0, -0.37, 2.97), (0, 0.37, 2.97), 0.08, 0.08, WOOD_DARK)
    box(bm, (0, 0, 2.62), (0.24, 0.24, 0.12), WOOD)
    lantern(bm, (0.78, 0, 2.2))
    bx, by = -0.6, -0.35   # flower barrel
    tube(bm, [(bx, by, 0), (bx, by, 0.2), (bx, by, 0.4)], [0.22, 0.25, 0.23], WOOD, 12)
    for z, r in ((0.07, 0.235), (0.33, 0.245)):
        tube(bm, [(bx, by, z - 0.025), (bx, by, z + 0.025)], [r, r + 0.008], IRON, 12)
    tube(bm, [(bx, by, 0.36), (bx, by, 0.41)], [0.21, 0.2], SOIL, 12)
    for i in range(7):
        a = 2 * math.pi * i / 7
        r = 0.12 if i else 0
        c = (bx + r * math.cos(a), by + r * math.sin(a), 0.5 + random.Random(i).uniform(0, 0.1))
        tube(bm, [(c[0], c[1], 0.4), (c[0], c[1], c[2])], [0.01, 0.01], GRASS, 6)
        flower(bm, c, i)
    for i in range(7):
        a = 2 * math.pi * i / 7 + 0.3
        leaf(bm, (bx + 0.1 * math.cos(a), by + 0.1 * math.sin(a), 0.42), math.degrees(a), 0.26, 0.1, 20, GRASS, droop=-0.5)
    grass(bm, (0.34, 0.32, 0), 6, 3)


def lamp_halloween(bm):
    for i, (w, z) in enumerate(((0.62, 0.13), (0.54, 0.38))):
        box(bm, (0, 0, z), (w, w, 0.25), PURPLE_STONE, yaw=i * 6)
    tube(bm, [(0, 0, 0.5), (0.03, 0.01, 1.2), (-0.04, 0, 1.9), (0.02, -0.01, 2.5), (0.08, 0, 2.75)], [0.13, 0.11, 0.1, 0.09, 0.08], PURPLE_WOOD, 8, 0.5, 2.8)
    tube(bm, [(-0.05, 0, 2.55), (0.4, 0, 2.62), (0.8, 0, 2.78), (1.0, 0, 2.95)], [0.08, 0.07, 0.06, 0.05], PURPLE_WOOD, 8)
    tube(bm, [(0.02, 0, 1.9), (0.3, 0, 2.3), (0.5, 0, 2.6)], [0.05, 0.045, 0.04], PURPLE_WOOD, 6)
    box(bm, (0.0, 0, 2.55), (0.24, 0.24, 0.12), IRON, yaw=8)
    tube(bm, [(0.9, 0, 2.85), (0.9, 0, 2.6)], [0.012, 0.012], IRON, 6)
    # jack-o'-lantern facing the front (-Y): built just off the origin on -Y so f_jack turns its
    # face that way, then moved under the hook; its carved face glows
    jb = bmesh.new()
    f_jack(jb, (0, -1e-3, 0), 0.2, 7)
    bmesh.ops.translate(jb, vec=Vector((0.9, 1e-3, 2.38)), verts=jb.verts)
    uvl = jb.loops.layers.uv.verify()
    for f in jb.faces:
        u, v = f.loops[0][uvl].uv
        if abs(u - GLOW[0]) < 1e-3 and v > 0.97:
            f.material_index = GLOWMARK
    merge(bm, jb)
    web_c = Vector((0.0, 0.0, 2.48))   # cobweb in the corner of post and arm
    for k in range(5):
        a = math.radians(-5 + k * 22)
        tube(bm, [web_c + Vector((0, 0.02, 0)), web_c + Vector((0.55 * math.cos(a), 0.02, -0.55 * math.sin(a)))], [0.006, 0.006], WEB, 4)
    for ring in (0.18, 0.32, 0.46):
        for k in range(4):
            a0, a1 = math.radians(-5 + k * 22), math.radians(-5 + (k + 1) * 22)
            p0 = web_c + Vector((ring * math.cos(a0), 0.02, -ring * math.sin(a0)))
            p1 = web_c + Vector((ring * math.cos(a1), 0.02, -ring * math.sin(a1)))
            tube(bm, [p0, (p0 + p1) / 2 + Vector((-0.02, 0, 0.02)), p1], [0.005] * 3, WEB, 4)
    # torn bat banner hanging from the arm, facing the front (-Y)
    bx = 0.42
    tube(bm, [(bx - 0.2, -0.05, 2.62), (bx + 0.2, -0.05, 2.65)], [0.015, 0.015], IRON, 6)
    for i, drop in enumerate((0.62, 0.5, 0.66)):
        box(bm, (bx - 0.12 + i * 0.12, -0.05, 2.63 - drop / 2), (0.12, 0.03, drop), BANNER, pitch=random.Random(i).uniform(-3, 3))
    box(bm, (bx, -0.075, 2.3), (0.08, 0.03, 0.06), IRON)          # the bat
    for sgn in (-1, 1):
        box(bm, (bx + sgn * 0.09, -0.075, 2.31), (0.12, 0.025, 0.05), IRON, pitch=-sgn * 18, taper=0.6)
    for i, (px, py, pr) in enumerate(((0.42, 0.3, 0.19), (0.66, 0.05, 0.13), (-0.38, 0.4, 0.14))):
        b = quad_sphere(pr, 2, (1.1, 1.1, 0.8), 0.0, i)
        for v in b.verts:
            a = math.atan2(v.co.y, v.co.x)
            k = 1 + 0.07 * math.cos(8 * a)
            v.co.x *= k
            v.co.y *= k
        bmesh.ops.translate(b, vec=Vector((px, py, pr * 0.8)), verts=b.verts)
        uv_part(b, PUMPKIN)
        merge(bm, b)
        tube(bm, [(px, py, pr * 1.45), (px + 0.03, py, pr * 1.75)], [0.025, 0.018], BARK_DARK, 6)
    for a in (2.3, 3.6, 5.2):   # dead twigs
        tube(bm, [(0.3 * math.cos(a), 0.3 * math.sin(a), 0), (0.42 * math.cos(a + 0.2), 0.42 * math.sin(a + 0.2), 0.28),
                  (0.5 * math.cos(a + 0.4), 0.5 * math.sin(a + 0.4), 0.48)], [0.03, 0.02, 0.006], SPOOKY_BARK, 6)
    rock(bm, (-0.4, -0.32, 0.04), 0.11, 5, PURPLE_STONE)


LAMPS = [("SM_LampPost_Wood", lamp_wood), ("SM_LampPost_Roof", lamp_roof), ("SM_LampPost_Halloween", lamp_halloween)]


def build_lamps():
    coll = bpy.data.collections.get("LampPosts") or bpy.data.collections.new("LampPosts")
    if coll.name not in [c.name for c in bpy.context.scene.collection.children]:
        bpy.context.scene.collection.children.link(coll)
    objs = []
    for i, (name, fn) in enumerate(LAMPS):
        bm = bmesh.new()
        fn(bm)
        objs.append(finish_lamp(bm, name, coll, (i * 3.0, -8, 0)))
    return check_closed(objs)
