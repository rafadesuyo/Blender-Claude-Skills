# gab House Mode pointer glove, v2 (2026-10-29, from Dante's reference picture): ONE smooth soft hand
# like a cute 3D emoji glove - a puffy fist with three curled-finger knuckles along its bottom, the
# index finger pointing down, the thumb sticking out to the side, and a thick rounded cuff. No
# stitches. Built from exact ellipsoids / capsules, fused by a voxel remesh, the joins softened, then
# remeshed to quads (QuadriFlow); white from the atlas, smooth shaded, with three black stitch lines
# on the back of the hand (laid on the finished surface).
#   SM_PointerGlove  pivot = the fingertip (origin), the hand above it (+Z), the back of the hand
#                    towards Blender +Y (= UE local -X, which the game turns to the camera).
#   exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/glove2.py")).read())
#   build_glove2(out_dir, preview_png)
import bpy, bmesh, math
from mathutils import Vector, Euler

exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/glove.py")).read())

GLOVE2 = c0(18, 0.85, 0.875)   # white (Dante: the cream read too yellow)
STITCH2 = c1(7, 0.70, 0.80)     # black stitch lines on the back of the hand


def _blob(name, parts):
    """One mesh object from ellipsoids ('E', centre, radii) and capsules ('C', a, b, radius)."""
    bm = bmesh.new()
    for p in parts:
        b = bmesh.new()
        if p[0] == 'E':
            bmesh.ops.create_uvsphere(b, u_segments=32, v_segments=20, radius=1.0)
            for v in b.verts:
                v.co = Vector((v.co.x * p[2][0], v.co.y * p[2][1], v.co.z * p[2][2])) + Vector(p[1])
        else:
            a, c, r = Vector(p[1]), Vector(p[2]), p[3]
            L = (c - a).length
            seg = p[4] if len(p) > 4 else (24, 16)
            bmesh.ops.create_uvsphere(b, u_segments=seg[0], v_segments=seg[1], radius=r)
            for v in b.verts:   # the top half moves up: a capsule along +Z from the origin
                if v.co.z > 0:
                    v.co.z += L
            q = Vector((0, 0, 1)).rotation_difference((c - a).normalized())
            for v in b.verts:
                v.co = q @ v.co + a
        me = bpy.data.meshes.new("_p")
        b.to_mesh(me)
        b.free()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def _fuse(o, voxel, smooth, faces):
    """Union the overlapping parts (voxel remesh), round the joins, then clean quads."""
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    o.data.remesh_voxel_size = voxel
    bpy.ops.object.voxel_remesh()
    if smooth:
        m = o.modifiers.new("smooth", 'SMOOTH')
        m.factor = 0.6
        m.iterations = smooth
        bpy.ops.object.modifier_apply(modifier=m.name)
    try:
        bpy.ops.object.quadriflow_remesh(target_faces=faces, use_preserve_sharp=False, use_mesh_symmetry=False, smooth_normals=True)
    except Exception as e:
        print("quadriflow failed", e)


def build_glove2(out_dir=None, preview=None):
    mat = bpy.data.materials["M_GradientTexture"]
    coll = bpy.data.collections.get("BarnRoom") or bpy.data.collections.new("BarnRoom")
    # seen from the back (+Y): the fist on the left, the pointing finger right of it, the thumb right
    hand = _blob("_glove_hand", [
        ('E', (0.07, 0.0, 0.48), (0.205, 0.14, 0.17)),           # fist
        ('E', (0.205, 0.025, 0.355), (0.07, 0.08, 0.075)),       # curled fingers (knuckles)
        ('E', (0.115, 0.03, 0.34), (0.075, 0.085, 0.08)),
        ('E', (0.025, 0.03, 0.345), (0.072, 0.082, 0.078)),
        ('C', (-0.055, 0.0, 0.065), (-0.055, 0.0, 0.42), 0.068),  # pointing index finger
        ('C', (-0.11, -0.03, 0.5), (-0.215, -0.03, 0.38), 0.066), # thumb
    ])
    _fuse(hand, 0.009, 12, 3200)
    # the cuff: a thick rounded oval band on top
    b = bmesh.new()
    bmesh.ops.create_cone(b, cap_ends=True, segments=40, radius1=1.0, radius2=1.0, depth=1.0)
    for v in b.verts:
        v.co = Vector((v.co.x * 0.19 + 0.06, v.co.y * 0.148, v.co.z * 0.17 + 0.69))
    rim = [e for e in b.edges if len(e.link_faces) == 2 and abs(e.link_faces[0].normal.z - e.link_faces[1].normal.z) > 0.5]
    bmesh.ops.bevel(b, geom=rim, offset=0.06, segments=6, profile=0.5, affect='EDGES')
    me = bpy.data.meshes.new("_glove_cuff")
    b.to_mesh(me)
    b.free()
    cuff = bpy.data.objects.new("_glove_cuff", me)
    bpy.context.scene.collection.objects.link(cuff)
    _fuse(cuff, 0.008, 4, 1000)
    # three stitch lines on the back of the fist (+Y), each laid on the smoothed surface
    import mathutils
    bvh = mathutils.bvhtree.BVHTree.FromObject(hand, bpy.context.evaluated_depsgraph_get())
    lines = []
    for x in (0.01, 0.075, 0.14):
        # short capsules from surface point to surface point, so the line follows the curve
        pts = []
        for k in range(5):
            z = 0.425 + 0.135 * k / 4
            hit = bvh.ray_cast(Vector((x, 1.0, z)), Vector((0, -1, 0)), 2.0)
            pts.append(Vector((x, (hit[0].y if hit[0] else 0.13) - 0.002, z)))
        for k in range(4):
            lines.append(('C', tuple(pts[k]), tuple(pts[k + 1]), 0.012, (12, 8)))
    stitches = _blob("_glove_lines", lines)
    zs_all = [v.co.z for o_ in (hand, cuff) for v in o_.data.vertices]
    z0, z1 = min(zs_all), max(zs_all)
    for o_, strip, shade in ((hand, GLOVE2, True), (cuff, GLOVE2, True), (stitches, STITCH2, False)):
        me_ = o_.data
        if not me_.uv_layers:
            me_.uv_layers.new(name="UVMap")
        uvl = me_.uv_layers.active.data
        u, v0, v1 = strip
        for poly in me_.polygons:
            poly.use_smooth = True
            for li in poly.loop_indices:
                z = me_.vertices[me_.loops[li].vertex_index].co.z
                t = (z - z0) / max(z1 - z0, 1e-6) if shade else 0.5
                uvl[li].uv = (u, v1 + (v0 - v1) * (0.15 + 0.7 * t))
    bpy.ops.object.select_all(action='DESELECT')
    for o_ in (hand, cuff, stitches):
        o_.select_set(True)
    bpy.context.view_layer.objects.active = hand
    bpy.ops.object.join()
    o = hand
    me = o.data
    tip = min(me.vertices, key=lambda v: v.co.z).co.copy()
    for v in me.vertices:
        v.co -= tip
    me.transform(Euler((0, math.radians(8), 0)).to_matrix().to_4x4())
    me.materials.clear()
    me.materials.append(mat)
    old = bpy.data.objects.get("SM_PointerGlove")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    o.name = me.name = "SM_PointerGlove"
    for c in list(o.users_collection):
        c.objects.unlink(o)
    coll.objects.link(o)
    o.location = (60, -150, 0)
    res = {"dims": [round(d, 3) for d in o.dimensions], "faces": len(me.polygons),
           "quads": sum(1 for p in me.polygons if len(p.vertices) == 4)}
    if out_dir:
        exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/blender_helpers.py")).read(), globals())
        export_fbx(o, out_dir + "/SM_PointerGloveC.fbx")
    if preview:
        _preview2(o, preview)
    return res


def _preview2(o, path):
    sc = bpy.context.scene
    cam = bpy.data.objects.new("_GlovePreviewCam", bpy.data.cameras.new("_GlovePreviewCam"))
    sc.collection.objects.link(cam)
    c = Vector(o.location) + Vector((0.0, 0, 0.4))
    cam.location = c + Vector((0.25, 1.9, 0.15))
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sun = bpy.data.objects.new("_GloveSun", bpy.data.lights.new("_GloveSun", 'SUN'))
    sc.collection.objects.link(sun)
    sun.data.energy = 2.5
    sun.rotation_euler = (math.radians(40), math.radians(10), math.radians(160))
    sc.camera = cam
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x = sc.render.resolution_y = 600
    sc.render.film_transparent = True
    if sc.world is None:
        sc.world = bpy.data.worlds.new("_glove_world")
    sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes.get("Background")
    keep = None
    if bg:
        keep = (tuple(bg.inputs[0].default_value), bg.inputs[1].default_value)
        bg.inputs[0].default_value = (0.9, 0.9, 0.92, 1)
        bg.inputs[1].default_value = 0.8
    hidden = [ob for ob in sc.objects if ob not in (o, cam, sun) and not ob.hide_render]
    for ob in hidden:
        ob.hide_render = True
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for ob in hidden:
        ob.hide_render = False
    if bg and keep:
        bg.inputs[0].default_value = keep[0]
        bg.inputs[1].default_value = keep[1]
    bpy.data.objects.remove(cam)
    bpy.data.objects.remove(sun)
