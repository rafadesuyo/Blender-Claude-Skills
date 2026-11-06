# gab house layout v3 (2026-10-30) + wall skins. Dante: "add the wall textures to the walls, make the
# bedroom taller, main living room +40%".
# All coordinates are BarnRoom-local UE cm (X forward from the exit door, Y right).
#   ROOMS  interior rectangles; FLOORS = the same reaching 25 cm under the outer walls.
#   WALLS  the structural SM_HouseWall runs placed in the level (collision + house.verse HitsWall):
#          (name, axis, c, s0, s1, zscale): axis "Y" = runs along Y at X = c, axis "X" = along X at Y = c.
#   Wall skins: SM_HouseWallSkin<V>_<Room> = thin panels 13.5 cm in front of every wall face that faces
#   the room (just past the trims), clipped to the room, ONE slot "M_Wall". UVs: u along the wall
#   (one repeat every 2.95 m, so a square texture keeps its aspect), v = 0 at the floor .. 1 at the top,
#   so the full-height wainscot textures fit the wall. Swap a room's walls by setting its slot to
#   another /gab/HouseSurfaces/Walls/MI_Wall_<Name>.
#   exec(open(r"<skills>/blender-game-props/house_walls.py").read())
#   build_house_v3(out_dir)   # floors + skins into collection BarnRoom, FBX for UEFN
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

import bpy, bmesh

VERSION = "4"
# v4 (2026-10-30, Dante's sketch): living room in the middle (exit at its back), toilet left lined up
# with the back wall, kitchen right reaching further back, bedroom across the front (not over the kitchen).
ROOMS = {"Living": (-600, 1000, -775, 775), "Toilet": (-600, 550, -1275, -775),
         "Kitchen": (-1050, 700, 775, 1425), "Bedroom": (1000, 1900, -1275, 1150)}
WALLS = [("HouseWallBack", "Y", -610, -1295, 785, 1.0),
         ("HouseWallToiletLeft", "X", -1285, -620, 570, 1.0), ("HouseWallToiletFront", "Y", 560, -1295, -765, 1.0),
         ("HouseWallToiletA", "X", -775, -600, -400, 0.99), ("HouseWallToiletB", "X", -775, -200, 1000, 0.99),
         ("HouseWallKitchenA", "X", 775, -1060, 450, 0.99), ("HouseWallKitchenB", "X", 775, 650, 1000, 0.99),
         ("HouseWallKitchenBack", "Y", -1060, 765, 1445, 1.0), ("HouseWallKitchenRight", "X", 1435, -1070, 720, 1.0),
         ("HouseWallKitchenFront", "Y", 710, 765, 1445, 1.0),
         ("HouseWallBedroomA", "Y", 1000, -1295, -200, 0.99), ("HouseWallBedroomB", "Y", 1000, 200, 1170, 0.99),
         ("HouseWallFront", "Y", 1910, -1295, 1170, 1.0),
         ("HouseWallBedroomLeft", "X", -1285, 990, 1920, 1.0), ("HouseWallBedroomRight", "X", 1160, 990, 1920, 1.0)]
SKIN_GAP = 13.5      # cm from the wall's centre line (SM_HouseWall is 26 cm thick with its trims)
SKIN_H = 295.0       # cm, under the wall's top cap
U_REPEAT = 295.0


def floors():
    """Each room's floor, reaching 25 cm further on every edge no other room's floor touches (so
    neighbouring floors never overlap and z-fight in the doorways)."""
    def shared(r, k, v):
        other = {0: 1, 1: 0, 2: 3, 3: 2}[k]
        return any(abs(b[other] - v) < 1 for n, b in ROOMS.items() if n != r)
    out = {}
    for r, b in ROOMS.items():
        e = [b[k] + (0 if shared(r, k, b[k]) else (-25 if k in (0, 2) else 25)) for k in range(4)]
        out[r] = tuple(e)
    return out


def _bl(x, y, z):
    """UE local cm -> Blender m (the FBX import turns Blender +X into UE -Y, Blender -Y into UE +X)."""
    return (-y / 100.0, -x / 100.0, z / 100.0)


def _box(bm, uvl, corners_ue, uv_fn):
    """A box from its 8 UE corners c[(i, j, k)], i/j/k in {0, 1}; uv_fn(x, y, z) per corner."""
    v = {k: bm.verts.new(_bl(*p)) for k, p in corners_ue.items()}
    quads = [[(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)], [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)],
             [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)], [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)],
             [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)], [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]]
    for q in quads:
        f = bm.faces.new([v[k] for k in q])
        for loop, k in zip(f.loops, q):
            loop[uvl].uv = uv_fn(*corners_ue[k])


def _mesh(name, bm, slot):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = False
    me.materials.append(bpy.data.materials.get(slot) or bpy.data.materials.new(slot))
    return me


def floor_mesh(name, x0, x1, y0, y1):
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    c = {(i, j, k): ((x0, x1)[i], (y0, y1)[j], (-10.0, 0.0)[k]) for i in (0, 1) for j in (0, 1) for k in (0, 1)}
    _box(bm, uvl, c, lambda x, y, z: (x / 200.0, y / 200.0))
    return _mesh(name, bm, "M_Floor")


def skin_panels(room):
    """[(axis, plane, side, a, b)] for every wall face that faces room."""
    rx0, rx1, ry0, ry1 = ROOMS[room]
    out = []
    for _, axis, c, s0, s1, _ in WALLS:
        lo, hi = (rx0, rx1) if axis == "Y" else (ry0, ry1)       # the room across the wall
        alo, ahi = (ry0, ry1) if axis == "Y" else (rx0, rx1)     # the room along the wall
        for side in (-1, 1):
            if (side > 0 and abs(lo - c) < 20) or (side < 0 and abs(hi - c) < 20):
                a, b = max(s0, alo), min(s1, ahi)
                if b - a > 1:
                    out.append((axis, c + side * SKIN_GAP, side, a, b))
    return out


def skin_mesh(name, room):
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    for axis, p, side, a, b in skin_panels(room):
        q0, q1 = sorted((p, p - side * 0.6))
        if axis == "Y":
            c = {(i, j, k): ((q0, q1)[i], (a, b)[j], (0.0, SKIN_H)[k]) for i in (0, 1) for j in (0, 1) for k in (0, 1)}
            uv = lambda x, y, z: (y / U_REPEAT, z / SKIN_H)
        else:
            c = {(i, j, k): ((a, b)[i], (q0, q1)[j], (0.0, SKIN_H)[k]) for i in (0, 1) for j in (0, 1) for k in (0, 1)}
            uv = lambda x, y, z: (x / U_REPEAT, z / SKIN_H)
        _box(bm, uvl, c, uv)
    return _mesh(name, bm, "M_Wall")


def build_house_v3(out_dir=None):
    coll = bpy.data.collections.get("BarnRoom") or bpy.data.collections.new("BarnRoom")
    made = []
    jobs = [("SM_HouseFloor%s_%s" % (VERSION, r), (lambda n, r=r: floor_mesh(n, *floors()[r]))) for r in ROOMS]
    jobs += [("SM_HouseWallSkin%s_%s" % (VERSION, r), (lambda n, r=r: skin_mesh(n, r))) for r in ROOMS]
    for i, (name, fn) in enumerate(jobs):
        old = bpy.data.objects.get(name)
        if old:
            bpy.data.objects.remove(old, do_unlink=True)
        o = bpy.data.objects.new(name, fn(name))
        coll.objects.link(o)
        o.location = (30 + i * 30, -210, 0)
        made.append(o)
    res = {o.name: [round(d, 2) for d in o.dimensions] for o in made}
    res["panels"] = {r: len(skin_panels(r)) for r in ROOMS}
    if out_dir:
        exec(open(_skill("blender-game-props/blender_helpers.py")).read(), globals())
        for o in made:
            export_fbx(o, out_dir + "/" + o.name + ".fbx")
    return res
