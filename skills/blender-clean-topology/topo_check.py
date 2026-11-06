# Topology check: counts everything a buyer (or a subdivision modifier) complains about.
#   exec(open(r"<skills>/blender-clean-topology/topo_check.py").read())
#   topo_check(obj, target="quad")       -> dict report (+ "verdict" and "problems" list)
#   topo_check(obj, select=True)         -> also selects the bad faces/edges/verts in Edit Mode
#   topo_report(objs, target="game")     -> {name: short report} for several objects
# target="quad": sellable / subdivision-ready (no tris unless allowed, no n-gons, few 6+ poles).
# target="game": tris are fine (engines triangulate anyway), but still no n-gons, holes, doubles.
import bpy, bmesh, math
from mathutils import kdtree

TC_DOUBLE_DIST = 1e-5    # m: verts closer than this are duplicates
TC_THIN_ANGLE = 5.0      # deg: a triangle with a smaller corner is a sliver
TC_NONPLANAR = 12.0      # deg: a quad folded more than this along its diagonal shades badly
TC_MAX_TRI_PCT = 2.0     # quad target: up to this % of tris is still "mostly quads" (hidden spots)


def _tc_islands(b):
    b.faces.ensure_lookup_table()
    part, n = {}, 0
    for f in b.faces:
        if f.index in part:
            continue
        stack = [f]
        part[f.index] = n
        while stack:
            g = stack.pop()
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in part:
                        part[h.index] = n
                        stack.append(h)
        n += 1
    return part, n


def _quad_fold(f):
    """Angle between the two triangles of a quad (worst of both diagonals) in degrees."""
    a, b, c, d = (v.co for v in f.verts)
    def ang(p, q, r, s):
        n1, n2 = (q - p).cross(r - p), (r - p).cross(s - p)
        if n1.length < 1e-12 or n2.length < 1e-12:
            return 0.0
        return math.degrees(n1.angle(n2))
    return min(ang(a, b, c, d), ang(b, c, d, a))


def _min_corner(f):
    best = 180.0
    vs = [v.co for v in f.verts]
    for i in range(len(vs)):
        p, q, r = vs[i - 1], vs[i], vs[(i + 1) % len(vs)]
        u, w = p - q, r - q
        if u.length > 1e-12 and w.length > 1e-12:
            best = min(best, math.degrees(u.angle(w)))
    return best


def topo_check(obj, target="quad", select=False, max_tri_pct=TC_MAX_TRI_PCT):
    me = obj.data
    if obj.mode == 'EDIT':
        bpy.ops.object.mode_set(mode='OBJECT')
    b = bmesh.new()
    b.from_mesh(me)
    b.verts.ensure_lookup_table()
    b.edges.ensure_lookup_table()
    b.faces.ensure_lookup_table()

    tris = [f for f in b.faces if len(f.verts) == 3]
    quads = [f for f in b.faces if len(f.verts) == 4]
    ngons = [f for f in b.faces if len(f.verts) > 4]
    nf = max(len(b.faces), 1)

    boundary = [e for e in b.edges if len(e.link_faces) == 1]
    nonmanifold = [e for e in b.edges if len(e.link_faces) > 2]
    wire = [e for e in b.edges if not e.link_faces]
    loose = [v for v in b.verts if not v.link_edges]
    # A manifold edge whose two faces run it in the same direction = one of them is flipped.
    flipped_edges = []
    for e in b.edges:
        if len(e.link_faces) == 2:
            l1, l2 = e.link_loops[0], e.link_loops[1]
            if l1.vert == l2.vert:
                flipped_edges.append(e)
    # Poles: valence of interior verts. 3 and 5 are normal in good topology, 6+ pinches.
    poles5 = [v for v in b.verts if not v.is_boundary and v.link_faces and len(v.link_edges) == 5]
    poles6 = [v for v in b.verts if not v.is_boundary and v.link_faces and len(v.link_edges) >= 6]

    kd = kdtree.KDTree(len(b.verts))
    for v in b.verts:
        kd.insert(v.co, v.index)
    kd.balance()
    doubles = set()
    for v in b.verts:
        for co, i, d in kd.find_range(v.co, TC_DOUBLE_DIST):
            if i != v.index:
                doubles.add(v.index)
    zero_faces = [f for f in b.faces if f.calc_area() < 1e-10]
    slivers = [f for f in tris if _min_corner(f) < TC_THIN_ANGLE]
    folded = [f for f in quads if _quad_fold(f) > TC_NONPLANAR]

    part, nparts = _tc_islands(b)
    vol = [0.0] * nparts
    for f in b.faces:
        vol[part[f.index]] += f.calc_center_median().dot(f.normal) * f.calc_area() / 3.0
    inside_out = sum(1 for i in range(nparts) if vol[i] < 0)

    uv = me.uv_layers.active
    uv_zero = 0
    if uv:
        uvl = b.loops.layers.uv.active
        for f in b.faces:
            pts = [l[uvl].uv for l in f.loops]
            a = sum(pts[i - 1].x * pts[i].y - pts[i].x * pts[i - 1].y for i in range(len(pts)))
            if abs(a) < 1e-12:
                uv_zero += 1

    r = {
        "object": obj.name, "target": target,
        "verts": len(b.verts), "faces": len(b.faces), "tris_if_triangulated": sum(len(f.verts) - 2 for f in b.faces),
        "tris": len(tris), "quads": len(quads), "ngons": len(ngons),
        "quad_pct": round(100.0 * len(quads) / nf, 1),
        "poles_5": len(poles5), "poles_6plus": len(poles6),
        "open_edges": len(boundary), "nonmanifold_edges": len(nonmanifold),
        "wire_edges": len(wire), "loose_verts": len(loose), "double_verts": len(doubles),
        "flipped_edges": len(flipped_edges), "inside_out_parts": inside_out, "parts": nparts,
        "zero_area_faces": len(zero_faces), "sliver_tris": len(slivers), "folded_quads": len(folded),
        "uv_layers": len(me.uv_layers), "uv_zero_area_faces": uv_zero,
        "scale_applied": all(abs(s - 1) < 1e-6 for s in obj.scale),
        "rotation_applied": all(abs(a) < 1e-6 for a in obj.rotation_euler),
        "modifiers": [m.type for m in obj.modifiers],
        "empty_material_slots": sum(1 for s in obj.material_slots if s.material is None),
    }

    # Errors make it unsellable / break in engine; warnings are worth a look.
    errors, warnings = [], []
    if ngons: errors.append(f"{len(ngons)} n-gons")
    if nonmanifold: errors.append(f"{len(nonmanifold)} non-manifold edges")
    if doubles: errors.append(f"{len(doubles)} doubled verts")
    if flipped_edges or inside_out: errors.append(f"flipped normals ({len(flipped_edges)} edges, {inside_out} inside-out parts)")
    if wire or loose: errors.append(f"{len(wire)} wire edges / {len(loose)} loose verts")
    if zero_faces: errors.append(f"{len(zero_faces)} zero-area faces")
    if target == "quad" and r["tris"] and 100.0 * len(tris) / nf > max_tri_pct:
        errors.append(f"{len(tris)} tris ({100.0 * len(tris) / nf:.1f}% > {max_tri_pct}%)")
    elif r["tris"] and target == "quad":
        warnings.append(f"{len(tris)} tris (under {max_tri_pct}%: keep them on flat, hidden spots)")
    if boundary: warnings.append(f"{len(boundary)} open edges (holes; fine only if the model is meant to be open)")
    if poles6: warnings.append(f"{len(poles6)} poles with 6+ edges (pinching under subdivision)")
    if slivers: warnings.append(f"{len(slivers)} sliver triangles (<{TC_THIN_ANGLE} deg corner)")
    if folded: warnings.append(f"{len(folded)} folded quads (>{TC_NONPLANAR} deg)")
    if not r["uv_layers"]: warnings.append("no UV map")
    elif uv_zero: warnings.append(f"{uv_zero} faces with zero UV area (collapsed UVs)")
    if not (r["scale_applied"] and r["rotation_applied"]): warnings.append("unapplied rotation/scale")
    if r["modifiers"]: warnings.append(f"unapplied modifiers {r['modifiers']}")
    if r["empty_material_slots"]: warnings.append(f"{r['empty_material_slots']} empty material slots")
    r["errors"], r["warnings"] = errors, warnings
    r["verdict"] = "CLEAN" if not errors and not warnings else ("OK (warnings)" if not errors else "FIX")

    if select:
        for el in list(b.verts) + list(b.edges) + list(b.faces):
            el.select = False
        bad_faces = set(ngons) | set(zero_faces) | set(slivers) | set(folded)
        if target == "quad":
            bad_faces |= set(tris)
        for f in bad_faces:
            f.select = True
        for e in nonmanifold + wire + flipped_edges + boundary:
            e.select = True
        for v in poles6 + loose:
            v.select = True
        for i in doubles:
            b.verts[i].select = True
        b.to_mesh(me)
    b.free()
    if select:
        for o in bpy.context.selected_objects:
            o.select_set(False)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(use_extend=True, type='VERT')
        bpy.ops.mesh.select_mode(use_extend=True, type='EDGE')
        bpy.ops.mesh.select_mode(use_extend=True, type='FACE')
    return r


def topo_report(objs, target="quad"):
    keys = ("verdict", "faces", "quad_pct", "tris", "ngons", "poles_6plus", "open_edges", "errors", "warnings")
    return {o.name: {k: v for k, v in topo_check(o, target).items() if k in keys}
            for o in objs if o.type == 'MESH'}
