# gab House Mode pointer: a cute cartoon white glove (classic toon style: puffy fingers, three black
# stitch lines on the back, a rolled cuff) pointing DOWN with its index finger. It hovers over the
# furniture the player aims at.
#   SM_PointerGlove  pivot = the fingertip (origin), the hand above it (+Z); the back of the hand
#                    (stitches) faces Blender +Y = UE local -X, so in game it turns to the camera.
#   exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/glove.py")).read())
#   build_glove(out_dir)
import bpy, bmesh, math
from mathutils import Vector, Euler

exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/chest.py")).read())

GLOVE = c0(18, 0.85, 0.875)        # white, a soft grey shade at the bottom of each part
GLOVE_CUFF = c0(18, 0.852, 0.87)
STITCH = c1(7, 0.70, 0.80)         # black
PUFFY = dict(cuts=3, power=2.4)    # round, soft toy shapes


def put(bm, size, col, at, rot=(0, 0, 0), **k):
    """A rounded part (mailbox rbox) of size, turned by rot (degrees XYZ) and moved to at."""
    b = bmesh.new()
    rbox(b, (0, 0, 0), size, col, **(k or PUFFY))
    bmesh.ops.rotate(b, verts=b.verts, cent=(0, 0, 0), matrix=Euler([math.radians(a) for a in rot]).to_matrix())
    bmesh.ops.translate(b, verts=b.verts, vec=Vector(at))
    me = bpy.data.meshes.new("_glove_part")
    b.to_mesh(me)
    b.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)


def glove(bm):
    # the pointing index finger: tip at the origin, a little fatter at the tip (toon fingers)
    put(bm, (0.13, 0.13, 0.38), GLOVE, (0, 0, 0.19))
    put(bm, (0.14, 0.14, 0.15), GLOVE, (0, 0, 0.08), cuts=3, power=2.1)
    # the puffy palm
    put(bm, (0.38, 0.24, 0.32), GLOVE, (0.1, 0.0, 0.44))
    # two curled fingers folded under the palm, beside the pointing one
    put(bm, (0.12, 0.15, 0.16), GLOVE, (0.13, -0.05, 0.29), (12, 0, 0))
    put(bm, (0.11, 0.14, 0.15), GLOVE, (0.24, -0.04, 0.31), (14, 0, -8))
    # the thumb, folded across the front
    put(bm, (0.1, 0.1, 0.22), GLOVE, (-0.06, -0.1, 0.38), (25, 0, -40))
    # three stitch lines on the back of the hand
    for x in (0.0, 0.1, 0.2):
        put(bm, (0.022, 0.02, 0.17), STITCH, (x, 0.118, 0.47), cuts=2, power=3.0)
    # the flared cuff and its rolled rim
    put(bm, (0.33, 0.26, 0.17), GLOVE_CUFF, (0.1, 0.0, 0.63))
    put(bm, (0.41, 0.33, 0.13), GLOVE_CUFF, (0.1, 0.0, 0.73), cuts=3, power=2.0)


def build_glove(out_dir=None, preview=None):
    mat = bpy.data.materials["M_GradientTexture"]
    coll = bpy.data.collections.get("BarnRoom") or bpy.data.collections.new("BarnRoom")
    bm = bmesh.new()
    glove(bm)
    # lean it a little, like it's tapping the item
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler((0, math.radians(-10), 0)).to_matrix())
    o = finish(bm, "SM_PointerGlove", coll, (60, -150, 0), mat)
    res = {"dims": [round(d, 3) for d in o.dimensions], "faces": len(o.data.polygons)}
    if out_dir:
        exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/blender_helpers.py")).read(), globals())
        export_fbx(o, out_dir + "\\SM_PointerGlove.fbx")
    if preview:
        sc = bpy.context.scene
        cam = bpy.data.objects.get("_GlovePreviewCam") or bpy.data.objects.new("_GlovePreviewCam", bpy.data.cameras.new("_GlovePreviewCam"))
        if cam.name not in sc.collection.objects:
            sc.collection.objects.link(cam)
        c = Vector(o.location) + Vector((0.08, 0, 0.38))
        cam.location = c + Vector((0.55, 1.65, 0.35))
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sun = bpy.data.objects.get("_GloveSun") or bpy.data.objects.new("_GloveSun", bpy.data.lights.new("_GloveSun", 'SUN'))
        if sun.name not in sc.collection.objects:
            sc.collection.objects.link(sun)
        sun.data.energy = 3.0
        sun.rotation_euler = (math.radians(40), math.radians(10), math.radians(150))
        sc.camera = cam
        sc.render.engine = 'BLENDER_EEVEE'
        sc.render.resolution_x = sc.render.resolution_y = 600
        sc.render.film_transparent = True
        hidden = []
        for ob in sc.objects:
            if ob not in (o, cam, sun) and not ob.hide_render:
                ob.hide_render = True
                hidden.append(ob)
        sc.render.filepath = preview
        bpy.ops.render.render(write_still=True)
        for ob in hidden:
            ob.hide_render = False
        bpy.data.objects.remove(cam)
        bpy.data.objects.remove(sun)
    return res

