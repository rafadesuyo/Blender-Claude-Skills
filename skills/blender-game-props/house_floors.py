# gab house floors, v2 (2026-10-30). Dante: "don't make the ground with the mesh, use a texture".
# One flat slab per room (10 cm thick, top at z 0), ONE material slot "M_Floor" whose UVs are in WORLD
# space (one texture repeat every 2 m, u along UE X, v along UE Y), so neighbouring rooms line up and
# each room's floor texture can be swapped on its own (a floor material per texture in UEFN:
# /gab/HouseSurfaces/Floors/MI_Floor_<Name>). The outer edges reach under the outer walls.
#   (2026-10-30, Dante: "the house is mega tiny": rooms ~+85% area, toilet +44%)
#   Living  X -625..550, Y  -550..550    Kitchen X -625..550, Y 550..1225
#   Toilet  X -625..550, Y -1075..-550   Bedroom X  550..1475, Y -1075..1225
#   exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/house_floors.py")).read())
#   build_house_floors(out_dir)   # builds into collection BarnRoom and exports FBX (x100 for UEFN)
import bpy, bmesh

ROOMS = {"Living": (-625, 550, -550, 550), "Kitchen": (-625, 550, 550, 1225),
         "Toilet": (-625, 550, -1075, -550), "Bedroom": (550, 1475, -1075, 1225)}
PREFIX = "SM_HouseFloor2_"   # UEFN can't re-import over an asset: each size gets a new name
REPEAT = 200.0   # cm per texture repeat


def _floor_mesh(name, x0, x1, y0, y1, z0=-10.0, z1=0.0):
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    # UE local cm -> Blender m (the FBX import turns Blender +X into UE -Y and Blender -Y into UE +X)
    P = lambda x, y, z: bm.verts.new((-y / 100.0, -x / 100.0, z / 100.0))
    c = {}
    for xi, x in enumerate((x0, x1)):
        for yi, y in enumerate((y0, y1)):
            for zi, z in enumerate((z0, z1)):
                c[xi, yi, zi] = (P(x, y, z), (x, y, z))
    quads = [[(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)], [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)],
             [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)], [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)],
             [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)], [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]]
    for q in quads:
        f = bm.faces.new([c[k][0] for k in q])
        for loop, k in zip(f.loops, q):
            x, y, z = c[k][1]
            loop[uvl].uv = (x / REPEAT, y / REPEAT)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = False
    mat = bpy.data.materials.get("M_Floor") or bpy.data.materials.new("M_Floor")
    me.materials.append(mat)
    return me


def build_house_floors(out_dir=None):
    coll = bpy.data.collections.get("BarnRoom") or bpy.data.collections.new("BarnRoom")
    made = []
    for i, (room, (x0, x1, y0, y1)) in enumerate(ROOMS.items()):
        name = PREFIX + room
        old = bpy.data.objects.get(name)
        if old:
            bpy.data.objects.remove(old, do_unlink=True)
        o = bpy.data.objects.new(name, _floor_mesh(name, x0, x1, y0, y1))
        coll.objects.link(o)
        o.location = (30 + i * 20, -180, 0)
        made.append(o)
    res = {o.name: [round(d, 2) for d in o.dimensions] for o in made}
    if out_dir:
        exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/blender_helpers.py")).read(), globals())
        for o in made:
            export_fbx(o, out_dir + "/" + o.name + ".fbx")
    return res
