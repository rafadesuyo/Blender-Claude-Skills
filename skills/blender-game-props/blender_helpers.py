# Helpers for building low-poly game props with bmesh (run inside Blender via the Blender MCP):
#   exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/blender_helpers.py")).read())
import bpy, bmesh, math, os
from mathutils import Vector, Matrix


def srgb_to_linear(hexc):
    """'5BE84A' -> linear RGB tuple (what Blender material colors expect)."""
    c = [int(hexc[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


def flat_materials(colors, prefix="M_", roughness=0.6):
    """{'Top': '5BE84A', ...} -> list of materials (index order = dict order). Reuses existing ones."""
    mats = []
    for name, hexc in colors.items():
        full = prefix + name
        m = bpy.data.materials.get(full) or bpy.data.materials.new(full)
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        rgb = srgb_to_linear(hexc)
        bsdf.inputs["Base Color"].default_value = (*rgb, 1)
        bsdf.inputs["Roughness"].default_value = roughness
        m.diffuse_color = (*rgb, 1)
        mats.append(m)
    return mats


def _merge(bm, other):
    tmp = bpy.data.meshes.new("_tmp")
    other.to_mesh(tmp)
    other.free()
    bm.from_mesh(tmp)
    bpy.data.meshes.remove(tmp)


def add_box(bm, center, size, mat=0, bevel=0.0, top_mat=None, side_mat=None, edge_mat=None):
    """Adds a (chamfered) box. With top/side/edge_mat set, faces are colored by their normal:
    up-facing = top, axis-aligned = side, chamfers = edge (cartoon outline look)."""
    b = bmesh.new()
    bmesh.ops.create_cube(b, size=1.0)
    bmesh.ops.scale(b, vec=Vector(size), verts=b.verts)
    if bevel:
        bmesh.ops.bevel(b, geom=list(b.edges), offset=bevel, segments=1, affect='EDGES', profile=0.5)
    for f in b.faces:
        n = f.normal
        if top_mat is not None and n.z > 0.99:
            f.material_index = top_mat
        elif side_mat is not None and (abs(n.x) > 0.99 or abs(n.y) > 0.99 or n.z < -0.99):
            f.material_index = side_mat
        elif edge_mat is not None and bevel:
            f.material_index = edge_mat
        else:
            f.material_index = mat
    bmesh.ops.translate(b, vec=Vector(center), verts=b.verts)
    _merge(bm, b)


def inset_top(bm, mat, thickness, depth=-0.004):
    """Insets every up-facing face (a printed panel / label area) and gives the inner face mat."""
    tops = [f for f in bm.faces if f.normal.z > 0.99]
    bmesh.ops.inset_individual(bm, faces=tops, thickness=thickness, depth=depth)
    for f in tops:
        f.material_index = mat


def piece_mesh(build):
    """build(bm) fills a bmesh; returns it as a reusable mesh for stamp()."""
    bm = bmesh.new()
    build(bm)
    me = bpy.data.meshes.new("_piece")
    bm.to_mesh(me)
    bm.free()
    return me


def stamp(bm, piece, placements):
    """Copies piece (a mesh) into bm at each (x, y, z, yaw_degrees)."""
    for (x, y, z, yaw) in placements:
        b = bmesh.new()
        b.from_mesh(piece)
        bmesh.ops.rotate(b, cent=Vector(), matrix=Matrix.Rotation(math.radians(yaw), 3, 'Z'), verts=b.verts)
        bmesh.ops.translate(b, vec=Vector((x, y, z)), verts=b.verts)
        _merge(bm, b)


def bm_to_object(bm, name, materials, collection="GameProps", location=(0, 0, 0)):
    """Writes bm to a new (or replaced) flat-shaded object in its own collection."""
    col = bpy.data.collections.get(collection)
    if col is None:
        col = bpy.data.collections.new(collection)
        bpy.context.scene.collection.children.link(col)
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in materials:
        me.materials.append(m)
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    ob.location = location
    return ob


def export_fbx(ob, path, unreal_scale=100.0):
    """FBX for UEFN: zeroes the location, scales x100 (UEFN reads the file in cm), restores both.
    Use unreal_scale=1.0 for Unity."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    keep_loc, keep_scale = ob.location.copy(), ob.scale.copy()
    ob.location = (0, 0, 0)
    ob.scale = (unreal_scale, unreal_scale, unreal_scale)
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_unit_scale=True,
                             apply_scale_options='FBX_SCALE_ALL', axis_forward='-Y', axis_up='Z',
                             mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False)
    ob.location, ob.scale = keep_loc, keep_scale
    return os.path.getsize(path)


def look(distance=7.5, target=(0, 0, 0.4), pitch=62, yaw=35, shading='MATERIAL'):
    """Points the 3D viewport at the work for a screenshot."""
    from mathutils import Euler
    for a in bpy.context.screen.areas:
        if a.type == 'VIEW_3D':
            s = a.spaces.active
            s.shading.type = shading
            r = s.region_3d
            r.view_location = Vector(target)
            r.view_distance = distance
            r.view_rotation = Euler((math.radians(pitch), 0, math.radians(yaw)), 'XYZ').to_quaternion()
