# Topology cleanup: fixes what topo_check reports, on a COPY by default (the original is hidden,
# never deleted).
#   exec(open(r"<skills>/blender-clean-topology/quad_build.py").read())
#   exec(open(r"<skills>/blender-clean-topology/topo_check.py").read())
#   exec(open(r"<skills>/blender-clean-topology/topo_clean.py").read())
#   new_obj, before, after = topo_clean(obj)                  # copy "<name>_clean"
#   topo_clean(obj, in_place=True)                            # only when Dante said so
#   remesh(obj, "quadriflow", faces=4000)                     # organic shapes only, on a copy
# Order: merge doubles -> remove degenerate/loose -> tri fans to caps -> n-gons to quads ->
# tris to quads -> normals.
import bpy, bmesh, math

TCL_MERGE = 1e-4        # m: merge-by-distance radius
TCL_JOIN_ANGLE = 40.0   # deg: tris->quads face/shape thresholds (Blender's default)


def orient_outward(b):
    """Recalculates normals, then flips any closed part whose signed volume is negative."""
    bmesh.ops.recalc_face_normals(b, faces=b.faces)
    b.faces.ensure_lookup_table()
    seen = set()
    for f in b.faces:
        if f.index in seen:
            continue
        stack, part, vol = [f], [], 0.0
        seen.add(f.index)
        while stack:
            g = stack.pop()
            part.append(g)
            vol += g.calc_center_median().dot(g.normal) * g.calc_area()
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index)
                        stack.append(h)
        if vol < 0:
            bmesh.ops.reverse_faces(b, faces=part)


def _convex(f):
    vs = [v.co for v in f.verts]
    n = f.normal
    for i in range(len(vs)):
        if (vs[i] - vs[i - 1]).cross(vs[(i + 1) % len(vs)] - vs[i]).dot(n) < -1e-9:
            return False
    return True


def _planar(f, tol=0.02):
    """Planar enough to cap: every vert within tol * face size of the face plane."""
    c, n = f.calc_center_median(), f.normal
    size = max((v.co - c).length for v in f.verts) or 1.0
    return all(abs((v.co - c).dot(n)) <= tol * size for v in f.verts)


def ngons_to_quads(b, ngons=None):
    """Replaces n-gons. Convex planar caps with 4k verts (cylinder ends, round insets) get a
    grid cap, convex planar even ones get quad strips, the rest are triangulated (beauty) and
    joined back into quads. Returns how many n-gons were replaced."""
    ngons = [f for f in (ngons if ngons is not None else b.faces) if f.is_valid and len(f.verts) > 4]
    leftover = []
    for f in ngons:
        ring = [l.vert for l in f.loops]
        n, mat, smooth = len(ring), f.material_index, f.smooth
        if _convex(f) and _planar(f) and n % 2 == 0:
            normal = f.normal.copy()
            bmesh.ops.delete(b, geom=[f], context='FACES_ONLY')
            new = grid_cap(b, ring) if n % 4 == 0 and n >= 8 else strip_cap(b, ring)
            for g in new:
                g.material_index, g.smooth = mat, smooth
                g.normal_update()
                if g.normal.dot(normal) < 0:
                    g.normal_flip()
        else:
            leftover.append(f)
    if leftover:
        res = bmesh.ops.triangulate(b, faces=leftover, quad_method='BEAUTY', ngon_method='BEAUTY')
        tris_to_quads(b, res["faces"])
    return len(ngons)


def fix_fans(b, min_valence=6, max_rise=0.5):
    """Triangle fans (UV-sphere poles, poked caps): the centre vert is dissolved and the hole gets
    a grid/strip cap, lifted back onto the old fan's surface so the shape stays. Steep fans (tip
    higher than max_rise * ring radius: cone tips, spikes) are kept, a point needs its pole. Odd
    rings and non-convex fans are left for tris_to_quads. Returns fans fixed."""
    fixed = 0
    for v in [v for v in b.verts if not v.is_boundary and len(v.link_edges) >= min_valence]:
        if not v.is_valid or any(len(f.verts) != 3 for f in v.link_faces):
            continue
        n = len(v.link_faces)
        if n % 2:
            continue
        tip, mat, smooth = v.co.copy(), v.link_faces[0].material_index, v.link_faces[0].smooth
        rim = {u for e in v.link_edges for u in e.verts if u is not v}
        rc = sum((u.co for u in rim), v.co * 0) / len(rim)
        if (tip - rc).length > max_rise * sum((u.co - rc).length for u in rim) / len(rim):
            continue  # a real point (cone tip, spike): the fan IS the right topology
        bmesh.ops.dissolve_verts(b, verts=[v])
        cap = [f for f in next(iter(rim)).link_faces if len(f.verts) == n and set(f.verts) == rim]
        if not cap:
            continue
        f = cap[0]
        if not _convex(f):
            continue
        ring = [l.vert for l in f.loops]
        c, nrm = f.calc_center_median(), f.normal.copy()
        h = (tip - c).dot(nrm)
        R = sum((u.co - c).length for u in ring) / len(ring)
        bmesh.ops.delete(b, geom=[f], context='FACES_ONLY')
        new = grid_cap(b, ring) if n % 4 == 0 and n >= 8 else strip_cap(b, ring)
        ringset = set(ring)
        for g in new:
            g.material_index, g.smooth = mat, smooth
            g.normal_update()
            if g.normal.dot(nrm) < 0:
                g.normal_flip()
        for u in {u for g in new for u in g.verts} - ringset:  # back onto the old fan's surface
            t = min((u.co - c).length / R, 1.0)
            u.co += nrm * h * (1 - t)
        fixed += 1
    return fixed


def tris_to_quads(b, faces=None, angle=TCL_JOIN_ANGLE):
    faces = [f for f in (faces if faces is not None else b.faces) if f.is_valid and len(f.verts) == 3]
    if faces:
        bmesh.ops.join_triangles(b, faces=faces, angle_face_threshold=math.radians(angle),
                                 angle_shape_threshold=math.radians(angle), cmp_seam=True,
                                 cmp_sharp=True, cmp_uvs=True, cmp_vcols=True, cmp_materials=True)


def _copy(obj, suffix):
    new = obj.copy()
    new.data = obj.data.copy()
    new.name = new.data.name = obj.name + suffix
    for c in obj.users_collection:
        c.objects.link(new)
    obj.hide_set(True)
    return new


def topo_clean(obj, in_place=False, merge=TCL_MERGE, fix_ngons=True, fix_tris=True, target="quad"):
    """Returns (object, report_before, report_after). Does NOT remesh or move verts: shape and UVs
    stay the same. Whatever is left in report_after["errors"] needs a hand fix or a remesh."""
    if obj.mode == 'EDIT':
        bpy.ops.object.mode_set(mode='OBJECT')
    before = topo_check(obj, target)
    if not in_place:
        obj = _copy(obj, "_clean")
    b = bmesh.new()
    b.from_mesh(obj.data)
    bmesh.ops.remove_doubles(b, verts=b.verts, dist=merge)
    bmesh.ops.dissolve_degenerate(b, edges=b.edges, dist=merge)
    bmesh.ops.delete(b, geom=[e for e in b.edges if not e.link_faces], context='EDGES')
    bmesh.ops.delete(b, geom=[v for v in b.verts if not v.link_edges], context='VERTS')
    if fix_tris:
        fix_fans(b)  # before the n-gon pass: a fan it can't cap is left as an n-gon for it
    if fix_ngons:
        ngons_to_quads(b)
    if fix_tris:
        tris_to_quads(b)
    orient_outward(b)
    b.to_mesh(obj.data)
    b.free()
    obj.data.update()
    return obj, before, topo_check(obj, target)


def _activate(o):
    for x in bpy.context.selected_objects:
        x.select_set(False)
    o.select_set(True)
    bpy.context.view_layer.objects.active = o


def _quadriflow(o, faces, sharp):
    _activate(o)
    return 'FINISHED' in bpy.ops.object.quadriflow_remesh(
        mode='FACES', target_faces=max(int(faces), 20), use_preserve_sharp=sharp,
        use_preserve_boundary=True, use_mesh_symmetry=False, seed=0)


def _quadriflow_parts(o, faces, sharp):
    """QuadriFlow sometimes refuses a clean multi-part mesh ("needs to be manifold"): split it
    into loose parts, remesh each with a face share by area, join back. False if a part fails."""
    area = sum(p.area for p in o.data.polygons) or 1.0
    _activate(o)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type='LOOSE')
    bpy.ops.object.mode_set(mode='OBJECT')
    parts = list(bpy.context.selected_objects)
    ok = all(_quadriflow(p, faces * sum(q.area for q in p.data.polygons) / area, sharp) for p in parts)
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.join()
    return ok


def remesh(obj, method="quadriflow", faces=4000, voxel=None, sharp=True):
    """Full retopology on a copy ("<name>_retopo"). Throws away UVs, materials per face and the
    exact edges: use for organic / sculpted / scanned / AI meshes, NOT for hard-surface props.
    method: "quadriflow" | "voxel+quadriflow" (fixes holes/overlaps first) | "qremeshify"
    (needs the QRemeshify add-on; it runs with its own N-panel settings)."""
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    new = _copy(obj, "_retopo")
    _activate(new)
    if method == "voxel+quadriflow":
        size = new.data.remesh_voxel_size = voxel or max(new.dimensions) / 150
        bpy.ops.object.voxel_remesh()
        # Voxels leave tiny edges at sharp tips, which QuadriFlow rejects as "not manifold".
        b = bmesh.new()
        b.from_mesh(new.data)
        bmesh.ops.remove_doubles(b, verts=b.verts, dist=size * 0.2)
        bmesh.ops.dissolve_degenerate(b, edges=b.edges, dist=size * 0.2)
        orient_outward(b)
        b.to_mesh(new.data)
        b.free()
        method = "quadriflow"
    if method == "quadriflow":
        if not (_quadriflow(new, faces, sharp) or _quadriflow_parts(new, faces, sharp)):
            raise RuntimeError(f"QuadriFlow refused {new.name} (kept as is): run topo_clean first, "
                               "or use 'voxel+quadriflow' to make it manifold")
    elif method == "qremeshify":
        # bpy.ops.<anything> always exists, so check the operator list itself.
        ops = dir(bpy.ops.qremeshify)
        if not ops:
            raise RuntimeError("QRemeshify is not installed (ksami.gumroad.com/l/QRemeshify)")
        raise RuntimeError(f"QRemeshify ops {ops}: not wired up yet. Check their properties "
                           "(get_rna_type()) and the N-panel settings, then add the call here.")
    else:
        raise ValueError(method)
    return new, topo_check(new, "quad")
