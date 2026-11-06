# gab barn door + barn interior room (NewLua pack style, gradient atlas, closed quad boxes).
#   SM_BarnDoor    closed wooden double door for the barn opening (every barn design shares it:
#                  3.9 m x 2.69 m). Pivot at the bottom centre of the door, front -Y. In the barn
#                  it stands at Blender (0, -2.98, 0.205) of the barn (UE local X +298, Z +20.5).
#                  The same mesh is the room's exit door.
#   SM_RoomFloor   the room's floor: 16 x 11 m of cream / warm stone checker tiles (Animal Crossing
#                  style) in a dark-wood border; top at z = 0, pivot at its centre.
#   SM_RoomShell   a big black box seen from INSIDE (normals in), 40 x 40 x 16 m, so the floor
#                  floats in black. No collision in game.
#   exec(open(r"<skills>/blender-game-props/barn_room.py").read())
#   build_barn_room()
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

exec(open(_skill("blender-game-props/chest.py")).read())

DOOR_HALF = 1.93                    # half the door's width (the opening is +-1.95)
DOOR_H = 2.69
DOOR_A = c1(1, 0.71, 0.775)         # planks
DOOR_B = c1(1, 0.73, 0.785)         # lighter planks
DOOR_FRAME = c1(2, 0.69, 0.75)      # darker frame boards
DOOR_IRON = c1(7, 0.70, 0.80)       # black iron
FLOOR_W, FLOOR_D = 16, 11           # tiles (1 m) across X and Y
TILE_A = PAINT_CREAM
TILE_B = LIGHT_STONE
GROUT = GREY_STONE
BORDER = DOOR_FRAME
SHELL = IRON_BLACK
CRISP = dict(cuts=1, power=16.0)


def door_leaf(bm, s):
    """One leaf of the double door, hinged at x = s * DOOR_HALF (s = -1 left, 1 right)."""
    x0, x1 = 0.01, DOOR_HALF
    n = 5
    pw = (x1 - x0) / n
    for i in range(n):
        x = x0 + pw * (i + 0.5)
        rbox(bm, (s * x, 0, DOOR_H / 2), (pw - 0.012, 0.08, DOOR_H), DOOR_B if i % 2 else DOOR_A, **CRISP)
    # frame on the front (proud of the planks): two stiles, three rails between them
    fy, ft = -0.065, 0.05
    for x in (x0 + 0.08, x1 - 0.08):
        rbox(bm, (s * x, fy, DOOR_H / 2), (0.16, ft, DOOR_H - 0.004), DOOR_FRAME, **CRISP)
    inner, outer = x0 + 0.16, x1 - 0.16
    for z in (0.08, DOOR_H / 2, DOOR_H - 0.08):
        rbox(bm, (s * (inner + outer) / 2, fy, z), (outer - inner - 0.004, ft, 0.16), DOOR_FRAME, **CRISP)
    # a diagonal brace in each half, a little behind the frame's face
    for z0, z1 in ((0.16, DOOR_H / 2 - 0.08), (DOOR_H / 2 + 0.08, DOOR_H - 0.16)):
        beam(bm, (s * inner, -0.062, z0 + 0.06), (s * outer, -0.062, z1 - 0.06), 0.13, 0.04, DOOR_FRAME)
    # iron: hinge straps on the outer edge, a pull bar near the middle
    for z in (0.5, DOOR_H - 0.5):
        rbox(bm, (s * (x1 - 0.3), -0.1, z), (0.56, 0.02, 0.07), DOOR_IRON, **CRISP)
    rbox(bm, (s * 0.24, -0.12, 1.35), (0.04, 0.03, 0.42), DOOR_IRON, **CRISP)
    for z in (1.18, 1.52):
        rbox(bm, (s * 0.24, -0.1, z), (0.035, 0.03, 0.035), DOOR_IRON, **CRISP)


def room_floor(bm):
    # tiles (checker), top at z = 0, 3 cm grout gaps showing the slab under them
    for i in range(FLOOR_W):
        for j in range(FLOOR_D):
            x = (i + 0.5) - FLOOR_W / 2
            y = (j + 0.5) - FLOOR_D / 2
            box(bm, (x, y, -0.03), (0.97, 0.97, 0.06), TILE_A if (i + j) % 2 == 0 else TILE_B)
    # the slab (grout colour) and a dark wood border a little higher than the tiles
    box(bm, (0, 0, -0.17), (FLOOR_W + 0.6, FLOOR_D + 0.6, 0.26), GROUT)
    bw = 0.3
    for sy in (-1, 1):
        box(bm, (0, sy * (FLOOR_D / 2 + bw / 2), -0.01), (FLOOR_W + 2 * bw, bw, 0.08), BORDER)
    for sx in (-1, 1):
        box(bm, (sx * (FLOOR_W / 2 + bw / 2), 0, -0.01), (bw, FLOOR_D - 0.004, 0.08), BORDER)


def room_shell(bm, size=(40.0, 40.0, 16.0), z0=-6.0):
    b = bmesh.new()
    bmesh.ops.create_cube(b, size=1.0)
    for v in b.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], z0 + (v.co.z + 0.5) * size[2]))
    bmesh.ops.reverse_faces(b, faces=b.faces[:])
    uvl = b.loops.layers.uv.new("UVMap")
    u, v0, v1 = SHELL
    for f in b.faces:
        for l in f.loops:
            l[uvl].uv = (u, (v0 + v1) / 2)
    me = bpy.data.meshes.new("_shell")
    b.to_mesh(me)
    b.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)


def build_barn_room(out_dir=None):
    mat = bpy.data.materials["M_GradientTexture"]
    coll = bpy.data.collections.get("BarnRoom")
    if coll is None:
        coll = bpy.data.collections.new("BarnRoom")
        bpy.context.scene.collection.children.link(coll)
    made = []
    bm = bmesh.new()
    for s in (-1, 1):
        door_leaf(bm, s)
    made.append(finish(bm, "SM_BarnDoor", coll, (0, -120, 0), mat))
    bm = bmesh.new()
    room_floor(bm)
    made.append(finish(bm, "SM_RoomFloor", coll, (30, -120, 0), mat))
    bm = bmesh.new()
    room_shell(bm)
    made.append(finish(bm, "SM_RoomShell", coll, (80, -120, 0), mat))
    for o in made:
        for p in o.data.polygons:
            p.use_smooth = False
    res = {"closed": check_closed(made[:2]), "dims": {o.name: [round(d, 2) for d in o.dimensions] for o in made},
           "faces": {o.name: len(o.data.polygons) for o in made}}
    if out_dir:
        exec(open(_skill("blender-game-props/blender_helpers.py")).read(), globals())
        for o in made:
            export_fbx(o, out_dir + "/" + o.name + ".fbx")
    return res


# ---------- the house (2026-10-29): four rooms on one floor, cream walls in the level ----------
# UE local of the room root (X forward from the exit door, Y right) -> Blender (x = -UE Y, y = -UE X), m.
# Living room X -6..2, Y -4..4 (wood planks) | kitchen right Y 4..9 (checker tiles) | toilet left
# Y -9..-4 (small blue tiles) | bedroom front X 2..8 (soft carpet). The walls are SM_HouseWall pieces
# (1 m long, scaled in the level) and invisible SM_BoundBox boxes keep players in.
PLANK_A = c1(1, 0.75, 0.80)
PLANK_B = c1(1, 0.77, 0.815)
BATH_A = c0(18, 0.85, 0.87)          # white
BATH_B = c0(15, 0.955, 0.99)         # pale blue-grey
CARPET = c1(4, 0.80, 0.83)           # soft pink
CARPET_EDGE = c0(27, 0.86, 0.90)
WALL_PAINT = PAINT_CREAM
WAINSCOT = c1(1, 0.73, 0.785)
SKIRT = DARKWOOD


def ue_box(bm, x0, x1, y0, y1, z0, z1, col):
    """A box given in UE local cm (X forward, Y right), built in Blender metres (the FBX import
    turns Blender -Y into UE +X and Blender +X into UE -Y)."""
    bx0, bx1 = -y1 / 100, -y0 / 100
    by0, by1 = -x1 / 100, -x0 / 100
    box(bm, ((bx0 + bx1) / 2, (by0 + by1) / 2, (z0 + z1) / 200), (bx1 - bx0, by1 - by0, (z1 - z0) / 100), col)


def house_floor(bm):
    gap = 2.0
    # living room: planks 25 cm wide running along X, staggered joints
    for j in range(32):
        y0 = -400 + j * 25
        cuts = [-600, -600 + (j % 3) * 110 + 120, 200] if j % 2 else [-600, -600 + (j % 4) * 90 + 300, 200]
        for k in range(len(cuts) - 1):
            ue_box(bm, cuts[k] + gap / 2, cuts[k + 1] - gap / 2, y0 + gap / 2, y0 + 25 - gap / 2, -6, 0, PLANK_A if (j + k) % 2 else PLANK_B)
    # kitchen: 50 cm checker tiles
    for i in range(16):
        for j in range(10):
            ue_box(bm, -600 + i * 50 + gap, -600 + (i + 1) * 50 - gap, 400 + j * 50 + gap, 400 + (j + 1) * 50 - gap, -6, 0, TILE_A if (i + j) % 2 == 0 else TILE_B)
    # toilet: 25 cm white / blue tiles
    for i in range(32):
        for j in range(20):
            ue_box(bm, -600 + i * 25 + gap / 2, -600 + (i + 1) * 25 - gap / 2, -900 + j * 25 + gap / 2, -900 + (j + 1) * 25 - gap / 2, -6, 0, BATH_A if (i + j) % 2 == 0 else BATH_B)
    # bedroom: one soft carpet with a darker edge
    ue_box(bm, 215, 785, -885, 885, -6, 0, CARPET)
    for x0, x1, y0, y1 in ((200, 800, -900, -885), (200, 800, 885, 900), (200, 215, -885, 885), (785, 800, -885, 885)):
        ue_box(bm, x0, x1, y0, y1, -6, -0.5, CARPET_EDGE)
    # the slab under it all (grout colour), reaching under the outer walls
    ue_box(bm, -625, 825, -925, 925, -40, -4, GROUT)


def house_wall(bm):
    """1 m of wall (Blender x -0.5..0.5 = UE Y), 0.2 m thick, 3 m tall, pivot bottom centre:
    a skirting board, wooden wainscot to 0.9 m, cream paint above, a cap on top. Same on both faces."""
    # every layer runs the full metre (insets would stretch when the piece is scaled) and butts
    # the one behind it, so no two faces share a plane where they overlap
    box(bm, (0, 0, 1.5), (1.0, 0.2, 3.0), WALL_PAINT)
    for s in (-1, 1):
        box(bm, (0, s * 0.1055, 0.48), (1.0, 0.011, 0.84), WAINSCOT)
        box(bm, (0, s * 0.1205, 0.07), (1.0, 0.019, 0.14), SKIRT)
        box(bm, (0, s * 0.1205, 0.92), (1.0, 0.019, 0.05), SKIRT)
    box(bm, (0, 0, 3.02), (1.0, 0.26, 0.04), SKIRT)


def bound_box(bm):
    """A 1 m cube, pivot at the bottom centre (only its collision is used: hidden in game)."""
    box(bm, (0, 0, 0.5), (1.0, 1.0, 1.0), GREY_STONE)


def build_house(out_dir=None):
    mat = bpy.data.materials["M_GradientTexture"]
    coll = bpy.data.collections.get("BarnRoom") or bpy.data.collections.new("BarnRoom")
    made = []
    for name, fn, loc in (("SM_HouseFloor", house_floor, (30, -150, 0)), ("SM_HouseWall", house_wall, (50, -150, 0)), ("SM_BoundBox", bound_box, (52, -150, 0))):
        bm = bmesh.new()
        fn(bm)
        o = finish(bm, name, coll, loc, mat)
        for p in o.data.polygons:
            p.use_smooth = False
        made.append(o)
    res = {"closed": check_closed(made), "dims": {o.name: [round(d, 2) for d in o.dimensions] for o in made},
           "faces": {o.name: len(o.data.polygons) for o in made}}
    if out_dir:
        exec(open(_skill("blender-game-props/blender_helpers.py")).read(), globals())
        for o in made:
            export_fbx(o, out_dir + "/" + o.name + ".fbx")
    return res
