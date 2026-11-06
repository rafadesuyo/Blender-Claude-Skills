# Workbench (sheet 53) in the NewLua pack style: desk with drawer and shelf, plank back wall with
# hanging tools (hammer, wrench, saw), wall shelf with a box, lantern (slot 1 glow), red toolbox,
# blue blueprint mat, jar, crates either side with purple metal corners, leaves on the top beam.
# Pivot at the bottom centre, front -Y, ~2.7 m wide x 2.2 m tall. Used as gab's Customize station.
#   exec(open(r"<skills>/blender-game-props/workbench.py").read())
#   build_workbench()
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

exec(open(_skill("blender-game-props/gates2.py")).read())

METAL = c0(30, 0.885, 0.93)          # purple-grey metal caps / corners
STEEL = ((6 + 0.5) * CW, 0.79, 0.825)  # light grey tool steel
WOOD_L = c1(1, 0.74, 0.79)           # lighter wood (desk top, crates)
TOOLBOX = c0(14, 0.9, 0.96)
MAT_BLUE = c0(21, 0.86, 0.9)
MAT_LINE = c0(21, 0.95, 0.99)


def crate(bm, c, s, metal=False, seed=0):
    x, y, z = c
    w, d, h = s
    box(bm, (x, y, z + h / 2), (w - 0.04, d - 0.04, h - 0.04), WOOD)
    t = 0.06
    for sx in (-1, 1):   # frame posts
        for sy in (-1, 1):
            box(bm, (x + sx * (w / 2 - t / 2), y + sy * (d / 2 - t / 2), z + h / 2), (t, t, h), WOOD_L)
    for zz in (z + t / 2 + 0.004, z + h - t / 2 - 0.004):   # rims: 5 mm proud of the posts, inside their ends
        for sy in (-1, 1):
            box(bm, (x, y + sy * (d / 2 - t / 2), zz), (w - 0.012, t + 0.01, t - 0.008), WOOD_L)
    beam(bm, (x - w / 2 + t, y - d / 2 - 0.012, z + t), (x + w / 2 - t, y - d / 2 - 0.012, z + h - t), 0.03, 0.07, WOOD_L)
    if metal:
        for sx in (-1, 1):
            for zz in (z + 0.06, z + h - 0.06):
                box(bm, (x + sx * (w / 2 - 0.05), y - d / 2 + 0.03, zz), (0.13, 0.08, 0.13), METAL)
                bolt(bm, (x + sx * (w / 2 - 0.05), y - d / 2 - 0.02, zz), 0.02, True)


def hammer(bm, x, z, y):
    box(bm, (x, y, z - 0.18), (0.06, 0.04, 0.3), WOOD_L)
    box(bm, (x - 0.02, y, z), (0.2, 0.08, 0.08), STEEL)
    box(bm, (x + 0.1, y, z - 0.02), (0.08, 0.06, 0.05), STEEL, roll=0, pitch=25)
    box(bm, (x, y + 0.02, z + 0.08), (0.04, 0.03, 0.06), WOOD)


def wrench(bm, x, z, y):
    pts = [(x - 0.03, z - 0.3), (x + 0.03, z - 0.3), (x + 0.035, z - 0.05), (x + 0.075, z + 0.02), (x + 0.04, z + 0.08), (x + 0.015, z + 0.03),
           (x - 0.015, z + 0.03), (x - 0.04, z + 0.08), (x - 0.075, z + 0.02), (x - 0.035, z - 0.05)]
    slab(bm, pts, STEEL, 0.03, 0.01, center=(x, z - 0.08), at=(0, y, 0))
    t = bmesh.new()
    torus(t, (0, 0, 0), 0.05, 0.018, STEEL, 'Z', 12, 4)
    bmesh.ops.rotate(t, cent=Vector(), matrix=Matrix.Rotation(math.radians(90), 3, 'X'), verts=t.verts)
    bmesh.ops.translate(t, vec=Vector((x, y, z - 0.33)), verts=t.verts)
    merge(bm, t)
    box(bm, (x, y + 0.02, z + 0.1), (0.04, 0.03, 0.06), WOOD)


def saw(bm, x, z, y):
    pts = [(x - 0.06, z - 0.05), (x + 0.06, z - 0.05), (x + 0.04, z - 0.42), (x - 0.03, z - 0.42)]
    slab(bm, pts, STEEL, 0.015, 0.004, center=(x, z - 0.24), at=(0, y, 0))
    for k in range(6):   # teeth on the right edge
        zz = z - 0.1 - k * 0.055
        box(bm, (x + 0.06 - k * 0.003, y, zz), (0.03, 0.012, 0.03), STEEL, pitch=45)
    box(bm, (x, y - 0.005, z), (0.15, 0.05, 0.12), WOOD)
    box(bm, (x, y - 0.03, z), (0.08, 0.02, 0.05), DARKWOOD)
    box(bm, (x, y + 0.02, z + 0.1), (0.04, 0.03, 0.06), WOOD)


def g_workbench(bm):
    # desk
    top_z = 0.95
    box(bm, (0, -0.05, top_z), (1.75, 0.82, 0.12), WOOD_L)
    for k in (-0.2, 0.2):
        box(bm, (0, -0.05 + k, top_z + 0.063), (1.72, 0.012, 0.01), WOOD)   # plank seams
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(bm, (sx * 0.75, -0.05 + sy * 0.32, top_z / 2), (0.14, 0.14, top_z), WOOD)
        box(bm, (sx * 0.75, -0.37, 0.07), (0.2, 0.2, 0.14), METAL)
    box(bm, (0, -0.05, 0.3), (1.5, 0.7, 0.07), WOOD)            # lower shelf
    box(bm, (0, -0.42, 0.82), (1.5, 0.06, 0.14), WOOD)          # front apron
    box(bm, (0.32, -0.45, 0.66), (0.62, 0.06, 0.22), WOOD_L)    # drawer
    box(bm, (0.32, -0.49, 0.66), (0.26, 0.04, 0.05), METAL)
    # back wall + frame
    for i in range(5):
        box(bm, (0, 0.33, 1.05 + i * 0.2), (1.9, 0.08, 0.19), WOOD if i % 2 else RUSTIC)
    for sx in (-1, 1):
        box(bm, (sx * 1.0, 0.33, 1.05), (0.18, 0.18, 2.1), WOOD)
    box(bm, (0, 0.3, 2.12), (2.4, 0.32, 0.26), WOOD_L)
    box(bm, (1.18, 0.3, 2.12), (0.24, 0.36, 0.3), METAL)
    for k in range(5):
        leaf(bm, (-1.1 + k * 0.12, 0.15, 2.25), -60 - k * 25, 0.3, 0.2, 40, LEAF, droop=-0.25)
    for k in range(3):
        leaf(bm, (-1.2, 0.1, 2.05 - k * 0.12), -150 + k * 20, 0.28, 0.18, -20, LEAF, droop=-0.3)
    # tools on the wall
    hammer(bm, -0.45, 1.75, 0.27)
    wrench(bm, -0.1, 1.75, 0.27)
    saw(bm, 0.22, 1.75, 0.27)
    # wall shelf with a box
    box(bm, (0.72, 0.17, 1.62), (0.5, 0.3, 0.05), WOOD_L)
    beam(bm, (0.6, 0.27, 1.45), (0.6, 0.05, 1.6), 0.04, 0.05, WOOD)
    beam(bm, (0.86, 0.27, 1.45), (0.86, 0.05, 1.6), 0.04, 0.05, WOOD)
    box(bm, (0.72, 0.17, 1.75), (0.34, 0.24, 0.2), WOOD_L)
    box(bm, (0.72, 0.17, 1.86), (0.36, 0.26, 0.04), WOOD)
    # lantern on the left post
    hang_lantern(bm, -1.08, 1.75, -0.05, 0.6, 0.12, -1)
    # on the desk: toolbox, blueprint mat, jar
    box(bm, (-0.5, -0.05, top_z + 0.16), (0.5, 0.3, 0.22), TOOLBOX)
    box(bm, (-0.5, -0.05, top_z + 0.29), (0.52, 0.32, 0.05), TOOLBOX)
    box(bm, (-0.5, -0.21, top_z + 0.2), (0.07, 0.03, 0.08), STEEL)
    for dx in (-0.12, 0.12):
        box(bm, (-0.5 + dx, -0.05, top_z + 0.37), (0.04, 0.05, 0.12), STEEL)
    box(bm, (-0.5, -0.05, top_z + 0.44), (0.26, 0.062, 0.04), STEEL)
    box(bm, (0.15, -0.15, top_z + 0.069), (0.62, 0.42, 0.012), MAT_BLUE)
    for k in range(3):
        box(bm, (0.15 - 0.15 + k * 0.15, -0.15, top_z + 0.077), (0.008, 0.36, 0.006), MAT_LINE)
    for k in range(2):
        box(bm, (0.15, -0.15 - 0.07 + k * 0.14, top_z + 0.0765), (0.56, 0.008, 0.013), MAT_LINE)
    revolve(bm, [(0.1, top_z + 0.065), (0.11, top_z + 0.1), (0.1, top_z + 0.22)], METAL, (0.62, 0.05, 0), 12)
    revolve(bm, [(0.11, top_z + 0.22), (0.11, top_z + 0.25), (0.07, top_z + 0.25), (0.07, top_z + 0.2)], CREAM, (0.62, 0.05, 0), 12)
    # crates
    crate(bm, (-1.15, -0.05, 0), (0.55, 0.55, 0.5), seed=1)
    crate(bm, (-1.12, -0.05, 0.5), (0.45, 0.45, 0.36), seed=2)
    crate(bm, (1.15, -0.15, 0), (0.6, 0.55, 0.52), True, 3)
    crate(bm, (1.1, 0.1, 0.52), (0.5, 0.45, 0.4), True, 4)


def build_workbench():
    root = bpy.data.collections.get("Workbench") or bpy.data.collections.new("Workbench")
    if root.name not in [c.name for c in bpy.context.scene.collection.children]:
        bpy.context.scene.collection.children.link(root)
    bm = bmesh.new()
    g_workbench(bm)
    o = finish_lamp(bm, "SM_Workbench", root, (0, -90.0, 0))
    return check_closed([o]), [round(d, 2) for d in o.dimensions]
