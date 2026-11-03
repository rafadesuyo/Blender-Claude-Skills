# Index book lectern (sheet 61) in the NewLua pack style: a stepped wooden plinth, a planked
# pillar wrapped in a flowering vine, a slanted reading desk, and an open book (curved cream page
# blocks, purple cover with gold corner caps and clasp, purple bookmark ribbon with a gold edge),
# leaf sprigs behind. Pivot at the bottom centre, front -Y (the reader's side), ~1.5 m tall.
# check_closed + zfight must be 0.
#   exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/lectern.py")).read())
#   build_lectern()
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/barn_set2.py")).read())
exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/zfight_check.py")).read())

L_WOOD = c1(1, 0.72, 0.78)
L_WOOD_LIGHT = c1(1, 0.77, 0.82)
L_WOOD_DARK = c1(2, 0.69, 0.73)
COVER = canopy(5, 1235, 1335)
COVER_DARK = canopy(5, 1150, 1230)
PAGE = c1(9, 0.75, 0.825)
GOLD_C = c0(23, 0.88, 0.97)
TILT = 28.0             # desk / book tilt (degrees, back edge up)
DESK_Z = 1.3            # desk centre height


def tilted(fn):
    """Builds fn(t) in a flat local frame (desk top at z = 0), tilts it TILT about X (back up) and
    lifts it onto the desk."""
    def g(bm):
        t = bmesh.new()
        fn(t)
        bmesh.ops.rotate(t, cent=Vector(), matrix=Matrix.Rotation(math.radians(TILT), 3, 'X'), verts=t.verts)
        bmesh.ops.translate(t, vec=Vector((0, 0, DESK_Z)), verts=t.verts)
        merge(bm, t)
    return g


def page_block(bm, x0, x1, top0, top1, lift, depth, col):
    """One half of the open book's pages: flat bottom, a top that rises from the spine (top0)
    to a rounded hump and falls to the fore-edge (top1); extruded along Y (depth)."""
    n = 8
    pts = [(x0, 0.0), (x1, 0.0)]
    for i in range(n + 1)[::-1]:
        t = i / n
        x = x0 + (x1 - x0) * t
        z = top0 + (top1 - top0) * t + lift * math.sin(math.pi * min(1.0, t * 1.15))
        pts.append((x, z))
    if len(pts) % 2:
        pts.insert(1, ((x0 + x1) / 2, 0.0))
    slab(bm, pts, col, depth, 0.0, 0.7, center=((x0 + x1) / 2, (top0 + top1) / 4))


def book(t):
    W, D = 0.62, 0.86             # one page's width, the book's length (along Y)
    # cover: two halves meeting at the spine, slightly raised at the outside
    for sx in (-1, 1):
        box(t, (sx * (W / 2 + 0.03), 0, 0.04), (W + 0.06, D + 0.08, 0.08), COVER)
    box(t, (0, 0, 0.03), (0.07, D + 0.06, 0.07), COVER_DARK)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(t, (sx * (W + 0.045), sy * (D / 2 + 0.025), 0.045), (0.11, 0.11, 0.1), GOLD_C)
    # pages
    for sx in (-1, 1):
        p = bmesh.new()
        page_block(p, 0.015, W - 0.02, 0.07, 0.1, 0.07, D, PAGE)
        if sx < 0:
            bmesh.ops.scale(p, vec=Vector((-1, 1, 1)), verts=p.verts)
            bmesh.ops.reverse_faces(p, faces=p.faces)
        bmesh.ops.translate(p, vec=Vector((0, 0, 0.075)), verts=p.verts)
        merge(t, p)
    # gold clasp at the front edge
    box(t, (0, -(D / 2 + 0.05), 0.06), (0.16, 0.04, 0.05), GOLD_C)


def desk(t):
    box(t, (0, 0, -0.07), (1.5, 1.04, 0.12), L_WOOD)
    box(t, (0, -0.535, -0.02), (1.48, 0.05, 0.05), L_WOOD_DARK)    # book stop along the front


def g_lectern(bm):
    # stepped plinth
    box(bm, (0, 0, 0.07), (1.0, 0.8, 0.14), L_WOOD)
    box(bm, (0, 0, 0.2), (0.8, 0.62, 0.12), L_WOOD_LIGHT, taper=0.92)
    box(bm, (0, 0, 0.3), (0.62, 0.48, 0.08), L_WOOD)
    # pillar: a core and plank faces with grooves
    box(bm, (0, 0, 0.72), (0.5, 0.42, 0.78), L_WOOD)
    for k in (-1, 0, 1):
        box(bm, (k * 0.13, -0.215, 0.72), (0.025, 0.012, 0.72), L_WOOD_DARK)
    box(bm, (0, 0, 1.12), (0.66, 0.54, 0.07), L_WOOD_LIGHT)
    box(bm, (0, 0, 0.36), (0.58, 0.5, 0.04), L_WOOD_LIGHT)
    # tilted desk with the book on it
    tilted(desk)(bm)
    tilted(book)(bm)
    # the bookmark ribbon hanging down the front of the desk (purple with a gold edge, V cut)
    ey, ez = -0.475, 0.12          # the book's front edge, in the desk frame
    fy = ey * math.cos(math.radians(TILT)) - ez * math.sin(math.radians(TILT)) - 0.015
    fz = DESK_Z + ey * math.sin(math.radians(TILT)) + ez * math.cos(math.radians(TILT))
    rx = 0.33
    slab(bm, [(rx - 0.07, fz), (rx + 0.07, fz), (rx + 0.07, fz - 0.42), (rx, fz - 0.33), (rx - 0.07, fz - 0.42), (rx - 0.07, fz - 0.2)],
         COVER, 0.025, 0.008, center=(rx, fz - 0.2), at=(0, fy, 0))
    slab(bm, [(rx - 0.05, fz - 0.3), (rx + 0.05, fz - 0.3), (rx + 0.05, fz - 0.36), (rx, fz - 0.3), (rx - 0.05, fz - 0.36), (rx - 0.05, fz - 0.33)],
         GOLD_C, 0.02, 0.005, center=(rx, fz - 0.32), at=(0, fy - 0.02, 0))
    # vine around the pillar with leaves and white flowers
    rnd = random.Random(301)
    pts = [(0.3 * math.cos(-1.9 + i * 0.6), 0.26 * math.sin(-1.9 + i * 0.6), 0.4 + i * 0.07) for i in range(11)]
    tube(bm, pts, [0.028] * len(pts), LEAF_DARK, 8)
    for i in range(1, 11, 2):
        p = pts[i]
        leaf(bm, (p[0] * 1.05, p[1] * 1.05, p[2]), math.degrees(math.atan2(p[1], p[0])) + rnd.uniform(-30, 30), 0.18, 0.12, 30, LEAF, droop=-0.2)
    flat_flower(bm, (0.2, -0.29, 0.62), 0.08, SNOWW)
    flat_flower(bm, (-0.36, -0.42, 0.16), 0.06, SNOWW)
    leaf(bm, (-0.36, -0.43, 0.1), -150, 0.12, 0.08, 20, LEAF, droop=-0.2)
    # leaf sprigs behind the book
    for sx, x in ((-1, -0.62), (1, 0.75)):
        base = (x, 0.42, DESK_Z + 0.32)
        tube(bm, [base, (x + sx * 0.05, 0.47, DESK_Z + 0.55)], [0.012, 0.008], LEAF_DARK, 6)
        for k in range(4):
            leaf(bm, (x + sx * 0.02 * k, 0.45, DESK_Z + 0.38 + k * 0.05), 90 + sx * (20 + 25 * (k % 2)) + (k % 2) * 140, 0.14, 0.08, 40, LEAF, droop=-0.15)


def build_lectern():
    root = bpy.data.collections.get("Index") or bpy.data.collections.new("Index")
    if root.name not in [c.name for c in bpy.context.scene.collection.children]:
        bpy.context.scene.collection.children.link(root)
    bm = bmesh.new()
    g_lectern(bm)
    o = finish_lamp(bm, "SM_IndexLectern", root, (0, -230.0, 0))
    return check_closed([o]), zfight(o), [round(d, 2) for d in o.dimensions]
